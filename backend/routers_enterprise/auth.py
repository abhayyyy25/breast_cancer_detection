"""
Authentication Router

Endpoints:
- POST /auth/login: User login
- POST /auth/logout: User logout  
- POST /auth/refresh: Refresh access token
- GET /auth/me: Get current user profile
- PUT /auth/me: Update current user profile
- POST /auth/change-password: Change password

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database_enterprise import get_db
from models_enterprise import User, UserRole, AuditAction
from schemas_enterprise import (
    LoginRequest, Token, PasswordChange, UserResponse, UserUpdate
)
from auth_enterprise import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_active_user, log_audit, get_client_ip, get_user_agent,
    verify_password, get_password_hash, refresh_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Supports all 4 user roles:
    - super_admin: Platform-wide access
    - org_admin: Organization management
    - doctor/lab_tech/nurse: Medical workflows
    - patient: Patient portal access
    """
    user = await authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        # Log failed attempt
        log_audit(
            db=db,
            action=AuditAction.LOGIN,
            resource_type="auth",
            description=f"Failed login attempt for: {login_data.username}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=False,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check tenant status for non-super admins
    if user.role != UserRole.SUPER_ADMIN and user.tenant:
        if not user.tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is inactive"
            )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if login_data.remember_me:
        access_token_expires = timedelta(days=7)
    
    access_token = create_access_token(user, access_token_expires)
    refresh_token = create_refresh_token(user)
    
    # Log successful login
    log_audit(
        db=db,
        action=AuditAction.LOGIN,
        resource_type="auth",
        user_id=user.id,
        tenant_id=user.tenant_id,
        description=f"User logged in: {user.email}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "user": UserResponse.model_validate(user)
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.
    
    Logs the logout event for audit purposes.
    Token invalidation should be handled client-side.
    """
    log_audit(
        db=db,
        action=AuditAction.LOGOUT,
        resource_type="auth",
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        description=f"User logged out: {current_user.email}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_str: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    new_access_token, new_refresh_token = await refresh_access_token(
        refresh_token_str, db
    )
    
    # Get user for response
    from auth_enterprise import decode_token
    payload = decode_token(new_access_token)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user's profile.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: Request,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Users can update:
    - Name, phone, avatar
    - Preferences (timezone, locale, theme)
    
    Cannot update:
    - Email, username, role, tenant
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Remove fields that users cannot self-update
    protected_fields = ["is_active", "department_id"]
    for field in protected_fields:
        update_dict.pop(field, None)
    
    # Store old values for audit
    old_values = {
        k: getattr(current_user, k) 
        for k in update_dict.keys() 
        if hasattr(current_user, k)
    }
    
    # Apply updates
    for field, value in update_dict.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Log update
    log_audit(
        db=db,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        description="User updated own profile",
        old_values=old_values,
        new_values=update_dict,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    Requires current password verification.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.must_change_password = False
    db.commit()
    
    # Log password change
    log_audit(
        db=db,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=current_user.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        description="User changed password",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return {"message": "Password changed successfully"}

