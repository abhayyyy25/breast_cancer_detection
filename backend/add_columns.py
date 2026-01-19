"""
Database Migration: Add Missing Columns to ReportSettings
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/breast_cancer_db")

def add_missing_columns():
    """Add logo_base64, doctor_name, and footer_text columns"""
    engine = create_engine(DATABASE_URL)
    
    print("=" * 60)
    print("Adding Missing Columns to report_settings Table")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # Add logo_base64 column
            print("\n[1/3] Adding logo_base64 column...")
            conn.execute(text("""
                ALTER TABLE report_settings 
                ADD COLUMN IF NOT EXISTS logo_base64 TEXT;
            """))
            conn.commit()
            print("✅ logo_base64 column added")
            
            # Add doctor_name column
            print("\n[2/3] Adding doctor_name column...")
            conn.execute(text("""
                ALTER TABLE report_settings 
                ADD COLUMN IF NOT EXISTS doctor_name VARCHAR(255);
            """))
            conn.commit()
            print("✅ doctor_name column added")
            
            # Add footer_text column  
            print("\n[3/3] Adding footer_text column...")
            conn.execute(text("""
                ALTER TABLE report_settings 
                ADD COLUMN IF NOT EXISTS footer_text TEXT;
            """))
            conn.commit()
            print("✅ footer_text column added")
            
            print("\n" + "=" * 60)
            print("🎉 Migration Completed Successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_missing_columns()
