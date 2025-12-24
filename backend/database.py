"""
Database connection and session management.

Handles database initialization, connection pooling, and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL - supports both PostgreSQL and SQLite
# For production: postgresql://user:password@localhost/dbname
# For development: sqlite:///./breast_cancer_detection.db
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./breast_cancer_detection.db"
)

# Handle Heroku/Render postgres:// to postgresql:// conversion
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"[DATABASE] Using: {'PostgreSQL' if DATABASE_URL.startswith('postgresql') else 'SQLite'}")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL query logging
    )
else:
    # PostgreSQL specific settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    
    Should be called on application startup.
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def reset_db():
    """
    Drop all tables and recreate them.
    
    ⚠️ WARNING: This will delete all data! Use only in development.
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset successfully!")

