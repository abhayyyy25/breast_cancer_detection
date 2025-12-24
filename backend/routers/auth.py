"""
Authentication router for user login, signup, and profile management.

Endpoints:
- POST /auth/login: User login
- POST /auth/signup: User registration (admin only for doctors)
- GET /auth/me: Get current user profile
- POST /auth/logout: Logout (audit logging)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta

from database import get_db
from models import User, UserRole
from auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_admin,
    log_audit,
    get_client_ip,
    get_user_agent
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== Request/Response Models ====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.DOCTOR
    license_number: Optional[str] = None
    department: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    license_number: Optional[str]
    department: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    
    - Validates email and password
    - Creates JWT token
    - Logs successful login attempt
    - Updates last_login timestamp
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        # Log failed login attempt
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact administrator."
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Log successful login
    log_audit(
        db=db,
        user_id=user.id,
        action="LOGIN",
        resource_type="auth",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "license_number": user.license_number,
            "department": user.department
        }
    }


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    signup_data: SignupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Only admins can create users
):
    """
    Register a new user (doctor/lab tech).
    
    - Admin access required
    - Validates email uniqueness
    - Hashes password securely
    - Creates user account
    - Logs user creation
    
    ⚠️ In production, consider adding email verification.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if license number is already used (if provided)
    if signup_data.license_number:
        existing_license = db.query(User).filter(
            User.license_number == signup_data.license_number
        ).first()
        if existing_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered"
            )
    
    # Create new user
    new_user = User(
        email=signup_data.email,
        hashed_password=get_password_hash(signup_data.password),
        full_name=signup_data.full_name,
        role=signup_data.role,
        license_number=signup_data.license_number,
        department=signup_data.department,
        is_active=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_USER",
        resource_type="user",
        resource_id=new_user.id,
        details=f"Created user: {new_user.email} with role: {new_user.role}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    
    - Requires valid JWT token
    - Returns user details
    """
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (for audit logging purposes).
    
    Note: JWT tokens are stateless, so actual logout happens client-side
    by discarding the token. This endpoint is for audit trail only.
    """
    # Log logout
    log_audit(
        db=db,
        user_id=current_user.id,
        action="LOGOUT",
        resource_type="auth",
        resource_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"message": "Logged out successfully"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    List all users (admin only).
    
    - Admin access required
    - Returns all registered users
    """
    users = db.query(User).all()
    return users

