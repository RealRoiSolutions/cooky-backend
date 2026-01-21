from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base

class TranslationJob(Base):
    __tablename__ = "translation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False) # "ingredient" or "recipe"
    entity_id = Column(Integer, nullable=False)
    target_lang = Column(String, nullable=False)
    status = Column(String, nullable=False) # "pending", "in_progress", "done", "error"
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
