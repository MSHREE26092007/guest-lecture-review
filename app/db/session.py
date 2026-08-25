"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

# Default to SQLite for prototype; override via DATABASE_URL env var
DATABASE_URL = (
    "sqlite:///./guest_lecture_review.db"
    if not __import__("os").environ.get("DATABASE_URL")
    else __import__("os").environ["DATABASE_URL"]
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
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