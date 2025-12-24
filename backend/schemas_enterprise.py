"""
Enterprise Multi-Tenant Healthcare SaaS Pydantic Schemas

Comprehensive request/response models for the API.
Includes validation, serialization, and documentation.

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, time
from enum import Enum


# ==================== ENUMS (Mirror SQLAlchemy Enums) ====================

class TenantType(str, Enum):
    HOSPITAL = "hospital"
    LAB = "lab"
    CLINIC = "clinic"
    IMAGING_CENTER = "imaging_center"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    DOCTOR = "doctor"
    LAB_TECH = "lab_tech"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class ScanStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ReminderType(str, Enum):
    MEDICATION = "medication"
    FOLLOW_UP = "follow_up"
    SCREENING = "screening"
    APPOINTMENT = "appointment"
    LAB_RESULT = "lab_result"
    PRESCRIPTION_REFILL = "prescription_refill"


class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# ==================== BASE SCHEMAS ====================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.isoformat() if v else None,
        }


class TimestampMixin(BaseModel):
    """Common timestamp fields."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ==================== AUTHENTICATION SCHEMAS ====================

class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    email: str
    role: UserRole
    tenant_id: Optional[int] = None
    exp: datetime
    iat: datetime
    jti: Optional[str] = None  # Token ID for revocation


