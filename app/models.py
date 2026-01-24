from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class VideoTask(Base):
    __tablename__ = "video_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False)
    video_path = Column(String(500))
    audio_path = Column(String(500))
    transcript_path = Column(String(500))
    srt_path = Column(String(500))
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    transcript_text = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "status": self.status,
            "progress": self.progress,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "has_audio": bool(self.audio_path),
            "has_transcript": bool(self.transcript_path),
            "has_srt": bool(self.srt_path),
            "audio_url": f"/download/audio/{self.id}" if self.audio_path else None,
            "transcript_url": f"/download/transcript/{self.id}" if self.transcript_path else None,
            "srt_url": f"/download/srt/{self.id}" if self.srt_path else None,
            "preview_url": f"/download/preview/{self.id}" if self.transcript_text else None,
            "error_message": self.error_message
        }