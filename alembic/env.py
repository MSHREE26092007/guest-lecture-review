from __future__ import with_statement
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Base object from your models module
from app.db.models import Base

def get_url():
    """Read DATABASE_URL from environment, default to SQLite."""
    return os.environ.get("DATABASE_URL", "sqlite:///./guest_lecture_review.db")

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config_ini_section=os.environ.get("ALEMBIC_CONFIG_SECTION", "alembic"))
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.begin() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        context.run_migrations()