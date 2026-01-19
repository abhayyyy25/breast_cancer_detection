"""
Multi-Tenant SaaS Database Models for PATH Labs & Hospitals
Supports: Super Admin, Organization Admin, Medical Staff, Patient
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORGANIZATION_ADMIN = "organization_admin"
    DOCTOR = "doctor"
    LAB_TECH = "lab_tech"
    PATIENT = "patient"


class OrganizationType(str, enum.Enum):
    HOSPITAL = "hospital"
    PATHOLOGY_LAB = "pathology_lab"
    DIAGNOSTIC_CENTER = "diagnostic_center"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ============================================================================
# TENANT/ORGANIZATION MODEL
# ============================================================================

class Tenant(Base):
    """
    Represents a Hospital, Pathology Lab, or Diagnostic Center
    Each tenant is completely isolated from others
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    organization_type = Column(SQLEnum(OrganizationType), nullable=False)
    
    # Subscription Management
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    subscription_start_date = Column(DateTime, default=datetime.utcnow)
    subscription_end_date = Column(DateTime, nullable=True)
    
    # Contact Information
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="India")
    postal_code = Column(String(20), nullable=True)
    
    # Billing & Usage Limits
    monthly_scan_limit = Column(Integer, default=100)
    current_month_scans = Column(Integer, default=0)
    total_scans_processed = Column(Integer, default=0)
    
    # Settings
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#1E40AF")  # Hex color
    settings_json = Column(JSON, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="tenant", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', type='{self.organization_type}')>"


# ============================================================================
# USER MODEL (Multi-Role)
# ============================================================================

class User(Base):
    """
    Unified User model for all roles:
    - Super Admin (no tenant_id)
    - Organization Admin (has tenant_id)
    - Doctor (has tenant_id)
    - Lab Tech (has tenant_id)
    - Patient (has tenant_id)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    
    # Personal Information
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    
    # Professional Information (for Medical Staff)
    license_number = Column(String(100), nullable=True)  # Medical license
    department = Column(String(100), nullable=True)
    specialization = Column(String(100), nullable=True)
    
    # Profile
    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Security
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    created_by = relationship("User", remote_side=[id], foreign_keys=[created_by_user_id])
    
    # Medical Staff relationships
    scans_performed = relationship("Scan", back_populates="performed_by_user", foreign_keys="Scan.performed_by_user_id")
    
    # Patient-specific relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    
    # Audit logs
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


# ============================================================================
# PATIENT MODEL
# ============================================================================

class Patient(Base):
    """
    Patient records linked to a User account
    Contains medical history and demographics
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Patient Identification
    mrn = Column(String(50), nullable=False, index=True)  # Medical Record Number (unique per tenant)
    
    # Demographics (duplicated from User for convenience)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    
    # Contact Information
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(100), nullable=True)
    
    # Medical Information
    blood_group = Column(String(10), nullable=True)
    medical_history_json = Column(JSON, nullable=True)  # {allergies: [], conditions: [], medications: []}
    family_history_json = Column(JSON, nullable=True)   # {breast_cancer: bool, other_cancers: []}
    risk_factors_json = Column(JSON, nullable=True)     # {smoking: bool, alcohol: bool, etc.}
    
    # Insurance (optional)
    insurance_provider = Column(String(255), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    registered_date = Column(DateTime, default=datetime.utcnow)
    last_visit_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="patients")
    user = relationship("User", back_populates="patient_profile")
    scans = relationship("Scan", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, mrn='{self.mrn}', name='{self.full_name}')>"


# ============================================================================
# SCAN MODEL (Enhanced)
# ============================================================================

