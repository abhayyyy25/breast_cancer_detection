"""
Multi-Tenant Authentication & Authorization System
Supports 4-level role hierarchy with tenant isolation
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import string
import os

from models_saas import User, Tenant, UserRole, AuditLog
from schemas_saas import TokenData
from database_saas import get_db


# ============================================================================
# CONFIGURATION
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password meets complexity requirements
    if (any(c.islower() for c in password) and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password)):
        return password
    else:
        # Recursively try again if complexity not met
        return generate_secure_password(length)


def generate_username(full_name: str, tenant_id: Optional[int] = None) -> str:
    """Generate a unique username from full name"""
    # Remove special characters and convert to lowercase
    base_username = ''.join(c.lower() for c in full_name if c.isalnum() or c.isspace())
    base_username = base_username.replace(' ', '.')
    
    # Add tenant prefix if applicable
    if tenant_id:
        username = f"t{tenant_id}.{base_username}"
    else:
        username = base_username
    
    # Add random suffix to ensure uniqueness
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"{username}.{random_suffix}"


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        tenant_id: Optional[int] = payload.get("tenant_id")
        
        if username is None or user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=UserRole(role),
            tenant_id=tenant_id
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# ============================================================================
# ROLE-BASED AUTHORIZATION
# ============================================================================

class RoleChecker:
    """Dependency class to check if user has required role"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Specific role checkers
require_super_admin = RoleChecker([UserRole.SUPER_ADMIN])

require_org_admin = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ORGANIZATION_ADMIN])

require_medical_staff = RoleChecker([
    UserRole.SUPER_ADMIN,
    UserRole.ORGANIZATION_ADMIN,
    UserRole.DOCTOR,
    UserRole.LAB_TECH
])

require_patient = RoleChecker([UserRole.PATIENT])


# ============================================================================
# TENANT ISOLATION
# ============================================================================

class TenantChecker:
    """Ensure user can only access data within their tenant"""
    
    def __init__(self, allow_super_admin: bool = True):
        self.allow_super_admin = allow_super_admin
    
    def __call__(
        self,
        tenant_id: int,
        current_user: User = Depends(get_current_user)
    ) -> bool:
        """Check if user has access to the specified tenant"""
        
        # Super admin can access all tenants
        if self.allow_super_admin and current_user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Other users can only access their own tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Cannot access data from another organization."
            )
        
        return True


def get_user_tenant_id(current_user: User = Depends(get_current_user)) -> int:
    """Get the tenant ID of the current user"""
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super admin is not associated with a tenant"
        )
    
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any organization"
        )
    
    return current_user.tenant_id


async def verify_tenant_access(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """Verify user has access to tenant and return tenant object"""
    
    # Super admin can access all tenants
    if current_user.role != UserRole.SUPER_ADMIN:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization account is suspended"
        )
    
    return tenant


# ============================================================================
# PATIENT DATA ACCESS CONTROL
# ============================================================================

async def verify_patient_access(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify user has permission to access patient data"""
    from models_saas import Patient
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Super admin can access all patients
    if current_user.role == UserRole.SUPER_ADMIN:
        return patient
    
    # Patients can only access their own data
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own data."
            )
        return patient
    
    # Medical staff can only access patients in their tenant
    if current_user.tenant_id != patient.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient belongs to another organization."
        )
    
    return patient


# ============================================================================
# AUDIT LOGGING
# ============================================================================

async def create_audit_log(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    description: Optional[str] = None,
    request: Optional[Request] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """Create an audit log entry"""
    
    audit_log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        user_role=user.role.value,
        user_name=user.full_name,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        patient_id=patient_id,
        scan_id=scan_id,
        description=description,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        request_method=request.method if request else None,
        request_path=str(request.url.path) if request else None,
        success=success,
        error_message=error_message
    )
    
    db.add(audit_log)
    db.commit()
    return audit_log


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        # Try email as username
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        db.commit()
        return None
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def create_user_with_credentials(
    db: Session,
    email: str,
    full_name: str,
    role: UserRole,
    tenant_id: Optional[int] = None,
    **kwargs
) -> tuple[User, str]:
    """
    Create a new user with auto-generated username and password
    Returns: (User object, plain_password)
    """
    
    # Generate secure credentials
    username = generate_username(full_name, tenant_id)
    plain_password = generate_secure_password()
    
    # Ensure username is unique
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        # Add more randomness if collision occurs
        username = f"{username}.{secrets.token_hex(2)}"
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(plain_password),
        full_name=full_name,
        role=role,
        tenant_id=tenant_id,
        **kwargs
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user, plain_password

