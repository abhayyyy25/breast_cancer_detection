"""
Multi-Tenant Database Configuration
PostgreSQL/SQLite support with connection pooling
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models_saas import Base


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./breast_cancer_saas.db"  # Default to SQLite for development
)

# Handle Heroku/Render postgres:// to postgresql:// conversion
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"[DATABASE] Using: {'PostgreSQL' if DATABASE_URL.startswith('postgresql') else 'SQLite'}")

# SQLite-specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL query logging
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# DATABASE DEPENDENCY
# ============================================================================

def get_db():
    """
    Dependency to get database session
    Use with FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def create_all_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("[OK] All database tables created successfully")


def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("[WARNING] All database tables dropped")


def reset_database():
    """Drop and recreate all tables"""
    drop_all_tables()
    create_all_tables()
    print("[RESET] Database reset complete")

