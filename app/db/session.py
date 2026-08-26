"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

import os
from app.config import get_settings

DATABASE_URL = os.environ.get("DATABASE_URL") or get_settings().database_url

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """Yield a new SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Create all tables (use Alembic in production)."""
    Base.metadata.create_all(bind=engine)