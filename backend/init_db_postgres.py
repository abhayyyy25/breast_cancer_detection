"""
Initialize PostgreSQL Database for Multi-Tenant SaaS Platform
Creates all tables and optionally adds sample data
"""

import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database_saas import engine, Base, SessionLocal
from models_saas import User, Tenant, Patient, Scan
from auth_saas import hash_password


def create_tables():
    """Create all database tables"""
    print("\n" + "=" * 80)
    print("Creating PostgreSQL database tables...")
    print("=" * 80)
    
    try:
        # Import all models to ensure they're registered
        from models_saas import User, Tenant, Patient, Scan
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("[OK] All database tables created successfully")
        print(f"[OK] Tables: {', '.join(Base.metadata.tables.keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        return False


def create_super_admin(db):
    """Create Super Admin user"""
    print("\n[*] Creating Super Admin...")
    
    # Check if super admin already exists
    existing = db.query(User).filter(User.username == "superadmin").first()
    if existing:
        print("[!] Super Admin already exists - skipping")
        return existing
    
    super_admin = User(
        username="superadmin",
        email="superadmin@breastcancer-saas.com",
        password_hash=hash_password("SuperAdmin@123"),
        role="super_admin",
        full_name="System Administrator",
        is_active=True,
        is_verified=True
    )
    
    db.add(super_admin)
    db.commit()
    db.refresh(super_admin)
    
    print("[OK] Super Admin created successfully")
    print(f"   Email: {super_admin.email}")
    print(f"   Username: {super_admin.username}")
    print(f"   Password: SuperAdmin@123")
    print("   [!] CHANGE THIS PASSWORD IMMEDIATELY!")
    
    return super_admin


def create_sample_data(db):
    """Create sample tenants and users"""
    print("\n[*] Creating sample data...")
    
    # Create Tenant 1: Apollo Hospitals
    print("\n  Creating Tenant 1: Apollo Hospitals...")
    from models_saas import OrganizationType, SubscriptionStatus
    apollo = Tenant(
        name="Apollo Hospitals",
        organization_type=OrganizationType.HOSPITAL,
        subscription_status=SubscriptionStatus.ACTIVE,
        contact_email="admin@apollo-hospitals.com",
        contact_phone="+91-11-2612-3456",
        address="Indraprastha Apollo Hospitals, Sarita Vihar, Delhi",
        city="Delhi",
        state="Delhi",
        country="India",
        is_active=True
    )
    db.add(apollo)
    db.commit()
    db.refresh(apollo)
    print(f"  [OK] Tenant created: {apollo.name} (ID: {apollo.id})")
    
    # Create Apollo Admin
    apollo_admin = User(
        tenant_id=apollo.id,
        username="admin.apollo",
        email="admin@apollo-hospitals.com",
        password_hash=hash_password("Apollo@123"),
        role="organization_admin",
        full_name="Dr. Rajesh Kumar",
        phone="+91-11-2612-3456",
        is_active=True,
        is_verified=True
    )
    db.add(apollo_admin)
    
    # Create Apollo Doctor
    apollo_doctor = User(
        tenant_id=apollo.id,
        username="dr.rishabh.sharma",
        email="dr.sharma@apollo-hospitals.com",
        password_hash=hash_password("Doctor@123"),
        role="doctor",
        full_name="Dr. Rishabh Sharma",
        phone="+91-98765-43210",
        department="Oncology",
        specialization="Breast Cancer Specialist",
        license_number="MCI-12345",
        is_active=True,
        is_verified=True,
        created_by_user_id=apollo_admin.id
    )
    db.add(apollo_doctor)
    
    # Create Apollo Lab Tech
    apollo_tech = User(
        tenant_id=apollo.id,
        username="tech.priya",
        email="priya.tech@apollo-hospitals.com",
        password_hash=hash_password("LabTech@123"),
        role="lab_tech",
        full_name="Priya Verma",
        phone="+91-98765-11111",
        department="Radiology",
        license_number="RAD-67890",
        is_active=True,
        is_verified=True,
        created_by_user_id=apollo_admin.id
    )
    db.add(apollo_tech)
    
    db.commit()
    print("  [OK] Created 3 users for Apollo Hospitals")
    
    # Create sample patients for Apollo (with User accounts)
    from models_saas import Gender
    
    # Patient 1: Priya Patel
    patient1_user = User(
        tenant_id=apollo.id,
        username="priya.patel",
        email="priya.patel@email.com",
        password_hash=hash_password("Patient@123"),
        role="patient",
        full_name="Priya Patel",
        phone="+91-98765-00001",
        date_of_birth=datetime(1985, 5, 15).date(),
        gender="female",
        is_active=True,
        is_verified=True,
        created_by_user_id=apollo_doctor.id
    )
    db.add(patient1_user)
    db.commit()
    db.refresh(patient1_user)
    
    patient1 = Patient(
        tenant_id=apollo.id,
        user_id=patient1_user.id,
        mrn=f"T{apollo.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0001",
        full_name="Priya Patel",
        email="priya.patel@email.com",
        phone="+91-98765-00001",
        date_of_birth=datetime(1985, 5, 15).date(),
        gender=Gender.FEMALE,
        address="123 MG Road, Mumbai, Maharashtra",
        city="Mumbai",
        state="Maharashtra",
        emergency_contact_name="Raj Patel",
        emergency_contact_phone="+91-98765-00002",
        emergency_contact_relation="Spouse"
    )
    db.add(patient1)
    
    # Patient 2: Anita Desai
    patient2_user = User(
        tenant_id=apollo.id,
        username="anita.desai",
        email="anita.desai@email.com",
        password_hash=hash_password("Patient@123"),
        role="patient",
        full_name="Anita Desai",
        phone="+91-98765-00003",
        date_of_birth=datetime(1978, 8, 22).date(),
        gender="female",
        is_active=True,
        is_verified=True,
        created_by_user_id=apollo_doctor.id
    )
    db.add(patient2_user)
    db.commit()
    db.refresh(patient2_user)
    
    patient2 = Patient(
        tenant_id=apollo.id,
        user_id=patient2_user.id,
        mrn=f"T{apollo.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0002",
        full_name="Anita Desai",
        email="anita.desai@email.com",
        phone="+91-98765-00003",
        date_of_birth=datetime(1978, 8, 22).date(),
        gender=Gender.FEMALE,
        address="456 Park Street, Kolkata, West Bengal",
        city="Kolkata",
        state="West Bengal",
        emergency_contact_name="Vikram Desai",
        emergency_contact_phone="+91-98765-00004",
        emergency_contact_relation="Spouse"
    )
    db.add(patient2)
    
    db.commit()
    print("  [OK] Created 2 patients for Apollo Hospitals")
    
    # Create Tenant 2: Dr. Lal PathLabs
    print("\n  Creating Tenant 2: Dr. Lal PathLabs...")
    pathlabs = Tenant(
        name="Dr. Lal PathLabs",
        organization_type=OrganizationType.PATHOLOGY_LAB,
        subscription_status=SubscriptionStatus.ACTIVE,
        contact_email="admin@lalpathlabs.com",
        contact_phone="+91-11-4777-7777",
        address="Block E, Sector 18, Rohini, Delhi",
        city="Delhi",
        state="Delhi",
        country="India",
        is_active=True
    )
    db.add(pathlabs)
    db.commit()
    db.refresh(pathlabs)
    print(f"  [OK] Tenant created: {pathlabs.name} (ID: {pathlabs.id})")
    
    # Create PathLabs Admin
    pathlabs_admin = User(
        tenant_id=pathlabs.id,
        username="admin.pathlabs",
        email="admin@lalpathlabs.com",
        password_hash=hash_password("PathLabs@123"),
        role="organization_admin",
        full_name="Dr. Arvind Lal",
        phone="+91-11-4777-7777",
        is_active=True,
        is_verified=True
    )
    db.add(pathlabs_admin)
    
    # Create PathLabs Doctor
    pathlabs_doctor = User(
        tenant_id=pathlabs.id,
        username="dr.meera.singh",
        email="dr.meera@lalpathlabs.com",
        password_hash=hash_password("Doctor@123"),
        role="doctor",
        full_name="Dr. Meera Singh",
        phone="+91-98765-22222",
        department="Pathology",
        specialization="Histopathology",
        license_number="MCI-54321",
        is_active=True,
        is_verified=True,
        created_by_user_id=pathlabs_admin.id
    )
    db.add(pathlabs_doctor)
    
    db.commit()
    print("  [OK] Created 2 users for Dr. Lal PathLabs")
    
    # Create sample patient for PathLabs (with User account)
    patient3_user = User(
        tenant_id=pathlabs.id,
        username="sunita.sharma",
        email="sunita.sharma@email.com",
        password_hash=hash_password("Patient@123"),
        role="patient",
        full_name="Sunita Sharma",
        phone="+91-98765-00005",
        date_of_birth=datetime(1990, 3, 10).date(),
        gender="female",
        is_active=True,
        is_verified=True,
        created_by_user_id=pathlabs_doctor.id
    )
    db.add(patient3_user)
    db.commit()
    db.refresh(patient3_user)
    
    patient3 = Patient(
        tenant_id=pathlabs.id,
        user_id=patient3_user.id,
        mrn=f"T{pathlabs.id:03d}-{datetime.utcnow().strftime('%Y%m%d')}-0001",
        full_name="Sunita Sharma",
        email="sunita.sharma@email.com",
        phone="+91-98765-00005",
        date_of_birth=datetime(1990, 3, 10).date(),
        gender=Gender.FEMALE,
        address="789 Nehru Place, New Delhi",
        city="New Delhi",
        state="Delhi",
        emergency_contact_name="Amit Sharma",
        emergency_contact_phone="+91-98765-00006",
        emergency_contact_relation="Spouse"
    )
    db.add(patient3)
    
    db.commit()
    print("  [OK] Created 1 patient for Dr. Lal PathLabs")
    
    print("\n  [OK] Sample data creation completed!")


def main():
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL Database")
    parser.add_argument(
        "--with-sample",
        action="store_true",
        help="Create sample data (tenants, users, patients)"
    )
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("Breast Cancer Detection - Multi-Tenant SaaS Platform")
    print("PostgreSQL Database Initialization")
    print("=" * 80)
    
    # Create tables
    if not create_tables():
        print("\n[ERROR] Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create Super Admin
        create_super_admin(db)
        
        # Create sample data if requested
        if args.with_sample:
            create_sample_data(db)
        
        print("\n" + "=" * 80)
        print("[OK] PostgreSQL Database initialization completed successfully!")
        print("=" * 80)
        
        print("\n[*] LOGIN CREDENTIALS:")
        print("-" * 80)
        print("Super Admin:")
        print("  Email: superadmin@breastcancer-saas.com")
        print("  Username: superadmin")
        print("  Password: SuperAdmin@123")
        
        if args.with_sample:
            print("\nSample Hospital Admin (Apollo Hospitals):")
            print("  Email: admin@apollo-hospitals.com")
            print("  Username: admin.apollo")
            print("  Password: Apollo@123")
            
            print("\nSample Doctor (Apollo):")
            print("  Email: dr.sharma@apollo-hospitals.com")
            print("  Username: dr.rishabh.sharma")
            print("  Password: Doctor@123")
        
        print("-" * 80)
        print("\n[!] IMPORTANT: Change all default passwords before production use!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

