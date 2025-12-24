"""
Authentication Router - Login, Signup, Profile Management
Handles authentication for all user roles
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from database_saas import get_db
from auth_saas import (
    authenticate_user, create_access_token, get_current_user,
    create_audit_log, hash_password, generate_username
)
from schemas_saas import (
    LoginRequest, LoginResponse, UserResponse,
    ChangePasswordRequest, MessageResponse, TokenData
)
from models_saas import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token
    Accepts username or email as login identifier
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        # Audit failed login attempt
        failed_user = db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()
        
        if failed_user:
            await create_audit_log(
                db=db,
                user=failed_user,
                action="login",
                resource_type="authentication",
                description="Failed login attempt",
                request=request,
                success=False,
                error_message="Invalid password"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact your administrator."
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id
        }
    )
    
    # Audit successful login
    await create_audit_log(
        db=db,
        user=user,
        action="login",
        resource_type="authentication",
        description=f"Successful login: {user.role.value}",
        request=request
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


# ============================================================================
# CURRENT USER
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile
    """
    return current_user


# ============================================================================
# LOGOUT
# ============================================================================

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (audit log only, token invalidation handled client-side)
    """
    await create_audit_log(
        db=db,
        user=current_user,
        action="logout",
        resource_type="authentication",
        description="User logged out",
        request=request
    )
    
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user's password
    """
    from auth_saas import verify_password
    from datetime import datetime
    
    # Verify old password
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    db.commit()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="change_password",
        resource_type="user",
        resource_id=current_user.id,
        description="Password changed successfully",
        request=request
    )
    
    return MessageResponse(
        message="Password changed successfully",
        success=True
    )


@router.post("/reset-password-request", response_model=MessageResponse)
async def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Request password reset (sends email with reset link)
    Note: Implement email sending in production
    """
    user = db.query(User).filter(User.email == email).first()
    
    # Don't reveal if user exists or not (security)
    if not user:
        return MessageResponse(
            message="If the email exists, a password reset link has been sent",
            success=True
        )
    
    # TODO: Generate reset token and send email
    # For now, just return success message
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent",
        success=True
    )


# ============================================================================
# PROFILE UPDATE
# ============================================================================

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: Request,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    bio: Optional[str] = None,
    profile_picture_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's profile information
    """
    from typing import Optional
    from datetime import datetime
    
    if full_name:
        current_user.full_name = full_name
    if phone:
        current_user.phone = phone
    if bio is not None:
        current_user.bio = bio
    if profile_picture_url:
        current_user.profile_picture_url = profile_picture_url
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="update",
        resource_type="user_profile",
        resource_id=current_user.id,
        description="Updated profile information",
        request=request
    )
    
    return current_user


# ============================================================================
# TOKEN VALIDATION
# ============================================================================

@router.post("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify if current token is valid
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value,
        "tenant_id": current_user.tenant_id
    }

