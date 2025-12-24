"""
Scan management router - handles medical image analysis and scan records.

Endpoints:
- POST /scans/analyze: Analyze image and create scan record
- GET /scans/{id}: Get scan details
- PUT /scans/{id}/notes: Update doctor's notes
- GET /scans/{id}/download-report: Download PDF report
- DELETE /scans/{id}: Delete scan record
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import io
import os
from pathlib import Path
from PIL import Image
import json

from database import get_db
from models import User, Patient, Scan
from auth_utils import (
    get_current_user,
    get_current_active_doctor,
    log_audit,
    get_client_ip,
    get_user_agent
)

# Import analysis functions - avoid circular import
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Import analysis modules
try:
    from grad_cam import create_gradcam_visualization
    from report_generator import generate_report_pdf
    import numpy as np
    from PIL import Image as PILImage
    TENSORFLOW_AVAILABLE = True
    ANALYSIS_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    ANALYSIS_AVAILABLE = False

# Always import mock analysis as fallback
from mock_analysis import run_mock_analysis, DEMO_MODE, DEMO_MESSAGE

router = APIRouter(prefix="/scans", tags=["Scans"])


# Storage directory for uploaded images
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    patient_id: int
    doctor_notes: Optional[str] = None


class ScanResponse(BaseModel):
    id: int
    patient_id: int
    user_id: int
    image_path: str
    original_filename: Optional[str]
    prediction_result: str
    confidence_score: float
    malignant_probability: float
    benign_probability: float
    risk_level: str
    doctor_notes: Optional[str]
    report_generated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UpdateNotesRequest(BaseModel):
    doctor_notes: str


# ==================== Helper Functions ====================

def save_uploaded_file(file_data: bytes, filename: str, patient_id: int) -> str:
    """Save uploaded file to disk and return path."""
    # Create patient-specific directory
    patient_dir = UPLOAD_DIR / f"patient_{patient_id}"
    patient_dir.mkdir(exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(filename).suffix
    unique_filename = f"scan_{timestamp}{file_extension}"
    
    file_path = patient_dir / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(file_data)
    
    return str(file_path)


# ==================== Endpoints ====================

@router.post("/analyze", response_model=dict, status_code=status.HTTP_201_CREATED)
async def analyze_and_create_scan(
    request: Request,
    patient_id: int,
    file: UploadFile = File(...),
    doctor_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_doctor)
):
    """
    Analyze medical image and create scan record.
    
    - Requires doctor authentication
    - Validates patient exists
    - Analyzes image with AI model
    - Saves image to disk
    - Creates scan record in database
    - Returns analysis results with images
    - Logs action for compliance
    
    ⚠️ This is AI-assisted diagnosis, not a replacement for medical judgment.
    """
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an image file"
        )
    
    # Read and analyze image
    file_data = await file.read()
    
    try:
        image = Image.open(io.BytesIO(file_data)).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read image file: {str(e)}"
        )
    
    # Run AI analysis (use mock if TensorFlow not available)
    try:
        if TENSORFLOW_AVAILABLE:
            # TODO: Implement real TensorFlow analysis here
            # For now, fall back to mock
            analysis, image_data = run_mock_analysis(image)
            analysis_mode = "DEMO (TensorFlow Available but not configured)"
        else:
            # Use mock analysis
            analysis, image_data = run_mock_analysis(image)
            analysis_mode = "DEMO (TensorFlow Not Installed)"
        
        # Add mode indicator
        analysis["analysis_mode"] = analysis_mode
        analysis["demo_warning"] = DEMO_MESSAGE
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    
    # Save uploaded image
    image_path = save_uploaded_file(file_data, file.filename, patient_id)
    
    # Create scan record
    new_scan = Scan(
        patient_id=patient_id,
        user_id=current_user.id,
        image_path=image_path,
        original_filename=file.filename,
        prediction_result=analysis["result"],
        confidence_score=analysis["confidence"],
        malignant_probability=analysis["malignant_prob"],
        benign_probability=analysis["benign_prob"],
        risk_level=analysis["risk_level"],
        mean_intensity=analysis["stats"]["mean_intensity"],
        std_intensity=analysis["stats"]["std_intensity"],
        brightness=analysis["stats"]["brightness"],
        contrast=analysis["stats"]["contrast"],
        image_width=analysis["image_size"]["width"],
        image_height=analysis["image_size"]["height"],
        file_format=analysis["file_format"],
        doctor_notes=doctor_notes,
        findings=json.dumps(analysis.get("findings", {})),
        report_generated=0
    )
    
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    # Log scan creation
    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_SCAN",
        resource_type="scan",
        resource_id=new_scan.id,
        patient_id=patient_id,
        scan_id=new_scan.id,
        details=f"Analyzed scan for patient {patient.full_name}: {analysis['result']}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Return analysis results with scan ID
    return {
        "scan_id": new_scan.id,
        "patient_id": patient_id,
        "patient_name": patient.full_name,
        "analysis": {
            "result": analysis["result"],
            "probability": analysis["confidence"],
            "malignant_prob": analysis["malignant_prob"],
            "benign_prob": analysis["benign_prob"],
            "risk_level": analysis["risk_level"],
            "risk_icon": analysis.get("risk_icon", "⚠️"),
            "stats": analysis["stats"],
            "image_size": analysis["image_size"],
            "findings": analysis["findings"],
            "mode": analysis.get("analysis_mode", "DEMO"),
            "demo_warning": analysis.get("demo_warning", "")
        },
        "images": {
            "original": image_data.get("original_base64"),
            "overlay": image_data.get("overlay_base64"),
            "heatmap_only": image_data.get("heatmap_base64"),
            "bbox": image_data.get("bbox_base64")
        }
    }


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    request: Request,
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get scan details by ID.
    
    - Requires authentication
    - Returns scan information
    - Logs access for compliance
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Log access
    log_audit(
        db=db,
        user_id=current_user.id,
        action="VIEW_SCAN",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return scan


@router.put("/{scan_id}/notes", response_model=ScanResponse)
async def update_scan_notes(
    request: Request,
    scan_id: int,
    notes_data: UpdateNotesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_doctor)
):
    """
    Update doctor's notes for a scan.
    
    - Requires doctor authentication
    - Updates notes field
    - Logs update for compliance
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Update notes
    scan.doctor_notes = notes_data.doctor_notes
    scan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(scan)
    
    # Log update
    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_SCAN_NOTES",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return scan


