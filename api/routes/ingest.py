from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from rq import Queue
import redis
import uuid
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from storage.database import get_db
from storage.models import URLIngestion, IngestStatus
from api.deps import validate_url, URLValidationError

load_dotenv()

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)
q = Queue(connection=redis_conn)

class IngestRequest(BaseModel):
    url: HttpUrl

@router.post("/ingest-url", status_code=202)
async def ingest_url(req: IngestRequest, db: Session = Depends(get_db)):
    try:
        # Validate URL first
        metadata = await validate_url(str(req.url))
        
        # Check if URL was already processed
        existing = db.query(URLIngestion).filter(
            URLIngestion.url == str(req.url),
            URLIngestion.status == IngestStatus.COMPLETED
        ).first()
        
        if existing:
            return {
                "job_id": existing.job_id,
                "status": "already_processed",
                "message": "URL was already ingested successfully"
            }
        
        # Generate job ID and create metadata record
        job_id = str(uuid.uuid4())
        ingestion = URLIngestion(
            job_id=job_id,
            url=str(metadata.url),
            status=IngestStatus.PENDING
        )
        db.add(ingestion)
        db.commit()
        
        # Queue the job
        payload = {
            "job_id": job_id,
            "url": str(metadata.url),
            "metadata": metadata.dict()
        }
        q.enqueue("worker.jobs.ingest_job", payload, job_id=job_id)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "metadata": metadata.dict()
        }
        
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/ingest-status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    from rq.job import Job
    
    # Get metadata from database
    ingestion = db.query(URLIngestion).filter(URLIngestion.job_id == job_id).first()
    if not ingestion:
        return {"job_id": job_id, "status": "not_found"}
        
    try:
        # Get queue job status
        job = Job.fetch(job_id, connection=redis_conn)
        queue_status = job.get_status()
        
        # Update metadata if needed
        if queue_status == "finished" and ingestion.status != IngestStatus.COMPLETED:
            if job.result and job.result.get("status") == "completed":
                ingestion.status = IngestStatus.COMPLETED
                ingestion.chunks_count = job.result.get("chunks", 0)
            else:
                ingestion.status = IngestStatus.FAILED
                ingestion.error_message = str(job.result.get("error", "Unknown error"))
            db.commit()
            
        return {
            **ingestion.to_dict(),
            "queue_status": queue_status,
            "result": job.result
        }
    except Exception as e:
        return {
            **ingestion.to_dict(),
            "queue_status": "unknown",
            "error": str(e)
        }
