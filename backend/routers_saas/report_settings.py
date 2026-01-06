"""
Report Settings Router
Allows doctors to customize PDF report branding and default information
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime

from database_saas import get_db
from models_saas import ReportSettings, User, UserRole
from schemas_saas import ReportSettingsCreate, ReportSettingsResponse, MessageResponse
from auth_saas import get_current_user


router = APIRouter(tags=["Report Settings"])


# ============================================================================
# GET REPORT SETTINGS
# ============================================================================

@router.get("/report-settings", response_model=ReportSettingsResponse)
async def get_report_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's report customization settings
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH]:
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
            license_number=current_user.license_number,
            report_header_color="#2563EB"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


# ============================================================================
# UPDATE REPORT SETTINGS
# ============================================================================

@router.put("/report-settings", response_model=ReportSettingsResponse)
async def update_report_settings(
    settings_data: ReportSettingsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update report customization settings
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH]:
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
# UPLOAD LOGO
# ============================================================================

@router.post("/report-settings/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload hospital/clinic logo for PDF reports
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only medical staff can upload logos"
        )
    
    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 5MB)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    logos_dir = os.path.join(upload_dir, "logos")
    os.makedirs(logos_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logo_{current_user.id}_{timestamp}{file_ext}"
    file_path = os.path.join(logos_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Update settings with logo URL
    settings = db.query(ReportSettings).filter(
        ReportSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = ReportSettings(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        db.add(settings)
    
    # Store relative path
    settings.hospital_logo_url = f"/uploads/logos/{filename}"
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Logo uploaded successfully",
        "logo_url": settings.hospital_logo_url,
        "filename": filename
    }


# ============================================================================
# UPLOAD SIGNATURE
# ============================================================================

@router.post("/report-settings/upload-signature")
async def upload_signature(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload doctor's signature for PDF reports
    Only for doctors
    """
    # Check if user is a doctor
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can upload signatures"
        )
    
    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 2MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 2MB limit"
        )
    
    # Create uploads directory
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    signatures_dir = os.path.join(upload_dir, "signatures")
    os.makedirs(signatures_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"signature_{current_user.id}_{timestamp}{file_ext}"
    file_path = os.path.join(signatures_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Update settings
    settings = db.query(ReportSettings).filter(
        ReportSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = ReportSettings(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        db.add(settings)
    
    settings.signature_url = f"/uploads/signatures/{filename}"
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Signature uploaded successfully",
        "signature_url": settings.signature_url,
        "filename": filename
    }


# ============================================================================
# DELETE REPORT SETTINGS
# ============================================================================

@router.delete("/report-settings", response_model=MessageResponse)
async def reset_report_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset report settings to default
    Only for doctors and lab techs
    """
    # Check if user is medical staff
    if current_user.role not in [UserRole.DOCTOR, UserRole.LAB_TECH]:
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
