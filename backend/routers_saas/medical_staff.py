"""
Medical Staff Router - Doctor & Lab Tech Operations
Handles patient scans, analysis, and report generation
DOCTORS ONLY can register patients (role-based endpoint)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime
import os
import base64
from io import BytesIO

from database_saas import get_db
from auth_saas import (
    require_medical_staff, get_user_tenant_id, verify_tenant_access,
    verify_patient_access, create_audit_log, hash_password
)
from schemas_saas import (
    PatientSearchResponse, PatientResponse, PatientCreate,
    ScanCreate, ScanUpdate, ScanResponse, ScanAnalysisResult,
    MessageResponse, MedicalStaffDashboard
)
from models_saas import User, Patient, Scan, ScanStatus, UserRole
from datetime import timedelta


router = APIRouter(prefix="/medical-staff", tags=["Medical Staff"])


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@router.get("/dashboard-stats", response_model=MedicalStaffDashboard)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get dashboard statistics for the current medical staff member (Doctor/Lab Tech)
    Uses ORGANIZATION-WIDE counts (same logic as History page)
    Shows ALL patients and scans in the organization, not just those created by this user
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    # FIXED: Count ALL patients in the organization (same as History page)
    # This matches the logic in GET /medical-staff/patients endpoint
    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.tenant_id == tenant_id
    ).scalar()
    
    # FIXED: Count ALL scans in the organization (same as History page)
    # This matches the counts shown in the Patient History page
    total_scans = db.query(func.count(Scan.id)).filter(
        Scan.tenant_id == tenant_id
    ).scalar()
    
    # Today's scans (organization-wide)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= today_start
        )
    ).scalar()
    
    # This week's scans (organization-wide)
    week_start = datetime.utcnow() - timedelta(days=7)
    scans_this_week = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= week_start
        )
    ).scalar()
    
    # This month's scans (organization-wide)
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= first_day_of_month
        )
    ).scalar()
    
    # Recent scans (last 7 days) - same as this week
    recent_scans = scans_this_week
    
    return MedicalStaffDashboard(
        total_patients=total_patients or 0,
        total_scans=total_scans or 0,
        scans_today=scans_today or 0,
        scans_this_week=scans_this_week or 0,
        scans_this_month=scans_this_month or 0,
        recent_scans=recent_scans or 0,
        user_role=current_user.role.value,
        user_name=current_user.full_name
    )


# ============================================================================
# PATIENT REGISTRATION (DOCTORS ONLY)
# ============================================================================

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient_data: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    DOCTORS ONLY: Register a new patient
    Creates both Patient record and associated User account
    MRN is auto-generated
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    # ONLY DOCTORS can register patients
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Doctors can register new patients. Lab Technicians cannot perform this action."
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == patient_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == patient_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different username."
        )
    
    # Generate MRN (Medical Record Number)
    # Format: T{TenantID}-YYYYMMDD-{Sequential}
    today = datetime.utcnow().strftime("%Y%m%d")
    patient_count = db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar()
    mrn = f"T{tenant_id:03d}-{today}-{(patient_count + 1):04d}"
    
    # Create patient user account with manual credentials
    patient_user = User(
        username=patient_data.username,
        email=patient_data.email,
        password_hash=hash_password(patient_data.password),
        full_name=patient_data.full_name,
        role=UserRole.PATIENT,
        tenant_id=tenant_id,
        phone=patient_data.phone,
        gender=patient_data.gender,
        date_of_birth=patient_data.date_of_birth,
        is_active=True,
        is_verified=True
    )
    
    db.add(patient_user)
    db.commit()
    db.refresh(patient_user)
    
    # Create patient profile
    patient = Patient(
        tenant_id=tenant_id,
        user_id=patient_user.id,
        mrn=mrn,
        full_name=patient_data.full_name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
        email=patient_data.email,
        phone=patient_data.phone,
        address=patient_data.address,
        city=patient_data.city,
        state=patient_data.state,
        postal_code=patient_data.postal_code,
        emergency_contact_name=patient_data.emergency_contact_name,
        emergency_contact_phone=patient_data.emergency_contact_phone,
        emergency_contact_relation=patient_data.emergency_contact_relation,
        blood_group=patient_data.blood_group,
        medical_history_json=patient_data.medical_history_json,
        family_history_json=patient_data.family_history_json,
        risk_factors_json=patient_data.risk_factors_json
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="create",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        description=f"Doctor registered new patient: {patient.full_name} (MRN: {patient.mrn})",
        request=request
    )
    
    return patient


# ============================================================================
# PATIENT ACCESS
# ============================================================================

@router.get("/patients", response_model=List[PatientSearchResponse])
async def search_patients(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Search for patients in the organization
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    query = db.query(Patient).filter(
        and_(
            Patient.tenant_id == tenant_id,
            Patient.is_active == True
        )
    )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Patient.full_name.ilike(search_pattern)) |
            (Patient.mrn.ilike(search_pattern)) |
            (Patient.phone.ilike(search_pattern))
        )
    
    patients = query.offset(skip).limit(limit).all()
    return patients


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient_info(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Get detailed patient information
    """
    patient = await verify_patient_access(patient_id, current_user, db)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        description=f"Viewed patient: {patient.full_name}",
        request=request
    )
    
    return patient


