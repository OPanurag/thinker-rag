import hashlib, time
from trafilatura import fetch_url, extract
from model.embed_provider import embed_batch
from storage.qdrant_client import qdrant_upsert

CHUNK_SIZE = 800
OVERLAP = 200

def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def fetch_text(url):
    raw = fetch_url(url)
    if not raw:
        return ""
    text = extract(raw)
    return text or ""

from storage.database import get_db
from storage.models import URLIngestion, IngestStatus

def ingest_job(payload):
    job_id = payload["job_id"]
    
    if payload.get("is_text", False):
        text = payload["content"]
        source = f"text_input_{job_id}"
    else:
        url = payload["url"]
        # Update status to processing
        with get_db() as db:
            ingestion = db.query(URLIngestion).filter(URLIngestion.job_id == job_id).first()
            if ingestion:
                ingestion.status = IngestStatus.PROCESSING
                db.commit()
        
        print(f"[Worker] Ingesting {url}")
        text = fetch_text(url)
        source = url
        
        if not text:
            # Update status to failed
            with get_db() as db:
                if ingestion:
                    ingestion.status = IngestStatus.FAILED
                    ingestion.error_message = "No text could be extracted from the URL"
                    db.commit()
            return {"status": "failed", "error": "no_text"}
    
    chunks = chunk_text(text)
    embeddings = embed_batch(chunks)
    points = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        points.append({
            "id": f"{job_id}_{idx}",
            "vector": emb,
            "payload": {"url": url, "job_id": job_id, "chunk_index": idx, "text": chunk[:2000]}
        })
    qdrant_upsert(points)
    
    # Update status to completed with chunks count
    with get_db() as db:
        if ingestion:
            ingestion.status = IngestStatus.COMPLETED
            ingestion.chunks_count = len(points)
            db.commit()
    
    return {"status": "completed", "chunks": len(points)}