@router.get("/{scan_id}/download-report")
async def download_scan_report(
    request: Request,
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download PDF report for a scan.
    
    - Requires authentication
    - Generates PDF report from scan data
    - Logs download for compliance
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Load image from disk
    try:
        image = Image.open(scan.image_path).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load scan image: {str(e)}"
        )
    
    # Check if analysis is available
    if not ANALYSIS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report generation is temporarily unavailable. TensorFlow is not properly installed."
        )
    
    # Create simple images for report
    images = {
        "original": image,
        "overlay_image": image,
        "heatmap_only": image,
        "bbox_image": image
    }
    
    # Generate PDF report
    pdf_bytes = generate_report_pdf(
        result=scan.prediction_result,
        probability=scan.malignant_probability if "Malignant" in scan.prediction_result else scan.benign_probability,
        risk_level=scan.risk_level,
        benign_prob=scan.benign_probability,
        malignant_prob=scan.malignant_probability,
        stats={
            "mean_intensity": scan.mean_intensity,
            "std_intensity": scan.std_intensity,
            "brightness": scan.brightness,
            "contrast": scan.contrast,
            "min_intensity": 0.0,  # Default value if not stored
            "max_intensity": 255.0,  # Default value if not stored
            "median_intensity": scan.mean_intensity  # Use mean as approximation
        },
        image_size=(scan.image_width, scan.image_height),
        file_format=scan.file_format,
        original_image=images["original"],
        overlay_image=images["overlay_image"],
        heatmap_only=images["heatmap_only"],
        bbox_image=images["bbox_image"],
        confidence=scan.confidence_score
    )
    
    # Mark report as generated
    if not scan.report_generated:
        scan.report_generated = 1
        db.commit()
    
    # Log download
    log_audit(
        db=db,
        user_id=current_user.id,
        action="DOWNLOAD_REPORT",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=scan.patient_id,
        scan_id=scan.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Return PDF
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="scan_{scan_id}_report.pdf"'
        }
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    request: Request,
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_doctor)
):
    """
    Delete scan record.
    
    - Requires doctor authentication
    - Deletes scan record and image file
    - Logs deletion for compliance
    
    ⚠️ WARNING: This is a permanent operation!
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    patient_id = scan.patient_id
    image_path = scan.image_path
    
    # Log deletion before deleting
    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE_SCAN",
        resource_type="scan",
        resource_id=scan.id,
        patient_id=patient_id,
        scan_id=scan.id,
        details=f"Deleted scan {scan_id} for patient {patient_id}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    # Delete scan record
    db.delete(scan)
    db.commit()
    
    # Try to delete image file (fail silently if not found)
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception:
        pass  # Image deletion failure shouldn't fail the request
    
    return None

