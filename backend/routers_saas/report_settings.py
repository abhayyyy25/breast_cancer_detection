"""
Report Settings Router
Allows doctors to customize PDF report branding and default information
Supports base64 logo storage for cross-device persistence
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database_saas import get_db
from models_saas import ReportSettings, User, UserRole
from schemas_saas import ReportSettingsCreate, ReportSettingsResponse, MessageResponse
from auth_saas import get_current_user


router = APIRouter(tags=["Report Settings"])


# ============================================================================
# GET REPORT SETTINGS
# ============================================================================

@router.get("/settings", response_model=ReportSettingsResponse)
async def get_report_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's report customization settings
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only medical staff can access report settings"
        )
    
    # Get or create settings
    settings = db.query(ReportSettings).filter(
        ReportSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        # Create default settings
        settings = ReportSettings(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            display_name=current_user.full_name,
            doctor_name=current_user.full_name,
            license_number=current_user.license_number,
            report_header_color="#2563EB"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


# ============================================================================
# CREATE/UPDATE REPORT SETTINGS
# ============================================================================

@router.post("/settings", response_model=ReportSettingsResponse)
async def save_report_settings(
    settings_data: ReportSettingsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update report customization settings
    Only for doctors and lab techs
    Supports base64 logo storage
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only medical staff can update report settings"
        )
    
    # Get or create settings
    settings = db.query(ReportSettings).filter(
        ReportSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = ReportSettings(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        db.add(settings)
    
    # Update fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(settings)
    
    return settings


# ============================================================================
# DELETE REPORT SETTINGS
# ============================================================================

@router.delete("/settings", response_model=MessageResponse)
async def reset_report_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset report settings to default
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only medical staff can reset report settings"
        )
    
    settings = db.query(ReportSettings).filter(
        ReportSettings.user_id == current_user.id
    ).first()
    
    if settings:
        db.delete(settings)
        db.commit()
    
    return MessageResponse(
        message="Report settings reset to default",
        success=True
    )
