"""
Hospital/Lab Admin Router - Organization Management
Manages users (doctors, lab techs, patients) within their organization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import EmailStr

from database_saas import get_db
from auth_saas import (
    require_org_admin, get_user_tenant_id, verify_tenant_access,
    create_audit_log, create_user_with_credentials
)
from schemas_saas import (
    UserCreate, UserCreateResponse, UserUpdate, UserResponse,
    PatientCreate, PatientResponse, PatientSearchResponse,
    ScanResponse, HospitalAdminDashboard, MessageResponse
)
from models_saas import User, Patient, Scan, Tenant, UserRole, ScanStatus


router = APIRouter(prefix="/hospital-admin", tags=["Hospital Admin"])


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=HospitalAdminDashboard)
async def get_hospital_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get comprehensive statistics for Hospital Admin dashboard
    """
    tenant = await verify_tenant_access(tenant_id, current_user, db)
    
    # User statistics
    total_doctors = db.query(func.count(User.id)).filter(
        and_(
            User.tenant_id == tenant_id,
            User.role == UserRole.DOCTOR
        )
    ).scalar()
    
    total_lab_techs = db.query(func.count(User.id)).filter(
        and_(
            User.tenant_id == tenant_id,
            User.role == UserRole.LAB_TECH
        )
    ).scalar()
    
    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.tenant_id == tenant_id
    ).scalar()
    
    # Scan statistics
    total_scans = db.query(func.count(Scan.id)).filter(
        Scan.tenant_id == tenant_id
    ).scalar()
    
    # Today's scans
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= today_start
        )
    ).scalar()
    
    # This week's scans
    week_start = datetime.utcnow() - timedelta(days=7)
    scans_this_week = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= week_start
        )
    ).scalar()
    
    # This month's scans
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= first_day_of_month
        )
    ).scalar()
    
    # Calculate scan limit usage
    scan_limit_usage_percentage = (scans_this_month / tenant.monthly_scan_limit * 100) if tenant.monthly_scan_limit > 0 else 0
    
    # Recent scans
    recent_scans = db.query(Scan).filter(
        Scan.tenant_id == tenant_id
    ).order_by(Scan.created_at.desc()).limit(10).all()
    
    # Active users
    active_users = db.query(User).filter(
        and_(
            User.tenant_id == tenant_id,
            User.is_active == True,
            User.role.in_([UserRole.DOCTOR, UserRole.LAB_TECH])
        )
    ).order_by(User.last_login.desc()).limit(10).all()
    
    return HospitalAdminDashboard(
        tenant_name=tenant.name,
        total_doctors=total_doctors,
        total_lab_techs=total_lab_techs,
        total_patients=total_patients,
        total_scans=total_scans,
        scans_today=scans_today,
        scans_this_week=scans_this_week,
        scans_this_month=scans_this_month,
        monthly_scan_limit=tenant.monthly_scan_limit,
        scan_limit_usage_percentage=scan_limit_usage_percentage,
        recent_scans=recent_scans,
        active_users=active_users
    )


# ============================================================================
# STAFF MANAGEMENT (Doctors & Lab Techs ONLY)
# ============================================================================

@router.post("/staff", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_member(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Admin-only endpoint: Create a new STAFF member (Doctor or Lab Tech)
    Requires manual username and password
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    # Organization admins can ONLY create Doctors and Lab Techs (NOT Patients, NOT other Admins)
    if user_data.role not in [UserRole.DOCTOR, UserRole.LAB_TECH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only create Doctor and Lab Tech staff. Use the doctor endpoint to register patients."
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different username."
        )
    
    # Create user with manual credentials
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        tenant_id=tenant_id,
        phone=user_data.phone,
        gender=user_data.gender,
        date_of_birth=user_data.date_of_birth,
        license_number=user_data.license_number,
        department=user_data.department,
        specialization=user_data.specialization,
        is_active=True,
        is_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="create",
        resource_type="user",
        resource_id=user.id,
        description=f"Created new {user_data.role.value}: {user_data.full_name}",
        request=request
    )
    
    return UserCreateResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id,
        message="User created successfully."
    )


