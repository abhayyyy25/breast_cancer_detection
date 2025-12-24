"""
Enterprise Database Configuration

Supports both SQLite (development) and PostgreSQL (production).
Includes connection pooling and session management.

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from models_enterprise import Base

# Database URL from environment or default to SQLite
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./enterprise_healthcare.db"
)

# Handle SQLite specific settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency to get database session.
    
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions outside of FastAPI.
    
    Usage:
        with get_db_session() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)


def init_database():
    """Initialize database with tables."""
    create_tables()
    print("Database tables created successfully!")

