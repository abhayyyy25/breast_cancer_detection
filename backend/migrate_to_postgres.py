"""
SQLite to PostgreSQL Migration Script

This script migrates all data from SQLite to PostgreSQL:
- Users (with hashed passwords)
- Patients (with all demographics)
- Scans (with file paths and analysis results)
- Audit Logs (compliance tracking)

Usage:
    python migrate_to_postgres.py --postgres-url "postgresql://user:password@host:5432/dbname"
    
    Or set DATABASE_URL environment variable and run:
    python migrate_to_postgres.py
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import models
from models import Base, User, Patient, Scan, AuditLog


def create_postgres_engine(postgres_url: str):
    """Create PostgreSQL engine with proper settings"""
    return create_engine(
        postgres_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )


def create_sqlite_engine():
    """Create SQLite engine"""
    return create_engine(
        "sqlite:///./breast_cancer_detection.db",
        connect_args={"check_same_thread": False}
    )


def verify_postgres_connection(engine):
    """Test PostgreSQL connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False


def migrate_data(sqlite_engine, postgres_engine, drop_existing=False):
    """Migrate all data from SQLite to PostgreSQL"""
    
    print("\n" + "="*70)
    print("DATABASE MIGRATION: SQLite → PostgreSQL")
    print("="*70)
    
    # Create tables in PostgreSQL
    print("\n📦 Creating tables in PostgreSQL...")
    if drop_existing:
        print("⚠️  Dropping existing tables...")
        Base.metadata.drop_all(bind=postgres_engine)
    
    Base.metadata.create_all(bind=postgres_engine)
    print("✅ Tables created successfully")
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate Users
        print("\n👥 Migrating users...")
        users = sqlite_session.query(User).all()
        user_count = 0
        user_map = {}  # Map old IDs to new IDs
        
        for user in users:
            new_user = User(
                email=user.email,
                hashed_password=user.hashed_password,
                full_name=user.full_name,
                role=user.role,
                license_number=user.license_number,
                department=user.department,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login
            )
            postgres_session.add(new_user)
            postgres_session.flush()  # Get the new ID
            user_map[user.id] = new_user.id
            user_count += 1
            print(f"   ✓ {user.email} ({user.role})")
        
        postgres_session.commit()
        print(f"✅ Migrated {user_count} users")
        
        # Migrate Patients
        print("\n🏥 Migrating patients...")
        patients = sqlite_session.query(Patient).all()
        patient_count = 0
        patient_map = {}  # Map old IDs to new IDs
        
        for patient in patients:
            new_patient = Patient(
                medical_record_number=patient.medical_record_number,
                first_name=patient.first_name,
                last_name=patient.last_name,
                date_of_birth=patient.date_of_birth,
                gender=patient.gender,
                contact_phone=patient.contact_phone,
                contact_email=patient.contact_email,
                address=patient.address,
                emergency_contact_name=patient.emergency_contact_name,
                emergency_contact_phone=patient.emergency_contact_phone,
                created_at=patient.created_at,
                updated_at=patient.updated_at
            )
            postgres_session.add(new_patient)
            postgres_session.flush()
            patient_map[patient.id] = new_patient.id
            patient_count += 1
            print(f"   ✓ {patient.medical_record_number}: {patient.first_name} {patient.last_name}")
        
        postgres_session.commit()
        print(f"✅ Migrated {patient_count} patients")
        
        # Migrate Scans
        print("\n🔬 Migrating scans...")
        scans = sqlite_session.query(Scan).all()
        scan_count = 0
        
        for scan in scans:
            new_scan = Scan(
                patient_id=patient_map.get(scan.patient_id),
                user_id=user_map.get(scan.user_id),
                image_path=scan.image_path,
                original_filename=getattr(scan, 'original_filename', None),
                prediction_result=scan.prediction_result,
                confidence_score=scan.confidence_score,
                malignant_probability=scan.malignant_probability,
                benign_probability=scan.benign_probability,
                risk_level=scan.risk_level,
                mean_intensity=getattr(scan, 'mean_intensity', None),
                std_intensity=getattr(scan, 'std_intensity', None),
                brightness=getattr(scan, 'brightness', None),
                contrast=getattr(scan, 'contrast', None),
                image_width=getattr(scan, 'image_width', None),
                image_height=getattr(scan, 'image_height', None),
                file_format=getattr(scan, 'file_format', None),
                doctor_notes=getattr(scan, 'doctor_notes', None),
                findings=getattr(scan, 'findings', None),
                report_generated=getattr(scan, 'report_generated', 0),
                report_path=getattr(scan, 'report_path', None),
                created_at=scan.created_at,
                updated_at=getattr(scan, 'updated_at', scan.created_at)
            )
            postgres_session.add(new_scan)
            scan_count += 1
            print(f"   ✓ Scan {scan.id} for {patient_map.get(scan.patient_id)}: {scan.prediction_result}")
        
        postgres_session.commit()
        print(f"✅ Migrated {scan_count} scans")
        
        # Migrate Audit Logs
        print("\n📋 Migrating audit logs...")
        audit_logs = sqlite_session.query(AuditLog).all()
        audit_count = 0
        
        for log in audit_logs:
            new_log = AuditLog(
                user_id=user_map.get(log.user_id) if log.user_id else None,
                patient_id=patient_map.get(log.patient_id) if log.patient_id else None,
                scan_id=log.scan_id if hasattr(log, 'scan_id') else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=getattr(log, 'ip_address', None),
                user_agent=getattr(log, 'user_agent', None),
                timestamp=log.timestamp
            )
            postgres_session.add(new_log)
            audit_count += 1
        
        postgres_session.commit()
        print(f"✅ Migrated {audit_count} audit log entries")
        
        # Summary
        print("\n" + "="*70)
        print("MIGRATION COMPLETE!")
        print("="*70)
        print(f"✅ Users:       {user_count}")
        print(f"✅ Patients:    {patient_count}")
        print(f"✅ Scans:       {scan_count}")
        print(f"✅ Audit Logs:  {audit_count}")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        postgres_session.rollback()
        return False
    finally:
        sqlite_session.close()
        postgres_session.close()