class Token(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class LoginRequest(BaseModel):
    """Login credentials."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    remember_me: bool = False


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


# ==================== TENANT SCHEMAS ====================

class TenantBase(BaseModel):
    """Base tenant fields."""
    name: str = Field(..., min_length=2, max_length=255)
    legal_name: Optional[str] = None
    type: TenantType = TenantType.HOSPITAL
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"


class TenantCreate(TenantBase):
    """Create new tenant (organization)."""
    admin_email: EmailStr
    admin_name: str
    subscription_plan: SubscriptionPlan = SubscriptionPlan.TRIAL


class TenantUpdate(BaseModel):
    """Update tenant fields."""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    is_active: Optional[bool] = None


class TenantResponse(TenantBase, TimestampMixin, BaseSchema):
    """Tenant response model."""
    id: int
    uuid: str
    subscription_status: SubscriptionStatus
    subscription_plan: SubscriptionPlan
    trial_ends_at: Optional[datetime] = None
    max_users: int
    max_patients: int
    max_scans_per_month: int
    current_month_scans: int
    logo_url: Optional[str] = None
    primary_color: str
    hipaa_baa_signed: bool
    is_active: bool


class TenantStats(BaseModel):
    """Tenant statistics for super admin."""
    id: int
    name: str
    type: TenantType
    subscription_status: SubscriptionStatus
    subscription_plan: SubscriptionPlan
    user_count: int
    patient_count: int
    scan_count: int
    monthly_scans: int
    created_at: datetime


class TenantListResponse(PaginatedResponse):
    """Paginated tenant list."""
    items: List[TenantStats]


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None


class UserCreate(UserBase):
    """Create new user (by org admin)."""
    role: UserRole
    department_id: Optional[int] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None


class UserCreateResponse(BaseModel):
    """Response when creating user - includes generated credentials."""
    id: int
    username: str
    email: str
    temporary_password: str  # Must change on first login
    full_name: str
    role: UserRole
    message: str = "User created. Credentials must be shared securely with the user."


class UserUpdate(BaseModel):
    """Update user fields."""
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    theme: Optional[str] = None


class UserResponse(UserBase, TimestampMixin, BaseSchema):
    """User response model."""
    id: int
    uuid: str
    username: str
    role: UserRole
    tenant_id: Optional[int] = None
    department_id: Optional[int] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None


class UserListResponse(PaginatedResponse):
    """Paginated user list."""
    items: List[UserResponse]


class UserPreferences(BaseModel):
    """User preferences."""
    timezone: str = "UTC"
    locale: str = "en-US"
    theme: str = "dark"
    notifications: Dict[str, bool] = {
        "email": True,
        "push": True,
        "sms": False
    }
    dashboard_layout: Optional[Dict[str, Any]] = None


# ==================== PATIENT SCHEMAS ====================

class PatientBase(BaseModel):
    """Base patient fields."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = None
    date_of_birth: date
    gender: Gender
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None


class PatientCreate(PatientBase):
    """Create new patient."""
    medical_record_number: Optional[str] = None  # Auto-generated if not provided
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    breast_cancer_history: Optional[Dict[str, Any]] = None


class PatientUpdate(BaseModel):
    """Update patient fields."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    breast_cancer_history: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None


class PatientResponse(PatientBase, TimestampMixin, BaseSchema):
    """Patient response model."""
    id: int
    uuid: str
    tenant_id: int
    medical_record_number: str
    external_id: Optional[str] = None
    fhir_id: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    breast_cancer_history: Optional[Dict[str, Any]] = None
    consent_signed: bool
    portal_enabled: bool
    is_active: bool
    age: Optional[int] = None
    
    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)


class PatientSummary(BaseModel):
    """Brief patient info for lists."""
    id: int
    medical_record_number: str
    full_name: str
    age: int
    gender: Gender
    last_scan_date: Optional[datetime] = None
    risk_level: Optional[RiskLevel] = None


class PatientListResponse(PaginatedResponse):
    """Paginated patient list."""
    items: List[PatientSummary]


class PatientPortalAccess(BaseModel):
    """Enable/disable patient portal."""
    portal_enabled: bool
    email: EmailStr  # Required for portal access


# ==================== APPOINTMENT SCHEMAS ====================

class AppointmentBase(BaseModel):
    """Base appointment fields."""
    patient_id: int
    doctor_id: int
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 30
    appointment_type: str = "consultation"
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Create new appointment."""
    send_reminder: bool = True


class AppointmentUpdate(BaseModel):
    """Update appointment fields."""
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None


class AppointmentResponse(AppointmentBase, TimestampMixin, BaseSchema):
    """Appointment response model."""
    id: int
    uuid: str
    tenant_id: int
    status: AppointmentStatus
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reminder_sent: bool
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None


class AppointmentListResponse(PaginatedResponse):
    """Paginated appointment list."""
    items: List[AppointmentResponse]


class AppointmentCheckIn(BaseModel):
    """Check-in patient for appointment."""
    notes: Optional[str] = None


class AppointmentCancel(BaseModel):
    """Cancel appointment."""
    reason: str
    notify_patient: bool = True


# ==================== SCAN SCHEMAS ====================

class ScanCreate(BaseModel):
    """Create scan analysis request."""
    patient_id: int
    scan_type: str = "mammogram"
    doctor_notes: Optional[str] = None
    disclaimer_accepted: bool = False


class ScanAnalysisResult(BaseModel):
    """AI analysis result details."""
    result: str  # "Benign" or "Malignant"
    probability: float
    malignant_prob: float
    benign_prob: float
    risk_level: RiskLevel
    risk_icon: str
    confidence_score: float
    findings: Dict[str, Any]
    stats: Dict[str, float]
    mode: str  # "DEMO" or "PRODUCTION"


class ScanResponse(TimestampMixin, BaseSchema):
    """Scan response model."""
    id: int
    uuid: str
    tenant_id: int
    patient_id: int
    performed_by_id: int
    reviewed_by_id: Optional[int] = None
    scan_type: str
    status: ScanStatus
    prediction_result: Optional[str] = None
    confidence_score: Optional[float] = None
    malignant_probability: Optional[float] = None
    benign_probability: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    findings: Optional[Dict[str, Any]] = None
    doctor_notes: Optional[str] = None
    clinical_impression: Optional[str] = None
    recommendations: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    report_generated: bool
    patient_name: Optional[str] = None
    performed_by_name: Optional[str] = None


class ScanReview(BaseModel):
    """Doctor's review of scan."""
    clinical_impression: str
    recommendations: str
    doctor_notes: Optional[str] = None
    approve: bool = False


class ScanListResponse(PaginatedResponse):
    """Paginated scan list."""
    items: List[ScanResponse]


# ==================== PRESCRIPTION SCHEMAS ====================

class Medication(BaseModel):
    """Single medication in prescription."""
    name: str
    dosage: str
    frequency: str  # "once daily", "twice daily", etc.
    duration: str  # "7 days", "2 weeks", etc.
    instructions: Optional[str] = None
    quantity: int = 30
    refills: int = 0


class PrescriptionCreate(BaseModel):
    """Create new prescription."""
    patient_id: int
    scan_id: Optional[int] = None
    medications: List[Medication]
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    valid_days: int = 30  # Days prescription is valid


class PrescriptionUpdate(BaseModel):
    """Update prescription (draft only)."""
    medications: Optional[List[Medication]] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None


class PrescriptionSign(BaseModel):
    """Sign prescription digitally."""
    signature_confirmation: bool = True
    pin: Optional[str] = None  # Optional PIN verification


class PrescriptionResponse(TimestampMixin, BaseSchema):
    """Prescription response model."""
    id: int
    uuid: str
    tenant_id: int
    patient_id: int
    doctor_id: int
    scan_id: Optional[int] = None
    prescription_number: str
    medications: List[Medication]
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    status: PrescriptionStatus
    signed_at: Optional[datetime] = None
    dispensed_at: Optional[datetime] = None
    valid_from: date
    valid_until: Optional[date] = None
    pdf_path: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None


class PrescriptionListResponse(PaginatedResponse):
    """Paginated prescription list."""
    items: List[PrescriptionResponse]


# ==================== REMINDER SCHEMAS ====================

class ReminderCreate(BaseModel):
    """Create new reminder."""
    patient_id: int
    type: ReminderType
    title: str
    message: Optional[str] = None
    trigger_time: datetime
    recurrence: Optional[str] = None  # "daily", "weekly", etc.
    recurrence_end: Optional[datetime] = None
    channels: List[str] = ["in_app"]
    prescription_id: Optional[int] = None
    appointment_id: Optional[int] = None
    scan_id: Optional[int] = None


class ReminderUpdate(BaseModel):
    """Update reminder."""
    title: Optional[str] = None
    message: Optional[str] = None
    trigger_time: Optional[datetime] = None
    recurrence: Optional[str] = None
    recurrence_end: Optional[datetime] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ReminderResponse(TimestampMixin, BaseSchema):
    """Reminder response model."""
    id: int
    uuid: str
    tenant_id: int
    patient_id: int
    type: ReminderType
    title: str
    message: Optional[str] = None
    trigger_time: datetime
    recurrence: Optional[str] = None
    recurrence_end: Optional[datetime] = None
    channels: List[str]
    is_active: bool
    is_sent: bool
    sent_at: Optional[datetime] = None
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    patient_name: Optional[str] = None


class ReminderAcknowledge(BaseModel):
    """Acknowledge reminder."""
    notes: Optional[str] = None


# ==================== MEDICATION LOG SCHEMAS ====================

class MedicationLogCreate(BaseModel):
    """Log medication taken/skipped."""
    medication_name: str
    dosage: str
    scheduled_time: datetime
    taken: bool = False
    skip_reason: Optional[str] = None
    notes: Optional[str] = None
    side_effects: Optional[str] = None


class MedicationLogResponse(TimestampMixin, BaseSchema):
    """Medication log response."""
    id: int
    patient_id: int
    prescription_id: Optional[int] = None
    medication_name: str
    dosage: str
    scheduled_time: datetime
    taken: bool
    taken_at: Optional[datetime] = None
    skipped: bool
    skip_reason: Optional[str] = None
    notes: Optional[str] = None


class MedicationTrackerSummary(BaseModel):
    """Medication tracker summary for patient."""
    medication_name: str
    dosage: str
    frequency: str
    today_logs: List[MedicationLogResponse]
    adherence_rate: float  # Percentage taken vs scheduled


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationResponse(BaseSchema):
    """Notification response."""
    id: int
    title: str
    message: str
    type: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    created_at: datetime


class NotificationListResponse(PaginatedResponse):
    """Paginated notification list."""
    items: List[NotificationResponse]
    unread_count: int


# ==================== AUDIT LOG SCHEMAS ====================

class AuditLogResponse(BaseSchema):
    """Audit log entry."""
    id: int
    uuid: str
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    created_at: datetime


class AuditLogListResponse(PaginatedResponse):
    """Paginated audit log list."""
    items: List[AuditLogResponse]


class AuditLogFilter(BaseModel):
    """Audit log filter parameters."""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None


# ==================== DASHBOARD SCHEMAS ====================

class SuperAdminDashboard(BaseModel):
    """Super admin dashboard statistics."""
    total_tenants: int
    active_tenants: int
    trial_tenants: int
    total_users: int
    total_patients: int
    total_scans: int
    scans_this_month: int
    revenue_this_month: float
    tenants_by_plan: Dict[str, int]
    scans_by_day: List[Dict[str, Any]]
    recent_tenants: List[TenantStats]


class OrgAdminDashboard(BaseModel):
    """Organization admin dashboard statistics."""
    tenant_name: str
    total_users: int
    total_patients: int
    total_scans: int
    scans_this_month: int
    subscription_status: SubscriptionStatus
    subscription_plan: SubscriptionPlan
    usage_percentage: float
    users_by_role: Dict[str, int]
    scans_by_day: List[Dict[str, Any]]
    pending_reviews: int
    appointments_today: int
    recent_scans: List[ScanResponse]


class DoctorDashboard(BaseModel):
    """Doctor/medical staff dashboard."""
    doctor_name: str
    appointments_today: List[AppointmentResponse]
    pending_reviews: List[ScanResponse]
    recent_patients: List[PatientSummary]
    scans_this_week: int
    prescriptions_this_week: int
    notifications: List[NotificationResponse]


class PatientDashboard(BaseModel):
    """Patient portal dashboard."""
    patient_name: str
    upcoming_appointments: List[AppointmentResponse]
    recent_scans: List[ScanResponse]
    active_prescriptions: List[PrescriptionResponse]
    medication_schedule: List[MedicationTrackerSummary]
    alerts: List[ReminderResponse]
    unread_notifications: int


# ==================== ALERT SCHEMAS ====================

class Alert(BaseModel):
    """Alert/warning for patient portal."""
    id: int
    type: str  # "warning", "danger", "info"
    title: str
    message: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class PatientAlerts(BaseModel):
    """Patient alerts summary."""
    patient_id: int
    overdue_screenings: List[Alert]
    missed_medications: List[Alert]
    upcoming_appointments: List[Alert]
    pending_results: List[Alert]


# ==================== REPORT SCHEMAS ====================

class ReportRequest(BaseModel):
    """Request for report generation."""
    scan_id: int
    include_heatmap: bool = True
    include_statistics: bool = True
    include_recommendations: bool = True
    doctor_signature: bool = True


class ReportResponse(BaseModel):
    """Report generation response."""
    scan_id: int
    report_path: str
    pdf_url: str
    generated_at: datetime


# ==================== SEARCH SCHEMAS ====================

class SearchRequest(BaseModel):
    """Global search request."""
    query: str = Field(..., min_length=2)
    types: List[str] = ["patients", "scans", "appointments"]
    limit: int = 20


class SearchResult(BaseModel):
    """Search result item."""
    type: str
    id: int
    title: str
    subtitle: str
    url: str
    relevance: float


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    total_results: int
    results: List[SearchResult]


# ==================== ONBOARDING SCHEMAS ====================

class OnboardTenantRequest(BaseModel):
    """Onboard new hospital/organization."""
    # Organization Details
    organization_name: str = Field(..., min_length=2)
    organization_type: TenantType = TenantType.HOSPITAL
    organization_email: EmailStr
    organization_phone: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"
    
    # Admin Details
    admin_name: str = Field(..., min_length=2)
    admin_email: EmailStr
    
    # Subscription
    subscription_plan: SubscriptionPlan = SubscriptionPlan.TRIAL
    
    # Compliance
    accept_terms: bool = False
    accept_hipaa_baa: bool = False


class OnboardTenantResponse(BaseModel):
    """Onboarding response with credentials."""
    tenant: TenantResponse
    admin_user: UserCreateResponse
    message: str


# Update forward references
Token.model_rebuild()

