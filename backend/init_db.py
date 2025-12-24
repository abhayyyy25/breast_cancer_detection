"""
Database initialization script.

Run this script to:
1. Create all database tables
2. Create an initial admin user (if not exists)
3. Optionally create sample data for testing

Usage:
    python init_db.py                    # Initialize database only
    python init_db.py --with-sample     # Initialize with sample data
    python init_db.py --reset           # Reset database (DELETE ALL DATA!)
"""

import sys
import argparse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import init_db, reset_db, SessionLocal
from models import User, Patient, UserRole
from auth_utils import get_password_hash


def create_admin_user(db: Session):
    """Create default admin user if not exists."""
    admin_email = "admin@hospital.com"
    
    # Check if admin exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    
    if existing_admin:
        print(f"✅ Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create admin user
    admin = User(
        email=admin_email,
        hashed_password=get_password_hash("Admin@123"),  # Change this in production!
        full_name="System Administrator",
        role=UserRole.ADMIN,
        license_number="ADMIN-001",
        department="Administration",
        is_active=1
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✅ Admin user created successfully!")
    print(f"   Email: {admin_email}")
    print(f"   Password: Admin@123")
    print(f"   ⚠️ CHANGE THIS PASSWORD IN PRODUCTION!")
    
    return admin


def create_sample_users(db: Session):
    """Create sample doctor and lab tech users."""
    users_data = [
        {
            "email": "dr.smith@hospital.com",
            "password": "Doctor@123",
            "full_name": "Dr. Sarah Smith",
            "role": UserRole.DOCTOR,
            "license_number": "MD-12345",
            "department": "Radiology"
        },
        {
            "email": "dr.johnson@hospital.com",
            "password": "Doctor@123",
            "full_name": "Dr. Michael Johnson",
            "role": UserRole.DOCTOR,
            "license_number": "MD-67890",
            "department": "Oncology"
        },
        {
            "email": "lab.tech@hospital.com",
            "password": "LabTech@123",
            "full_name": "Emily Brown",
            "role": UserRole.LAB_TECH,
            "license_number": "LT-54321",
            "department": "Laboratory"
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            print(f"ℹ️  User already exists: {user_data['email']}")
            continue
        
        # Create user
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            license_number=user_data["license_number"],
            department=user_data["department"],
            is_active=1
        )
        
        db.add(user)
        created_users.append(user_data)
    
    db.commit()
    
    if created_users:
        print(f"\n✅ Created {len(created_users)} sample users:")
        for user_data in created_users:
            print(f"   - {user_data['email']} (Password: {user_data['password']})")
    
    return created_users


def create_sample_patients(db: Session):
    """Create sample patient records."""
    patients_data = [
        {
            "medical_record_number": "MRN-001",
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": datetime(1985, 5, 15),
            "gender": "Female",
            "contact_phone": "+1-555-0101",
            "contact_email": "jane.doe@email.com",
            "address": "123 Main St, Anytown, USA"
        },
        {
            "medical_record_number": "MRN-002",
            "first_name": "Mary",
            "last_name": "Johnson",
            "date_of_birth": datetime(1972, 8, 22),
            "gender": "Female",
            "contact_phone": "+1-555-0102",
            "contact_email": "mary.johnson@email.com",
            "address": "456 Oak Ave, Somewhere, USA"
        },
        {
            "medical_record_number": "MRN-003",
            "first_name": "Susan",
            "last_name": "Williams",
            "date_of_birth": datetime(1990, 3, 10),
            "gender": "Female",
            "contact_phone": "+1-555-0103",
            "contact_email": "susan.williams@email.com",
            "address": "789 Pine Rd, Elsewhere, USA"
        }
    ]
    
    created_patients = []
    
    for patient_data in patients_data:
        # Check if patient exists
        existing_patient = db.query(Patient).filter(
            Patient.medical_record_number == patient_data["medical_record_number"]
        ).first()
        
        if existing_patient:
            print(f"ℹ️  Patient already exists: {patient_data['medical_record_number']}")
            continue
        
        # Create patient
        patient = Patient(**patient_data)
        db.add(patient)
        created_patients.append(patient_data)
    
    db.commit()
    
    if created_patients:
        print(f"\n✅ Created {len(created_patients)} sample patients:")
        for patient_data in created_patients:
            print(f"   - {patient_data['medical_record_number']}: {patient_data['first_name']} {patient_data['last_name']}")
    
    return created_patients


def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(description="Initialize database for Breast Cancer Detection System")
    parser.add_argument("--reset", action="store_true", help="Reset database (DELETE ALL DATA!)")
    parser.add_argument("--with-sample", action="store_true", help="Create sample data for testing")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("Breast Cancer Detection Hospital System - Database Initialization")
    print("="*70 + "\n")
    
    # Reset database if requested
    if args.reset:
        print("⚠️  WARNING: This will DELETE ALL DATA!")
        confirm = input("Type 'yes' to confirm: ")
        
        if confirm.lower() != "yes":
            print("❌ Database reset cancelled.")
            return
        
        print("\n🔄 Resetting database...")
        reset_db()
        print("✅ Database reset complete!")
    else:
        # Initialize database
        print("🔄 Initializing database...")
        init_db()
    
    # Create admin user
    print("\n📝 Creating admin user...")
    db = SessionLocal()
    try:
        admin = create_admin_user(db)
        
        # Create sample data if requested
        if args.with_sample:
            print("\n📝 Creating sample users...")
            create_sample_users(db)
            
            print("\n📝 Creating sample patients...")
            create_sample_patients(db)
        
        print("\n" + "="*70)
        print("✅ Database initialization complete!")
        print("="*70)
        
        print("\n🔐 Login Credentials:")
        print(f"   Admin: admin@hospital.com / Admin@123")
        
        if args.with_sample:
            print(f"   Doctor: dr.smith@hospital.com / Doctor@123")
            print(f"   Lab Tech: lab.tech@hospital.com / LabTech@123")
        
        print("\n⚠️  IMPORTANT: Change default passwords in production!")
        print("\n🚀 You can now start the server with: uvicorn main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

