"""
Authentication utilities for JWT and password hashing.

Implements secure authentication using:
- JWT (JSON Web Tokens) for stateless authentication
- bcrypt for password hashing
- Token expiration and refresh logic
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from database import get_db
from models import User, AuditLog

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR-SECRET-KEY-CHANGE-IN-PRODUCTION-MIN-32-CHARS-LONG-RANDOM-STRING")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode in the token
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Validates JWT token and retrieves user from database.
    
    Usage:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert string ID back to integer
        user_id: int = int(user_id_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
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
            detail="Inactive user account"
        )
    
    return user


def get_current_active_doctor(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is an active doctor.
    
    Usage:
        @app.post("/analyze")
        def analyze(current_user: User = Depends(get_current_active_doctor)):
            # Only doctors can access this
            pass
    """
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can perform this action"
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is an admin.
    
    Usage:
        @app.post("/users")
        def create_user(current_user: User = Depends(get_current_admin)):
            # Only admins can create users
            pass
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log an audit entry for compliance tracking.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: Action being performed (e.g., "VIEW_PATIENT", "CREATE_SCAN")
        resource_type: Type of resource (e.g., "patient", "scan", "auth")
        resource_id: ID of the resource being accessed
        patient_id: Patient ID if applicable
        scan_id: Scan ID if applicable
        details: Additional details (JSON string)
        ip_address: IP address of the request
        user_agent: User agent of the request
    """
    audit_log = AuditLog(
        user_id=user_id,
        patient_id=patient_id,
        scan_id=scan_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("user-agent", "unknown")

