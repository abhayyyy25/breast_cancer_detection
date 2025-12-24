"""
Add legacy admin account for backward compatibility
This allows login with admin@hospital.com / Admin@123
"""

from database_saas import SessionLocal
from models_saas import User, Tenant, UserRole
from auth_saas import hash_password

def add_legacy_admin():
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == 'admin@hospital.com').first()
        
        if existing_admin:
            print(f"[!] Admin already exists: {existing_admin.username}")
            print(f"    Email: {existing_admin.email}")
            return
        
        # Get Apollo Hospitals tenant (ID should be 1)
        apollo = db.query(Tenant).filter(Tenant.name == 'Apollo Hospitals').first()
        
        if not apollo:
            print("[ERROR] Apollo Hospitals tenant not found!")
            print("[INFO] Please run: python init_db_saas.py --with-sample")
            return
        
        # Create legacy admin account
        legacy_admin = User(
            username='admin@hospital.com',  # Use email as username for compatibility
            email='admin@hospital.com',
            password_hash=hash_password('Admin@123'),
            full_name='Hospital Administrator',
            role=UserRole.ORGANIZATION_ADMIN,
            tenant_id=apollo.id,
            phone='+91-98765-00000',
            department='Administration',
            is_active=True,
            is_verified=True
        )
        
        db.add(legacy_admin)
        db.commit()
        db.refresh(legacy_admin)
        
        print("[OK] Legacy admin account created successfully!")
        print(f"    Username: {legacy_admin.username}")
        print(f"    Email: {legacy_admin.email}")
        print(f"    Password: Admin@123")
        print(f"    Tenant: {apollo.name}")
        print(f"    Role: {legacy_admin.role}")
        
    except Exception as e:
        print(f"[ERROR] Failed to create admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    add_legacy_admin()