def verify_migration(postgres_engine):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    PostgresSession = sessionmaker(bind=postgres_engine)
    session = PostgresSession()
    
    try:
        user_count = session.query(User).count()
        patient_count = session.query(Patient).count()
        scan_count = session.query(Scan).count()
        audit_count = session.query(AuditLog).count()
        
        print(f"✅ PostgreSQL database contains:")
        print(f"   - {user_count} users")
        print(f"   - {patient_count} patients")
        print(f"   - {scan_count} scans")
        print(f"   - {audit_count} audit logs")
        
        # Test a query
        first_user = session.query(User).first()
        if first_user:
            print(f"\n✅ Sample query successful: {first_user.email}")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Breast Cancer Detection System from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--postgres-url",
        help="PostgreSQL connection URL (postgresql://user:password@host:5432/dbname)",
        default=os.environ.get("DATABASE_URL")
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables in PostgreSQL before migration (DESTRUCTIVE!)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify connection, don't migrate"
    )
    
    args = parser.parse_args()
    
    if not args.postgres_url:
        print("❌ Error: PostgreSQL URL not provided!")
        print("\nUsage:")
        print("  python migrate_to_postgres.py --postgres-url 'postgresql://user:pass@host:5432/db'")
        print("  OR set DATABASE_URL environment variable")
        sys.exit(1)
    
    # Create engines
    print("🔄 Connecting to databases...")
    postgres_engine = create_postgres_engine(args.postgres_url)
    
    # Verify PostgreSQL connection
    if not verify_postgres_connection(postgres_engine):
        sys.exit(1)
    
    if args.verify_only:
        print("\n✅ Verification complete - connection successful!")
        return
    
    # Check SQLite database exists
    if not os.path.exists("breast_cancer_detection.db"):
        print("❌ Error: SQLite database not found!")
        print("   Expected: breast_cancer_detection.db")
        sys.exit(1)
    
    sqlite_engine = create_sqlite_engine()
    print("✅ Connected to SQLite database")
    
    # Confirm migration
    if args.drop_existing:
        print("\n⚠️  WARNING: This will DROP all existing tables in PostgreSQL!")
        if sys.stdin.isatty():
            confirm = input("Type 'yes' to continue: ")
            if confirm.lower() != 'yes':
                print("❌ Migration cancelled")
                sys.exit(0)
        else:
            print("⚠️  Running in non-interactive mode, proceeding with migration...")
    
    # Perform migration
    success = migrate_data(sqlite_engine, postgres_engine, args.drop_existing)
    
    if success:
        # Verify
        verify_migration(postgres_engine)
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Update your .env file with the PostgreSQL URL")
        print("   2. Restart your backend server")
        print("   3. Test the application")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

