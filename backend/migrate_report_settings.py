"""
Database Migration: Add ReportSettings Table
Run this script to add the report_settings table to existing database
"""

from sqlalchemy import create_engine, inspect
from database_saas import engine, Base
from models_saas import ReportSettings
import os

def migrate_database():
    """Add report_settings table if it doesn't exist"""
    
    print("=" * 80)
    print("[MIGRATION] Adding ReportSettings Table")
    print("=" * 80)
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "sqlite:///./breast_cancer_saas.db")
    db_type = "PostgreSQL" if db_url.startswith("postgresql") else "SQLite"
    print(f"[*] Database: {db_type}")
    print(f"[*] URL: {db_url}")
    
    # Check if table exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"\n[*] Existing tables: {', '.join(existing_tables)}")
    
    if 'report_settings' in existing_tables:
        print("\n[✓] Table 'report_settings' already exists. No migration needed.")
        return
    
    try:
        # Create only the report_settings table
        print("\n[*] Creating 'report_settings' table...")
        ReportSettings.__table__.create(engine, checkfirst=True)
        print("[✓] Table 'report_settings' created successfully!")
        
        # Verify creation
        inspector = inspect(engine)
        if 'report_settings' in inspector.get_table_names():
            print("[✓] Migration completed successfully!")
            
            # Show table columns
            columns = inspector.get_columns('report_settings')
            print(f"\n[*] Table structure ({len(columns)} columns):")
            for col in columns:
                print(f"    - {col['name']}: {col['type']}")
        else:
            print("[✗] Migration failed - table not found after creation")
            
    except Exception as e:
        print(f"\n[✗] Migration failed: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("[MIGRATION] Complete")
    print("=" * 80)


if __name__ == "__main__":
    migrate_database()
