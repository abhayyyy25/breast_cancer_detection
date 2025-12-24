"""
Enterprise Multi-Tenant Authentication & Authorization System

Features:
- 4-role hierarchy: SuperAdmin, OrgAdmin, MedicalStaff, Patient
- JWT tokens with role-based scopes
- Multi-tenancy data isolation
- Secure password hashing with bcrypt
- Audit logging for all auth events

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string
import uuid
import os
from functools import wraps

from database import get_db
from models_enterprise import (
    User, Tenant, Patient, AuditLog,
    UserRole, AuditAction, SubscriptionStatus
)
from schemas_enterprise import TokenPayload, UserRole as SchemaUserRole


# ==================== CONFIGURATION ====================

# Security settings (use environment variables in production)
SECRET_KEY = os.environ.get("SECRET_KEY", "enterprise-healthcare-saas-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


# ==================== ROLE HIERARCHY ====================

ROLE_HIERARCHY = {
    UserRole.SUPER_ADMIN: 100,
    UserRole.ORG_ADMIN: 80,
    UserRole.DOCTOR: 60,
    UserRole.LAB_TECH: 50,
    UserRole.NURSE: 40,
    UserRole.RECEPTIONIST: 30,
    UserRole.PATIENT: 10,
}

# Role permissions matrix
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        "manage_tenants", "view_all_tenants", "manage_users", "view_system_stats",
        "manage_subscriptions", "view_audit_logs", "system_settings"
    ],
    UserRole.ORG_ADMIN: [
        "manage_org_users", "view_org_users", "manage_departments",
        "view_org_stats", "view_org_audit_logs", "org_settings"
    ],
    UserRole.DOCTOR: [
        "view_patients", "create_patients", "update_patients",
        "view_scans", "create_scans", "review_scans", "approve_scans",
        "create_prescriptions", "sign_prescriptions",
        "view_appointments", "manage_own_appointments"
    ],
    UserRole.LAB_TECH: [
        "view_assigned_patients", "view_scans", "create_scans", "upload_images"
    ],
    UserRole.NURSE: [
        "view_assigned_patients", "view_scans", "view_prescriptions",
        "manage_appointments", "create_reminders"
    ],
    UserRole.RECEPTIONIST: [
        "view_patient_summary", "manage_appointments", "check_in_patients"
    ],
    UserRole.PATIENT: [
        "view_own_profile", "view_own_scans", "view_own_prescriptions",
        "view_own_appointments", "manage_own_medications", "view_own_reminders"
    ],
}


# ==================== PASSWORD UTILITIES ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt."""
    return pwd_context.hash(password)


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password."""
    # Ensure password has uppercase, lowercase, digit, and special char
    uppercase = secrets.choice(string.ascii_uppercase)
    lowercase = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    
    # Fill rest with random characters
    remaining_length = length - 4
    remaining = ''.join(secrets.choice(
        string.ascii_letters + string.digits + "!@#$%^&*"
    ) for _ in range(remaining_length))
    
    # Shuffle all characters
    password_chars = list(uppercase + lowercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)


def generate_username(full_name: str, existing_usernames: List[str]) -> str:
    """Generate unique username from full name."""
    # Clean and split name
    name_parts = full_name.lower().replace(".", "").replace(",", "").split()
    
    if len(name_parts) >= 2:
        base_username = f"{name_parts[0]}.{name_parts[-1]}"
    else:
        base_username = name_parts[0] if name_parts else "user"
    
    # Remove special characters
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '.')
    
    # Ensure uniqueness
    username = base_username
    counter = 1
    while username in existing_usernames:
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


# ==================== JWT TOKEN UTILITIES ====================

def create_access_token(
    user: User,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with user claims.
    
    Claims include:
    - sub: User ID (string)
    - email: User email
    - role: User role
    - tenant_id: Tenant ID (null for super admin)
    - permissions: List of permissions
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
        "permissions": ROLE_PERMISSIONS.get(user.role, []),
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # Unique token ID
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: User) -> str:
    """Create JWT refresh token for token renewal."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user.id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== AUDIT LOGGING ====================

def log_audit(
    db: Session,
    action: AuditAction,
    resource_type: str,
    user_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    description: Optional[str] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """Log action to audit trail for HIPAA compliance."""
    audit_entry = AuditLog(
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        success=success,
        error_message=error_message,
    )
    
    db.add(audit_entry)
    db.commit()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")[:500]


# ==================== AUTHENTICATION DEPENDENCIES ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Validates token and retrieves user from database.
    """
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# ==================== ROLE-BASED ACCESS DEPENDENCIES ====================

def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @app.get("/admin", dependencies=[Depends(require_role([UserRole.SUPER_ADMIN]))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    
    Usage:
        @app.get("/scans", dependencies=[Depends(require_permission("view_scans"))])
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    return permission_checker


async def get_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to ensure user is a Super Admin."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required"
        )
    return current_user


async def get_org_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to ensure user is an Org Admin or higher."""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization Admin access required"
        )
    return current_user


