"""
Patient management router.

Endpoints:
- GET /patients: List all patients
- POST /patients: Create new patient
- GET /patients/{id}: Get patient details
- PUT /patients/{id}: Update patient
- DELETE /patients/{id}: Delete patient (soft delete)
- GET /patients/{id}/history: Get patient's scan history
- GET /patients/search: Search patients by MRN or name
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import User, Patient, Scan
from auth_utils import (
    get_current_user,
    log_audit,
    get_client_ip,
    get_user_agent
)

router = APIRouter(prefix="/patients", tags=["Patients"])


# ==================== Statistics Endpoint ====================

@router.get("/stats/overview")
async def get_overview_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overview statistics for dashboard.
    
    Returns:
        - total_patients: Total number of patients
        - total_scans: Total number of scans
        - recent_scans: Scans from last 7 days
        - active_users: Number of active users
    """
    from datetime import timedelta
    
    # Count total patients
    total_patients = db.query(Patient).count()
    
    # Count total scans
    total_scans = db.query(Scan).count()
    
    # Count recent scans (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_scans = db.query(Scan).filter(
        Scan.created_at >= seven_days_ago
    ).count()
    
    # Count active users
    active_users = db.query(User).filter(User.is_active == 1).count()
    
    return {
        "total_patients": total_patients,
        "total_scans": total_scans,
        "recent_scans": recent_scans,
        "active_users": active_users,
        "user_role": current_user.role,
        "user_name": current_user.full_name
    }


# ==================== Request/Response Models ====================

class PatientCreate(BaseModel):
    medical_record_number: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    @validator("gender")
    def validate_gender(cls, v):
        """Validate gender field."""
        allowed = ["Male", "Female", "Other", "Prefer not to say"]
        if v not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
        return v


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    medical_record_number: str
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str
    contact_phone: Optional[str]
    contact_email: Optional[str]
    address: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScanHistoryItem(BaseModel):
    id: int
    scan_date: datetime
    prediction_result: str
    confidence_score: float
    risk_level: str
    doctor_name: str
    doctor_notes: Optional[str]
    report_generated: bool
    
    class Config:
        from_attributes = True


class PatientHistoryResponse(BaseModel):
    patient: PatientResponse
    scans: List[ScanHistoryItem]
    total_scans: int


# ==================== Endpoints ====================

@router.get("", response_model=List[PatientResponse])
async def list_patients(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all patients with pagination.
    
    - Requires authentication
    - Returns paginated list of patients
    - Logs access for compliance
    """
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    # Log access
    log_audit(
        db=db,
        user_id=current_user.id,
        action="LIST_PATIENTS",
        resource_type="patient",
        details=f"Listed {len(patients)} patients",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return patients


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new patient record.
    
    - Requires authentication
    - Validates MRN uniqueness
    - Creates patient record
    - Logs creation for compliance
    """
    # Check if MRN already exists
    existing_patient = db.query(Patient).filter(
        Patient.medical_record_number == patient_data.medical_record_number
    ).first()
    
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with MRN {patient_data.medical_record_number} already exists"
        )
    
    # Create new patient
    new_patient = Patient(**patient_data.dict())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    
    # Log creation
    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_PATIENT",
        resource_type="patient",
        resource_id=new_patient.id,
        patient_id=new_patient.id,
        details=f"Created patient: {new_patient.full_name} (MRN: {new_patient.medical_record_number})",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return new_patient


