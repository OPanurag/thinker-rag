from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class IngestStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class URLIngestion(Base):
    __tablename__ = "url_ingestions"

    job_id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    status = Column(SQLEnum(IngestStatus), nullable=False, default=IngestStatus.PENDING)
    chunks_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "url": self.url,
            "status": self.status,
            "chunks_count": self.chunks_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }