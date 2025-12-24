"""
Database Initialization Script for Multi-Tenant SaaS Platform
Creates tables, super admin, and sample data
"""

import sys
import argparse
from datetime import datetime, date
from sqlalchemy.orm import Session

from database_saas import engine, SessionLocal, create_all_tables
from models_saas import (
    Base, User, Tenant, Patient, Scan, AuditLog,
    UserRole, OrganizationType, SubscriptionStatus, Gender
)
from auth_saas import hash_password


def init_database(with_sample: bool = False):
    """Initialize database with tables and super admin"""
    
    print("=" * 80)
    print("Breast Cancer Detection - Multi-Tenant SaaS Platform")
    print("Database Initialization")
    print("=" * 80)
    
    # Create all tables
    print("\nCreating database tables...")
    create_all_tables()
    
    db = SessionLocal()
    
    try:
        # Check if super admin already exists
        existing_super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN
        ).first()
        
        if existing_super_admin:
            print(f"[!] Super Admin already exists: {existing_super_admin.email}")
        else:
            # Create Super Admin
            print("\n[*] Creating Super Admin...")
            super_admin = User(
                username="superadmin",
                email="superadmin@breastcancer-saas.com",
                password_hash=hash_password("SuperAdmin@123"),
                full_name="Super Administrator",
                role=UserRole.SUPER_ADMIN,
                tenant_id=None,
                is_active=True,
                is_verified=True
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            print(f"[OK] Super Admin created: {super_admin.email}")
            print(f"   Username: {super_admin.username}")
            print(f"   Password: SuperAdmin@123")
            print(f"   [!] CHANGE THIS PASSWORD IMMEDIATELY!")
        
        if with_sample:
            print("\n[*] Creating sample data...")
            create_sample_data(db)
        
        print("\n" + "=" * 80)
        print("[OK] Database initialization completed successfully!")
        print("=" * 80)
        
        # Print credentials summary
        print("\n[*] LOGIN CREDENTIALS:")
        print("-" * 80)
        print("Super Admin:")
        print("  Email: superadmin@breastcancer-saas.com")
        print("  Username: superadmin")
        print("  Password: SuperAdmin@123")
        
        if with_sample:
            print("\nSample Hospital Admin (Apollo Hospitals):")
            print("  Email: admin@apollo-hospitals.com")
            print("  Username: admin.apollo")
            print("  Password: Apollo@123")
            
            print("\nSample Doctor (Apollo):")
            print("  Email: dr.sharma@apollo-hospitals.com")
            print("  Username: dr.rishabh.sharma")
            print("  Password: Doctor@123")
            
            print("\nSample Patient (Apollo):")
            print("  Email: priya.patel@email.com")
            print("  Username: priya.patel")
            print("  Password: Patient@123")
        
        print("-" * 80)
        print("\n[!] IMPORTANT: Change all default passwords before production use!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_sample_data(db: Session):
    """Create sample tenants, users, and patients"""
    
    # ========================================================================
    # TENANT 1: Apollo Hospitals (Large Hospital Chain)
    # ========================================================================
    print("\n  Creating Tenant 1: Apollo Hospitals...")
    apollo = Tenant(
        name="Apollo Hospitals",
        organization_type=OrganizationType.HOSPITAL,
        subscription_status=SubscriptionStatus.ACTIVE,
        contact_email="contact@apollo-hospitals.com",
        contact_phone="+91-11-26925858",
        address="Sarita Vihar, Mathura Road",
        city="New Delhi",
        state="Delhi",
        country="India",
        postal_code="110076",
        monthly_scan_limit=500,
        current_month_scans=0,
        total_scans_processed=0,
        primary_color="#1E40AF"
    )
    db.add(apollo)
    db.commit()
    db.refresh(apollo)
    print(f"  [OK] Tenant created: {apollo.name} (ID: {apollo.id})")
    
    # Organization Admin for Apollo
    apollo_admin = User(
        username="admin.apollo",
        email="admin@apollo-hospitals.com",
        password_hash=hash_password("Apollo@123"),
        full_name="Dr. Rajiv Mehta",
        role=UserRole.ORGANIZATION_ADMIN,
        tenant_id=apollo.id,
        phone="+91-98765-43210",
        department="IT Administration",
        is_active=True,
        is_verified=True
    )
    db.add(apollo_admin)
    
    # Doctor at Apollo
    apollo_doctor = User(
        username="dr.rishabh.sharma",
        email="dr.sharma@apollo-hospitals.com",
        password_hash=hash_password("Doctor@123"),
        full_name="Dr. Rishabh Sharma",
        role=UserRole.DOCTOR,
        tenant_id=apollo.id,
        phone="+91-98765-11111",
        gender=Gender.MALE,
        license_number="DMC-2015-12345",
        department="Radiology",
        specialization="Breast Imaging",
        is_active=True,
        is_verified=True
    )
    db.add(apollo_doctor)
    
    # Lab Tech at Apollo
    apollo_labtech = User(
        username="tech.kumar",
        email="kumar@apollo-hospitals.com",
        password_hash=hash_password("LabTech@123"),
        full_name="Amit Kumar",
        role=UserRole.LAB_TECH,
        tenant_id=apollo.id,
        phone="+91-98765-22222",
        gender=Gender.MALE,
        department="Pathology",
        is_active=True,
        is_verified=True
    )
    db.add(apollo_labtech)
    
    db.commit()
    print(f"  [OK] Created 3 users for Apollo Hospitals")
    
    # Patients at Apollo
    patient1_user = User(
        username="priya.patel",
        email="priya.patel@email.com",
        password_hash=hash_password("Patient@123"),
        full_name="Priya Patel",
        role=UserRole.PATIENT,
        tenant_id=apollo.id,
        phone="+91-98765-33333",
        gender=Gender.FEMALE,
        date_of_birth=date(1985, 3, 15),
        is_active=True,
        is_verified=True
    )
    db.add(patient1_user)
    db.commit()
    db.refresh(patient1_user)
    
    patient1 = Patient(
        tenant_id=apollo.id,
        user_id=patient1_user.id,
        mrn=f"T{apollo.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0001",
        full_name="Priya Patel",
        date_of_birth=date(1985, 3, 15),
        gender=Gender.FEMALE,
        email="priya.patel@email.com",
        phone="+91-98765-33333",
        address="123 MG Road",
        city="New Delhi",
        state="Delhi",
        postal_code="110001",
        blood_group="A+",
        emergency_contact_name="Rahul Patel",
        emergency_contact_phone="+91-98765-44444",
        emergency_contact_relation="Husband",
        medical_history_json={
            "allergies": [],
            "conditions": [],
            "medications": []
        },
        family_history_json={
            "breast_cancer": False,
            "other_cancers": []
        }
    )
    db.add(patient1)
    
    patient2_user = User(
        username="anjali.singh",
        email="anjali.singh@email.com",
        password_hash=hash_password("Patient@123"),
        full_name="Anjali Singh",
        role=UserRole.PATIENT,
        tenant_id=apollo.id,
        phone="+91-98765-55555",
        gender=Gender.FEMALE,
        date_of_birth=date(1978, 7, 22),
        is_active=True,
        is_verified=True
    )
    db.add(patient2_user)
    db.commit()
    db.refresh(patient2_user)
    
    patient2 = Patient(
        tenant_id=apollo.id,
        user_id=patient2_user.id,
        mrn=f"T{apollo.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0002",
        full_name="Anjali Singh",
        date_of_birth=date(1978, 7, 22),
        gender=Gender.FEMALE,
        email="anjali.singh@email.com",
        phone="+91-98765-55555",
        address="456 Park Street",
        city="New Delhi",
        state="Delhi",
        postal_code="110002",
        blood_group="B+",
        emergency_contact_name="Vikram Singh",
        emergency_contact_phone="+91-98765-66666",
        emergency_contact_relation="Brother"
    )
    db.add(patient2)
    db.commit()
    print(f"  [OK] Created 2 patients for Apollo Hospitals")
    
    # ========================================================================
    # TENANT 2: PATH Labs (Diagnostic Chain)
    # ========================================================================
    print("\n  Creating Tenant 2: Dr. Lal PathLabs...")
    pathlabs = Tenant(
        name="Dr. Lal PathLabs",
        organization_type=OrganizationType.PATHOLOGY_LAB,
        subscription_status=SubscriptionStatus.TRIAL,
        contact_email="info@lalpathlabs.com",
        contact_phone="+91-11-30211000",
        address="Block E, Rohini",
        city="New Delhi",
        state="Delhi",
        country="India",
        postal_code="110085",
        monthly_scan_limit=200,
        current_month_scans=0,
        total_scans_processed=0,
        primary_color="#059669"
    )
    db.add(pathlabs)
    db.commit()
    db.refresh(pathlabs)
    print(f"  [OK] Tenant created: {pathlabs.name} (ID: {pathlabs.id})")
    
    # Organization Admin for PathLabs
    pathlabs_admin = User(
        username="admin.pathlabs",
        email="admin@lalpathlabs.com",
        password_hash=hash_password("PathLabs@123"),
        full_name="Dr. Sunita Lal",
        role=UserRole.ORGANIZATION_ADMIN,
        tenant_id=pathlabs.id,
        phone="+91-98765-77777",
        department="Operations",
        is_active=True,
        is_verified=True
    )
    db.add(pathlabs_admin)
    
    # Lab Tech at PathLabs
    pathlabs_tech = User(
        username="tech.verma",
        email="verma@lalpathlabs.com",
        password_hash=hash_password("LabTech@123"),
        full_name="Rohan Verma",
        role=UserRole.LAB_TECH,
        tenant_id=pathlabs.id,
        phone="+91-98765-88888",
        gender=Gender.MALE,
        department="Imaging",
        is_active=True,
        is_verified=True
    )
    db.add(pathlabs_tech)
    db.commit()
    print(f"  [OK] Created 2 users for Dr. Lal PathLabs")
    
    # Patient at PathLabs
    patient3_user = User(
        username="meera.kapoor",
        email="meera.kapoor@email.com",
        password_hash=hash_password("Patient@123"),
        full_name="Meera Kapoor",
        role=UserRole.PATIENT,
        tenant_id=pathlabs.id,
        phone="+91-98765-99999",
        gender=Gender.FEMALE,
        date_of_birth=date(1990, 11, 5),
        is_active=True,
        is_verified=True
    )
    db.add(patient3_user)
    db.commit()
    db.refresh(patient3_user)
    
    patient3 = Patient(
        tenant_id=pathlabs.id,
        user_id=patient3_user.id,
        mrn=f"T{pathlabs.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0001",
        full_name="Meera Kapoor",
        date_of_birth=date(1990, 11, 5),
        gender=Gender.FEMALE,
        email="meera.kapoor@email.com",
        phone="+91-98765-99999",
        address="789 Nehru Place",
        city="New Delhi",
        state="Delhi",
        postal_code="110019",
        blood_group="O+"
    )
    db.add(patient3)
    db.commit()
    print(f"  [OK] Created 1 patient for Dr. Lal PathLabs")
    
    print("\n  [OK] Sample data creation completed!")


def reset_database():
    """Drop all tables and reinitialize"""
    print("\n[!] WARNING: This will DELETE ALL DATA!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() == "yes":
        print("\n[*] Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped")
        
        print("\n[*] Recreating tables...")
        init_database(with_sample=True)
    else:
        print("[CANCELLED] Database reset cancelled")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize SaaS database")
    parser.add_argument(
        "--with-sample",
        action="store_true",
        help="Create sample tenants, users, and patients"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate all tables)"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database(with_sample=args.with_sample)

