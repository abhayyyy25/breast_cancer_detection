"""
Pydantic Schemas for Multi-Tenant SaaS API
Request/Response models for all endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ============================================================================
# ENUMS (matching database enums)
# ============================================================================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORGANIZATION_ADMIN = "organization_admin"
    DOCTOR = "doctor"
    LAB_TECH = "lab_tech"
    PATIENT = "patient"


class OrganizationType(str, Enum):
    HOSPITAL = "hospital"
    PATHOLOGY_LAB = "pathology_lab"
    DIAGNOSTIC_CENTER = "diagnostic_center"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ScanStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    user_id: int
    username: str
    role: UserRole
    tenant_id: Optional[int] = None


# ============================================================================
# TENANT SCHEMAS
# ============================================================================

class TenantCreate(BaseModel):
    """Super Admin creates a new organization (Hospital/Lab)"""
    name: str = Field(..., min_length=3, max_length=255)
    organization_type: OrganizationType
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None
    monthly_scan_limit: int = Field(default=100, ge=10, le=10000)
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    # Admin credentials
    admin_full_name: str = Field(..., min_length=2, max_length=255)
    admin_username: str = Field(..., min_length=3, max_length=100)
    admin_password: str = Field(..., min_length=6)


class TenantUpdate(BaseModel):
    """Update tenant information"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = None
    monthly_scan_limit: Optional[int] = Field(None, ge=10, le=10000)
    is_active: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    name: str
    organization_type: OrganizationType
    subscription_status: SubscriptionStatus
    contact_email: str
    contact_phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    monthly_scan_limit: int
    current_month_scans: int
    total_scans_processed: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Detailed statistics for a tenant"""
    tenant_id: int
    tenant_name: str
    total_users: int
    total_patients: int
    total_scans: int
    scans_this_month: int
    active_doctors: int
    active_lab_techs: int


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    """Organization Admin creates staff/patient accounts"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    license_number: Optional[str] = None  # For medical staff
    department: Optional[str] = None
    specialization: Optional[str] = None
    # Manual credentials
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    
    @validator('role')
    def validate_role(cls, v):
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Cannot create super admin through this endpoint")
        return v


class UserCreateResponse(BaseModel):
    """Response when creating a user with manual credentials"""
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    tenant_id: Optional[int]
    message: str = "User created successfully."


class UserUpdate(BaseModel):
    """Update user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    tenant_id: Optional[int]
    phone: Optional[str]
    gender: Optional[Gender]
    department: Optional[str]
    specialization: Optional[str]
    license_number: Optional[str]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


# ============================================================================
# PATIENT SCHEMAS
# ============================================================================

class PatientCreate(BaseModel):
    """Create a new patient record"""
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date
    gender: Gender
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history_json: Optional[Dict[str, Any]] = None
    family_history_json: Optional[Dict[str, Any]] = None
    risk_factors_json: Optional[Dict[str, Any]] = None
    # Patient portal credentials
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class PatientUpdate(BaseModel):
    """Update patient information"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history_json: Optional[Dict[str, Any]] = None
    family_history_json: Optional[Dict[str, Any]] = None
    risk_factors_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    mrn: str
    full_name: str
    date_of_birth: date
    gender: Gender
    email: str
    phone: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    blood_group: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    medical_history_json: Optional[Dict[str, Any]]
    family_history_json: Optional[Dict[str, Any]]
    is_active: bool
    registered_date: datetime
    last_visit_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class PatientSearchResponse(BaseModel):
    """Simplified patient info for search results"""
    id: int
    mrn: str
    full_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    last_visit_date: Optional[datetime]


# ============================================================================
# SCAN SCHEMAS
# ============================================================================

class ScanCreate(BaseModel):
    """Request to create a new scan analysis"""
    patient_id: int
    scan_type: str = "mammography"
    doctor_notes: Optional[str] = None
    disclaimer_accepted: bool = False


class ScanUpdate(BaseModel):
    """Update scan notes/status"""
    doctor_notes: Optional[str] = None
    radiologist_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    status: Optional[ScanStatus] = None


class ScanResponse(BaseModel):
    id: int
    tenant_id: int
    patient_id: int
    performed_by_user_id: int
    scan_number: str
    scan_type: str
    status: ScanStatus
    prediction: Optional[str]
    confidence_score: Optional[float]
    risk_level: Optional[str]
    image_filename: str
    doctor_notes: Optional[str]
    radiologist_notes: Optional[str]
    scan_date: datetime
    analysis_completed_at: Optional[datetime]
    report_generated: bool
    disclaimer_accepted: bool
    
    class Config:
        from_attributes = True


class ScanAnalysisResult(BaseModel):
    """Complete analysis results"""
    scan_id: int
    scan_number: str
    patient_name: str
    patient_mrn: str
    prediction: str
    confidence_score: float
    risk_level: str
    analysis_results: Dict[str, Any]
    image_statistics: Dict[str, Any]
    original_image_base64: str
    heatmap_image_base64: Optional[str]
    overlay_image_base64: Optional[str]
    scan_date: datetime
    performed_by: str


# ============================================================================
# AUDIT LOG SCHEMAS
# ============================================================================

class AuditLogCreate(BaseModel):
    """Internal schema for creating audit logs"""
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    patient_id: Optional[int] = None
    scan_id: Optional[int] = None
    description: Optional[str] = None
    changes_json: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    user_name: str
    user_role: str
    action: str
    resource_type: str
    resource_id: Optional[int]
    description: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]
    success: bool
    
    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD STATISTICS SCHEMAS
# ============================================================================

class SuperAdminDashboard(BaseModel):
    """Global statistics for Super Admin"""
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    suspended_tenants: int
    total_users: int
    total_patients: int
    total_scans_processed: int
    scans_today: int
    scans_this_month: int
    monthly_revenue: float
    total_revenue: float
    recent_tenants: List[TenantResponse]
    top_tenants_by_usage: List[TenantStats]


class HospitalAdminDashboard(BaseModel):
    """Statistics for Hospital/Lab Admin"""
    tenant_name: str
    total_doctors: int
    total_lab_techs: int
    total_patients: int
    total_scans: int
    scans_today: int
    scans_this_week: int
    scans_this_month: int
    monthly_scan_limit: int
    scan_limit_usage_percentage: float
    recent_scans: List[ScanResponse]
    active_users: List[UserResponse]


class PatientDashboard(BaseModel):
    """Patient portal statistics"""
    patient_name: str
    mrn: str
    total_scans: int
    last_scan_date: Optional[datetime]
    recent_scans: List[ScanResponse]
    risk_summary: Dict[str, Any]


class MedicalStaffDashboard(BaseModel):
    """Medical staff (Doctor/Lab Tech) dashboard statistics"""
    total_patients: int
    total_scans: int
    scans_today: int = 0
    scans_this_week: int = 0
    scans_this_month: int = 0
    recent_scans: int = 0  # Last 7 days
    user_role: str
    user_name: str


# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Forward references
LoginResponse.model_rebuild()