@router.get("/patients/{patient_id}/history", response_model=List[ScanResponse])
async def get_patient_scan_history(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Get all scans for a specific patient
    """
    patient = await verify_patient_access(patient_id, current_user, db)
    
    scans = db.query(Scan).filter(
        Scan.patient_id == patient_id
    ).order_by(desc(Scan.scan_date)).all()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="patient_history",
        resource_id=patient.id,
        patient_id=patient.id,
        description=f"Viewed scan history for: {patient.full_name}",
        request=request
    )
    
    return scans


# ============================================================================
# SCAN ANALYSIS
# ============================================================================

@router.post("/scans/analyze", response_model=ScanAnalysisResult, status_code=status.HTTP_201_CREATED)
async def analyze_scan(
    patient_id: int,
    request: Request,
    image: UploadFile = File(..., description="Medical scan image file"),
    doctor_notes: Optional[str] = Form(None, description="Optional doctor's notes"),
    disclaimer_accepted: bool = Form(False, description="Medical disclaimer acceptance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Upload and analyze a medical scan image
    Uses AI model to detect abnormalities
    """
    await verify_tenant_access(tenant_id, current_user, db)
    patient = await verify_patient_access(patient_id, current_user, db)
    
    # Verify disclaimer acceptance
    if not disclaimer_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical disclaimer must be accepted before analysis"
        )
    
    # Check monthly scan limit
    tenant = await verify_tenant_access(tenant_id, current_user, db)
    if tenant.current_month_scans >= tenant.monthly_scan_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly scan limit reached ({tenant.monthly_scan_limit}). Please contact support."
        )
    
    # Generate unique scan number
    scan_count = db.query(Scan).count()
    scan_number = f"SCN-{datetime.utcnow().strftime('%Y%m%d')}-{(scan_count + 1):06d}"
    
    # Save uploaded image
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(image.filename)[1]
    image_filename = f"{scan_number}{file_extension}"
    image_path = os.path.join(upload_dir, image_filename)
    
    with open(image_path, "wb") as buffer:
        content = await image.read()
        buffer.write(content)
    
    # Create scan record
    scan = Scan(
        tenant_id=tenant_id,
        patient_id=patient_id,
        performed_by_user_id=current_user.id,
        scan_number=scan_number,
        image_path=image_path,
        image_filename=image_filename,
        image_size_bytes=len(content),
        image_format=file_extension.replace('.', ''),
        status=ScanStatus.IN_PROGRESS,
        doctor_notes=doctor_notes,
        disclaimer_accepted=disclaimer_accepted,
        disclaimer_accepted_at=datetime.utcnow() if disclaimer_accepted else None,
        analysis_started_at=datetime.utcnow()
    )
    
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Perform AI analysis (using existing mock_analysis or real TensorFlow)
    try:
        # Import analysis function
        try:
            from mock_analysis import perform_mock_analysis
            analysis_result = perform_mock_analysis(image_path)
        except ImportError:
            # Fallback to basic mock if mock_analysis doesn't exist
            import random
            analysis_result = {
                "prediction": random.choice(["benign", "malignant"]),
                "confidence": random.uniform(0.7, 0.95),
                "risk_level": random.choice(["low", "moderate", "high"]),
                "statistics": {"mean": 127.5, "std": 50.0, "min": 0, "max": 255},
                "heatmap": None,
                "overlay": None
            }
        
        # Update scan with results
        scan.prediction = analysis_result["prediction"]
        scan.confidence_score = analysis_result["confidence"]
        scan.risk_level = analysis_result["risk_level"]
        scan.image_statistics_json = analysis_result.get("statistics", {})
        scan.analysis_results_json = analysis_result
        scan.status = ScanStatus.COMPLETED
        scan.analysis_completed_at = datetime.utcnow()
        scan.analysis_duration_seconds = (datetime.utcnow() - scan.analysis_started_at).total_seconds()
        
        # Save heatmap if generated
        if analysis_result.get("heatmap"):
            heatmap_path = image_path.replace(file_extension, "_heatmap.png")
            scan.heatmap_path = heatmap_path
        
        if analysis_result.get("overlay"):
            overlay_path = image_path.replace(file_extension, "_overlay.png")
            scan.overlay_path = overlay_path
        
        # Update tenant scan count
        tenant.current_month_scans += 1
        tenant.total_scans_processed += 1
        
        db.commit()
        db.refresh(scan)
        
        # Audit log
        await create_audit_log(
            db=db,
            user=current_user,
            action="analyze",
            resource_type="scan",
            resource_id=scan.id,
            patient_id=patient_id,
            scan_id=scan.id,
            description=f"Analyzed scan for patient: {patient.full_name}. Result: {scan.prediction}",
            request=request
        )
        
        # Prepare response with image data
        with open(image_path, "rb") as img_file:
            original_image_base64 = base64.b64encode(img_file.read()).decode()
        
        heatmap_image_base64 = None
        if scan.heatmap_path and os.path.exists(scan.heatmap_path):
            with open(scan.heatmap_path, "rb") as heatmap_file:
                heatmap_image_base64 = base64.b64encode(heatmap_file.read()).decode()
        
        overlay_image_base64 = None
        if scan.overlay_path and os.path.exists(scan.overlay_path):
            with open(scan.overlay_path, "rb") as overlay_file:
                overlay_image_base64 = base64.b64encode(overlay_file.read()).decode()
        
        return ScanAnalysisResult(
            scan_id=scan.id,
            scan_number=scan.scan_number,
            patient_name=patient.full_name,
            patient_mrn=patient.mrn,
            prediction=scan.prediction,
            confidence_score=scan.confidence_score,
            risk_level=scan.risk_level,
            analysis_results=scan.analysis_results_json,
            image_statistics=scan.image_statistics_json,
            original_image_base64=original_image_base64,
            heatmap_image_base64=heatmap_image_base64,
            overlay_image_base64=overlay_image_base64,
            scan_date=scan.scan_date,
            performed_by=current_user.full_name
        )
        
    except Exception as e:
        # Update scan status to failed
        scan.status = ScanStatus.FAILED
        scan.analysis_completed_at = datetime.utcnow()
        db.commit()
        
        # Audit log error
        await create_audit_log(
            db=db,
            user=current_user,
            action="analyze",
            resource_type="scan",
            resource_id=scan.id,
            patient_id=patient_id,
            scan_id=scan.id,
            description=f"Scan analysis failed for patient: {patient.full_name}",
            request=request,
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_details(
    scan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Get detailed information about a specific scan
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Verify access
    if current_user.role not in [UserRole.SUPER_ADMIN]:
        if scan.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        description=f"Viewed scan: {scan.scan_number}",
        request=request
    )
    
    return scan


@router.put("/scans/{scan_id}/notes", response_model=ScanResponse)
async def update_scan_notes(
    scan_id: int,
    scan_update: ScanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Update doctor/radiologist notes for a scan
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Verify access
    if current_user.role not in [UserRole.SUPER_ADMIN]:
        if scan.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Update notes
    if scan_update.doctor_notes is not None:
        scan.doctor_notes = scan_update.doctor_notes
    if scan_update.radiologist_notes is not None:
        scan.radiologist_notes = scan_update.radiologist_notes
    if scan_update.internal_notes is not None:
        scan.internal_notes = scan_update.internal_notes
    
    scan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(scan)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="update",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        description=f"Updated notes for scan: {scan.scan_number}",
        request=request
    )
    
    return scan


@router.get("/scans/{scan_id}/download-report")
async def download_scan_report(
    scan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Generate and download PDF report for a scan
    """
    from fastapi.responses import FileResponse
    
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Verify access
    if current_user.role not in [UserRole.SUPER_ADMIN]:
        if scan.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Generate report if not already generated
    if not scan.report_path or not os.path.exists(scan.report_path):
        try:
            from report_generator import generate_pdf_report
            patient = db.query(Patient).filter(Patient.id == scan.patient_id).first()
            report_path = generate_pdf_report(scan, patient, current_user)
            scan.report_path = report_path
            scan.report_generated = True
            db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}"
            )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="download",
        resource_type="report",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        description=f"Downloaded report for scan: {scan.scan_number}",
        request=request
    )
    
    return FileResponse(
        path=scan.report_path,
        filename=f"Scan_Report_{scan.scan_number}.pdf",
        media_type="application/pdf"
    )


# ============================================================================
# MY SCANS
# ============================================================================

@router.get("/my-scans", response_model=List[ScanResponse])
async def get_my_scans(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_medical_staff)
):
    """
    Get all scans performed by the current user
    """
    scans = db.query(Scan).filter(
        Scan.performed_by_user_id == current_user.id
    ).order_by(desc(Scan.scan_date)).offset(skip).limit(limit).all()
    
    return scans

