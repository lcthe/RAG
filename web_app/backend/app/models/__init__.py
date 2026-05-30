"""SQLAlchemy models - QueryLog only."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from web_app.backend.app.database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer_preview = Column(String(500), default="")
    latency_ms = Column(Float, default=0)
    retrieval_count = Column(Integer, default=0)
    model_used = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
