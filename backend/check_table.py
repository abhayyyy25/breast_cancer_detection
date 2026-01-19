"""
Test script to check ReportSettings table structure
"""
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/breast_cancer_db")

def check_table_structure():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("=== ReportSettings Table Columns ===")
    columns = inspector.get_columns('report_settings')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    print("\n✅ Table structure check complete!")

if __name__ == "__main__":
    check_table_structure()
