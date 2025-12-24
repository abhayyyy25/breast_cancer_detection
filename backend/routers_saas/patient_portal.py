"""
Patient Portal Router - Patient Self-Service
Allows patients to view their own medical history and reports
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import os

from database_saas import get_db
from auth_saas import require_patient, create_audit_log
from schemas_saas import PatientResponse, ScanResponse, PatientDashboard, MessageResponse, PatientUpdate
from models_saas import User, Patient, Scan, UserRole


router = APIRouter(prefix="/patient-portal", tags=["Patient Portal"])


# ============================================================================
# PATIENT DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=PatientDashboard)
async def get_patient_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get patient dashboard with overview of scans and health data
    """
    # Get patient profile
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Scan statistics
    total_scans = db.query(Scan).filter(Scan.patient_id == patient.id).count()
    
    # Last scan date
    last_scan = db.query(Scan).filter(
        Scan.patient_id == patient.id
    ).order_by(desc(Scan.scan_date)).first()
    
    last_scan_date = last_scan.scan_date if last_scan else None
    
    # Recent scans
    recent_scans = db.query(Scan).filter(
        Scan.patient_id == patient.id
    ).order_by(desc(Scan.scan_date)).limit(10).all()
    
    # Risk summary based on scan history
    benign_count = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.prediction == "benign"
    ).count()
    
    malignant_count = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.prediction == "malignant"
    ).count()
    
    suspicious_count = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.risk_level.in_(["high", "very_high"])
    ).count()
    
    risk_summary = {
        "total_scans": total_scans,
        "benign_results": benign_count,
        "malignant_results": malignant_count,
        "suspicious_findings": suspicious_count,
        "last_scan_date": last_scan_date.isoformat() if last_scan_date else None,
        "last_scan_result": last_scan.prediction if last_scan else None
    }
    
    return PatientDashboard(
        patient_name=patient.full_name,
        mrn=patient.mrn,
        total_scans=total_scans,
        last_scan_date=last_scan_date,
        recent_scans=recent_scans,
        risk_summary=risk_summary
    )


# ============================================================================
# PATIENT PROFILE
# ============================================================================

@router.get("/profile", response_model=PatientResponse)
async def get_my_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get patient's own profile information
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="patient_profile",
        resource_id=patient.id,
        patient_id=patient.id,
        description="Viewed own profile",
        request=request
    )
    
    return patient


@router.put("/profile", response_model=PatientResponse)
async def update_my_profile(
    profile_update: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Update patient's own profile information
    Only allows updating: phone, address, city, state, emergency contact info
    Email and full_name cannot be changed through this endpoint for security
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Allowed fields for patient self-update (excluding full_name and email for security)
    allowed_fields = [
        'phone', 'address', 'city', 'state', 'postal_code',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation'
    ]
    
    # Update only allowed fields that were provided
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field in allowed_fields and hasattr(patient, field) and value is not None:
            setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="update",
        resource_type="patient_profile",
        resource_id=patient.id,
        patient_id=patient.id,
        description="Updated own profile",
        request=request
    )
    
    return patient


# ============================================================================
# SCAN HISTORY
# ============================================================================

@router.get("/scans", response_model=List[ScanResponse])
async def get_my_scans(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get all scans for the current patient
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    scans = db.query(Scan).filter(
        Scan.patient_id == patient.id
    ).order_by(desc(Scan.scan_date)).offset(skip).limit(limit).all()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="scan_history",
        resource_id=patient.id,
        patient_id=patient.id,
        description="Viewed own scan history",
        request=request
    )
    
    return scans


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_details(
    scan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get details of a specific scan
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.patient_id == patient.id
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found or access denied"
        )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=patient.id,
        scan_id=scan.id,
        description=f"Viewed own scan: {scan.scan_number}",
        request=request
    )
    
    return scan


@router.get("/scans/{scan_id}/download-report")
async def download_my_scan_report(
    scan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Download PDF report for own scan
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.patient_id == patient.id
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found or access denied"
        )
    
    if not scan.report_path or not os.path.exists(scan.report_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not available. Please contact your healthcare provider."
        )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="download",
        resource_type="report",
        resource_id=scan.id,
        patient_id=patient.id,
        scan_id=scan.id,
        description=f"Downloaded own report: {scan.scan_number}",
        request=request
    )
    
    return FileResponse(
        path=scan.report_path,
        filename=f"Medical_Report_{scan.scan_number}.pdf",
        media_type="application/pdf"
    )


# ============================================================================
# SCAN IMAGES (View Only - No Download of Raw Images for Privacy)
# ============================================================================

@router.get("/scans/{scan_id}/image")
async def view_scan_image(
    scan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    View scan image (returns base64 encoded image for display in browser)
    """
    import base64
    
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.patient_id == patient.id
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found or access denied"
        )
    
    if not os.path.exists(scan.image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    # Read and encode image
    with open(scan.image_path, "rb") as img_file:
        image_data = base64.b64encode(img_file.read()).decode()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="scan_image",
        resource_id=scan.id,
        patient_id=patient.id,
        scan_id=scan.id,
        description=f"Viewed scan image: {scan.scan_number}",
        request=request
    )
    
    return {
        "scan_id": scan.id,
        "scan_number": scan.scan_number,
        "image_format": scan.image_format,
        "image_data": image_data
    }


# ============================================================================
# HEALTH STATISTICS
# ============================================================================

@router.get("/statistics")
async def get_my_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get statistical summary of patient's scan history
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Total scans
    total_scans = db.query(Scan).filter(Scan.patient_id == patient.id).count()
    
    # Prediction breakdown
    benign_count = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.prediction == "benign"
    ).count()
    
    malignant_count = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.prediction == "malignant"
    ).count()
    
    # Risk level breakdown
    low_risk = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.risk_level == "low"
    ).count()
    
    moderate_risk = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.risk_level == "moderate"
    ).count()
    
    high_risk = db.query(Scan).filter(
        Scan.patient_id == patient.id,
        Scan.risk_level.in_(["high", "very_high"])
    ).count()
    
    # Average confidence score
    from sqlalchemy import func
    avg_confidence = db.query(func.avg(Scan.confidence_score)).filter(
        Scan.patient_id == patient.id,
        Scan.confidence_score.isnot(None)
    ).scalar()
    
    # First and last scan dates
    first_scan = db.query(Scan).filter(
        Scan.patient_id == patient.id
    ).order_by(Scan.scan_date.asc()).first()
    
    last_scan = db.query(Scan).filter(
        Scan.patient_id == patient.id
    ).order_by(Scan.scan_date.desc()).first()
    
    return {
        "patient_name": patient.full_name,
        "mrn": patient.mrn,
        "total_scans": total_scans,
        "prediction_breakdown": {
            "benign": benign_count,
            "malignant": malignant_count
        },
        "risk_breakdown": {
            "low": low_risk,
            "moderate": moderate_risk,
            "high": high_risk
        },
        "average_confidence_score": round(avg_confidence, 2) if avg_confidence else None,
        "first_scan_date": first_scan.scan_date if first_scan else None,
        "last_scan_date": last_scan.scan_date if last_scan else None,
        "days_since_last_scan": (datetime.utcnow() - last_scan.scan_date).days if last_scan else None
    }