@router.get("/users", response_model=List[UserResponse])
async def list_organization_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    List all users in the organization
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    query = db.query(User).filter(User.tenant_id == tenant_id)
    
    if role:
        query = query.filter(User.role == role)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get detailed information about a user
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.tenant_id == tenant_id
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Update user information
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.tenant_id == tenant_id
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="update",
        resource_type="user",
        resource_id=user.id,
        description=f"Updated user: {user.full_name}",
        request=request
    )
    
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Deactivate a user (soft delete)
    DEPRECATED: Use PUT /users/{user_id}/status instead
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.tenant_id == tenant_id
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="deactivate",
        resource_type="user",
        resource_id=user.id,
        description=f"Deactivated user: {user.full_name}",
        request=request
    )
    
    return MessageResponse(
        message=f"User '{user.full_name}' deactivated successfully",
        success=True
    )


@router.put("/users/{user_id}/status", response_model=MessageResponse)
async def toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Toggle user status between active and inactive
    Allows both deactivation and reactivation of users
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    user = db.query(User).filter(
        and_(
            User.id == user_id,
            User.tenant_id == tenant_id
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Toggle the status
    new_status = not user.is_active
    user.is_active = new_status
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Audit log
    action = "activate" if new_status else "deactivate"
    await create_audit_log(
        db=db,
        user=current_user,
        action=action,
        resource_type="user",
        resource_id=user.id,
        description=f"{'Activated' if new_status else 'Deactivated'} user: {user.full_name}",
        request=request
    )
    
    return MessageResponse(
        message=f"User '{user.full_name}' {'activated' if new_status else 'deactivated'} successfully",
        success=True
    )


# ============================================================================
# PATIENT MANAGEMENT
# ============================================================================

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Register a new patient
    Creates both Patient record and associated User account
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == patient_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate MRN (Medical Record Number)
    # Format: TXXX-YYYYMMDD-NNNN (Tenant ID, Date, Sequential Number)
    today = datetime.utcnow().strftime("%Y%m%d")
    patient_count = db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar()
    mrn = f"T{tenant_id:03d}-{today}-{(patient_count + 1):04d}"
    
    # Create patient user account
    patient_user, plain_password = create_user_with_credentials(
        db=db,
        email=patient_data.email,
        full_name=patient_data.full_name,
        role=UserRole.PATIENT,
        tenant_id=tenant_id,
        phone=patient_data.phone,
        gender=patient_data.gender,
        date_of_birth=patient_data.date_of_birth,
        created_by_user_id=current_user.id
    )
    
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
        description=f"Registered new patient: {patient.full_name} (MRN: {patient.mrn})",
        request=request
    )
    
    # Note: In production, you might want to send credentials via email
    # For now, they'll need to communicate this to the patient securely
    
    return patient


@router.get("/patients", response_model=List[PatientSearchResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    List all patients in the organization with optional search
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    query = db.query(Patient).filter(Patient.tenant_id == tenant_id)
    
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
async def get_patient_details(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get detailed patient information
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    patient = db.query(Patient).filter(
        and_(
            Patient.id == patient_id,
            Patient.tenant_id == tenant_id
        )
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Audit log - patient data access
    await create_audit_log(
        db=db,
        user=current_user,
        action="view",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        description=f"Viewed patient details: {patient.full_name}",
        request=request
    )
    
    return patient


# ============================================================================
# SCAN OVERVIEW
# ============================================================================

@router.get("/scans/recent", response_model=List[ScanResponse])
async def get_recent_scans(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get recent scans performed in the organization
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    scans = db.query(Scan).filter(
        Scan.tenant_id == tenant_id
    ).order_by(Scan.created_at.desc()).limit(limit).all()
    
    return scans


@router.get("/scans/statistics")
async def get_scan_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    tenant_id: int = Depends(get_user_tenant_id)
):
    """
    Get scan statistics (distribution by prediction, status, etc.)
    """
    await verify_tenant_access(tenant_id, current_user, db)
    
    # Prediction distribution
    benign_count = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.prediction == "benign"
        )
    ).scalar()
    
    malignant_count = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.prediction == "malignant"
        )
    ).scalar()
    
    # Status distribution
    pending_count = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.status == ScanStatus.PENDING
        )
    ).scalar()
    
    completed_count = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.status == ScanStatus.COMPLETED
        )
    ).scalar()
    
    return {
        "prediction_distribution": {
            "benign": benign_count,
            "malignant": malignant_count
        },
        "status_distribution": {
            "pending": pending_count,
            "completed": completed_count
        }
    }