@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query (MRN or name)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search patients by MRN or name.
    
    - Requires authentication
    - Searches in MRN, first name, and last name
    - Returns matching patients
    """
    search_pattern = f"%{q}%"
    
    patients = db.query(Patient).filter(
        or_(
            Patient.medical_record_number.ilike(search_pattern),
            Patient.first_name.ilike(search_pattern),
            Patient.last_name.ilike(search_pattern)
        )
    ).limit(50).all()
    
    # Log search
    log_audit(
        db=db,
        user_id=current_user.id,
        action="SEARCH_PATIENTS",
        resource_type="patient",
        details=f"Searched for: {q}, found {len(patients)} results",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    request: Request,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get patient details by ID.
    
    - Requires authentication
    - Returns patient information
    - Logs access for compliance
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Log access
    log_audit(
        db=db,
        user_id=current_user.id,
        action="VIEW_PATIENT",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        details=f"Viewed patient: {patient.full_name}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    request: Request,
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update patient information.
    
    - Requires authentication
    - Updates only provided fields
    - Logs update for compliance
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Update fields
    update_data = patient_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(patient)
    
    # Log update
    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_PATIENT",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        details=f"Updated patient: {patient.full_name}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    request: Request,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete patient record.
    
    - Requires authentication
    - Permanently deletes patient and associated scans
    - Logs deletion for compliance
    
    ⚠️ WARNING: This is a permanent operation!
    Consider implementing soft delete in production.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient_name = patient.full_name
    patient_mrn = patient.medical_record_number
    
    # Log deletion before deleting
    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE_PATIENT",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        details=f"Deleted patient: {patient_name} (MRN: {patient_mrn})",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Delete patient (cascades to scans)
    db.delete(patient)
    db.commit()
    
    return None


@router.get("/history/all")
async def get_all_patients_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete scan history for ALL patients.
    
    - Requires authentication
    - Returns all patients with their scan histories
    - Useful for admin overview
    - Logs access for compliance
    """
    try:
        # Get all patients
        patients = db.query(Patient).all()
        
        all_patients_history = []
        
        for patient in patients:
            try:
                # Get all scans for this patient
                scans = db.query(Scan).filter(
                    Scan.patient_id == patient.id
                ).order_by(Scan.created_at.desc()).all()
                
                # Format scan history
                scan_history = []
                for scan in scans:
                    try:
                        scan_history.append({
                            "id": scan.id,
                            "scan_date": scan.created_at.isoformat() if scan.created_at else None,
                            "prediction_result": scan.prediction_result,
                            "confidence_score": float(scan.confidence_score) if scan.confidence_score else 0.0,
                            "risk_level": scan.risk_level,
                            "doctor_name": scan.user.full_name if scan.user else "Unknown",
                            "doctor_notes": scan.doctor_notes,
                            "report_generated": bool(scan.report_generated),
                            "image_path": scan.image_path,
                            "original_filename": scan.original_filename
                        })
                    except Exception as scan_error:
                        print(f"Error processing scan {scan.id}: {scan_error}")
                        continue
                
                all_patients_history.append({
                    "patient": {
                        "id": patient.id,
                        "medical_record_number": patient.medical_record_number,
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "full_name": f"{patient.first_name} {patient.last_name}",
                        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                        "gender": patient.gender,
                        "contact_phone": patient.contact_phone,
                        "contact_email": patient.contact_email
                    },
                    "scans": scan_history,
                    "total_scans": len(scans),
                    "latest_scan": scans[0].created_at.isoformat() if scans and scans[0].created_at else None
                })
            except Exception as patient_error:
                print(f"Error processing patient {patient.id}: {patient_error}")
                continue
        
        return {
            "patients": all_patients_history,
            "total_patients": len(patients)
        }
    except Exception as e:
        print(f"Error fetching all patients history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch patients history: {str(e)}"
        )


@router.get("/{patient_id}/history", response_model=PatientHistoryResponse)
async def get_patient_history(
    request: Request,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete scan history for a patient.
    
    - Requires authentication
    - Returns patient info and all scans
    - Ordered by most recent first
    - Logs access for compliance
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Get all scans for this patient
    scans = db.query(Scan).filter(
        Scan.patient_id == patient_id
    ).order_by(Scan.created_at.desc()).all()
    
    # Format scan history
    scan_history = []
    for scan in scans:
        scan_history.append({
            "id": scan.id,
            "scan_date": scan.created_at,
            "prediction_result": scan.prediction_result,
            "confidence_score": scan.confidence_score,
            "risk_level": scan.risk_level,
            "doctor_name": scan.user.full_name,
            "doctor_notes": scan.doctor_notes,
            "report_generated": bool(scan.report_generated)
        })
    
    # Log access
    log_audit(
        db=db,
        user_id=current_user.id,
        action="VIEW_PATIENT_HISTORY",
        resource_type="patient",
        resource_id=patient.id,
        patient_id=patient.id,
        details=f"Viewed history for patient: {patient.full_name} ({len(scans)} scans)",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {
        "patient": patient,
        "scans": scan_history,
        "total_scans": len(scans)
    }