class Scan(Base):
    """
    Medical imaging scans with AI analysis results
    """
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    performed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Scan Identification
    scan_number = Column(String(100), unique=True, nullable=False, index=True)  # Auto-generated
    scan_type = Column(String(100), default="mammography")
    
    # Image Information
    image_path = Column(String(500), nullable=False)
    image_filename = Column(String(255), nullable=False)
    image_size_bytes = Column(Integer, nullable=True)
    image_format = Column(String(20), nullable=True)  # jpg, png, dcm
    
    # AI Analysis Results
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, index=True)
    prediction = Column(String(50), nullable=True)  # "benign", "malignant"
    confidence_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)  # "low", "moderate", "high", "very_high"
    
    # Detailed Statistics
    analysis_results_json = Column(JSON, nullable=True)  # Full AI output
    image_statistics_json = Column(JSON, nullable=True)  # {mean, std, min, max, etc.}
    
    # Visualizations
    heatmap_path = Column(String(500), nullable=True)
    overlay_path = Column(String(500), nullable=True)
    
    # Clinical Notes
    doctor_notes = Column(Text, nullable=True)
    radiologist_notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Disclaimer & Compliance
    disclaimer_accepted = Column(Boolean, default=False)
    disclaimer_accepted_at = Column(DateTime, nullable=True)
    
    # Report
    report_generated = Column(Boolean, default=False)
    report_path = Column(String(500), nullable=True)
    
    # Timing
    scan_date = Column(DateTime, default=datetime.utcnow, index=True)
    analysis_started_at = Column(DateTime, nullable=True)
    analysis_completed_at = Column(DateTime, nullable=True)
    analysis_duration_seconds = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="scans")
    patient = relationship("Patient", back_populates="scans")
    performed_by_user = relationship("User", back_populates="scans_performed", foreign_keys=[performed_by_user_id])
    audit_logs = relationship("AuditLog", back_populates="scan", foreign_keys="AuditLog.scan_id")

    def __repr__(self):
        return f"<Scan(id={self.id}, scan_number='{self.scan_number}', patient_id={self.patient_id})>"


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class AuditLog(Base):
    """
    Comprehensive audit trail for HIPAA compliance
    Logs every access and modification of patient data
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)
    user_name = Column(String(255), nullable=False)
    
    # What was accessed/modified
    action = Column(String(100), nullable=False, index=True)  # "view", "create", "update", "delete", "login", "export"
    resource_type = Column(String(100), nullable=False, index=True)  # "patient", "scan", "user", "tenant"
    resource_id = Column(Integer, nullable=True)
    
    # Related records
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True, index=True)
    
    # Details
    description = Column(Text, nullable=True)
    changes_json = Column(JSON, nullable=True)  # Before/after values
    
    # Request Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Security
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
    scan = relationship("Scan", back_populates="audit_logs", foreign_keys=[scan_id])

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id}, timestamp={self.timestamp})>"


# ============================================================================
# SYSTEM STATISTICS MODEL
# ============================================================================

class SystemStatistics(Base):
    """
    Global statistics for Super Admin dashboard
    """
    __tablename__ = "system_statistics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metrics
    total_tenants = Column(Integer, default=0)
    active_tenants = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    total_patients = Column(Integer, default=0)
    total_scans_processed = Column(Integer, default=0)
    scans_today = Column(Integer, default=0)
    scans_this_month = Column(Integer, default=0)
    
    # Revenue (for future billing integration)
    monthly_revenue = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)
    
    # Timestamp
    date = Column(Date, unique=True, default=datetime.utcnow().date)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemStatistics(date={self.date}, total_scans={self.total_scans_processed})>"


# ============================================================================
# REPORT SETTINGS MODEL
# ============================================================================

class ReportSettings(Base):
    """
    Doctor/Organization Report Customization Settings
    Stores branding and default information for PDF reports
    """
    __tablename__ = "report_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Hospital/Clinic Branding
    hospital_name = Column(String(255), nullable=True)
    hospital_logo_url = Column(String(500), nullable=True)
    logo_base64 = Column(Text, nullable=True)  # Base64-encoded logo image for database storage
    hospital_address = Column(Text, nullable=True)
    hospital_contact = Column(String(255), nullable=True)
    
    # Doctor Details (Default)
    doctor_name = Column(String(255), nullable=True)  # Doctor's name for reports
    display_name = Column(String(255), nullable=True)  # e.g., "Dr. Rajesh Sharma, MD"
    license_number = Column(String(100), nullable=True)  # Medical license/registration #
    signature_url = Column(String(500), nullable=True)  # Digital signature image
    
    # Report Customization
    footer_text = Column(Text, nullable=True)  # Custom footer text for PDF reports
    
    # Report Customization
    report_header_color = Column(String(7), default="#2563EB")  # Hex color
    report_footer_text = Column(Text, nullable=True)
    include_disclaimer = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    def __repr__(self):
        return f"<ReportSettings(id={self.id}, user_id={self.user_id}, hospital='{self.hospital_name}')>"

