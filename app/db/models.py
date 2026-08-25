"""SQLAlchemy models for submission persistence."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    overall_score = Column(Float, nullable=True)
    overall_max = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    report_json = Column(Text, nullable=True)  # JSON-serialized FinalReport
    created_at = Column(DateTime, nullable=True)