async def get_medical_staff(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to ensure user is medical staff."""
    medical_roles = [
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN,
        UserRole.DOCTOR, UserRole.LAB_TECH, UserRole.NURSE
    ]
    if current_user.role not in medical_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Medical staff access required"
        )
    return current_user


async def get_doctor(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to ensure user is a Doctor or higher."""
    doctor_roles = [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.DOCTOR]
    if current_user.role not in doctor_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required"
        )
    return current_user


async def get_patient_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to get patient user."""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required"
        )
    return current_user


# ==================== MULTI-TENANCY DEPENDENCIES ====================

async def get_current_tenant(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Optional[Tenant]:
    """
    Get current tenant from authenticated user.
    
    Returns None for Super Admins (global access).
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return None  # Super admin has global access
    
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with any organization"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive"
        )
    
    if tenant.subscription_status == SubscriptionStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization subscription is suspended"
        )
    
    return tenant


def require_tenant_access(tenant_id: int):
    """
    Dependency factory to validate access to specific tenant.
    
    Ensures user belongs to the requested tenant or is super admin.
    """
    async def tenant_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user  # Super admin can access any tenant
        
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other organization's data"
            )
        return current_user
    return tenant_checker


# ==================== PATIENT ACCESS CONTROL ====================

async def validate_patient_access(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Patient:
    """
    Validate user has access to specific patient.
    
    - Super Admin: Can access all patients
    - Org Admin/Staff: Can access patients in their tenant
    - Patient: Can only access their own record
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Super admin has global access
    if current_user.role == UserRole.SUPER_ADMIN:
        return patient
    
    # Patient can only access their own record
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile or current_user.patient_profile.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own records"
            )
        return patient
    
    # Staff can access patients in their tenant
    if current_user.tenant_id != patient.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Patient belongs to different organization"
        )
    
    return patient


# ==================== AUTHENTICATION FUNCTIONS ====================

async def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[User]:
    """
    Authenticate user with username/email and password.
    
    Returns user if authentication successful, None otherwise.
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.commit()
        return None
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked. Please try again later."
        )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


async def create_user_for_tenant(
    db: Session,
    tenant_id: int,
    email: str,
    full_name: str,
    role: UserRole,
    created_by: int,
    department_id: Optional[int] = None,
    license_number: Optional[str] = None,
    specialty: Optional[str] = None
) -> tuple[User, str]:
    """
    Create new user for a tenant.
    
    Returns tuple of (user, temporary_password).
    Auto-generates username and secure password.
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate unique username
    existing_usernames = [u.username for u in db.query(User.username).all()]
    username = generate_username(full_name, existing_usernames)
    
    # Generate secure password
    temp_password = generate_secure_password()
    
    # Parse name
    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    # Create user
    user = User(
        tenant_id=tenant_id,
        username=username,
        email=email,
        password_hash=get_password_hash(temp_password),
        role=role,
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        department_id=department_id,
        license_number=license_number,
        specialty=specialty,
        must_change_password=True,
        created_by=created_by,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user, temp_password


# ==================== TOKEN REFRESH ====================

async def refresh_access_token(
    refresh_token: str,
    db: Session
) -> tuple[str, str]:
    """
    Refresh access token using refresh token.
    
    Returns new (access_token, refresh_token) pair.
    """
    try:
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        # Generate new tokens
        new_access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)
        
        return new_access_token, new_refresh_token
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# ==================== HELPER FUNCTIONS ====================

def has_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission."""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_higher_role(user: User, target_role: UserRole) -> bool:
    """Check if user has higher role than target."""
    user_level = ROLE_HIERARCHY.get(user.role, 0)
    target_level = ROLE_HIERARCHY.get(target_role, 0)
    return user_level > target_level


def can_manage_user(manager: User, target: User) -> bool:
    """Check if manager can manage target user."""
    # Super admin can manage anyone
    if manager.role == UserRole.SUPER_ADMIN:
        return True
    
    # Org admin can manage users in their tenant (except super admins)
    if manager.role == UserRole.ORG_ADMIN:
        return (
            manager.tenant_id == target.tenant_id and
            target.role != UserRole.SUPER_ADMIN
        )
    
    return False

