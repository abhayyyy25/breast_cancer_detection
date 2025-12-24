"""
Enterprise Multi-Tenant Healthcare SaaS Database Models

This module defines the complete SQLAlchemy ORM schema for a HIPAA-compliant,
multi-tenant medical imaging and patient management platform.

Architecture:
- Multi-tenancy via tenant_id foreign keys
- 4-level role hierarchy: SuperAdmin, OrgAdmin, MedicalStaff, Patient
- Full audit logging for compliance
- Soft deletes for data retention requirements

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Enum, JSON, Date, Time, UniqueConstraint, Index,
    CheckConstraint, Table
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
import uuid

Base = declarative_base()


# ==================== ENUMS ====================

class TenantType(enum.Enum):
    """Type of healthcare organization."""
    HOSPITAL = "hospital"
    LAB = "lab"
    CLINIC = "clinic"
    IMAGING_CENTER = "imaging_center"


class SubscriptionStatus(enum.Enum):
    """Tenant subscription status."""
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionPlan(enum.Enum):
    """Subscription plan tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserRole(enum.Enum):
    """User role hierarchy."""
    SUPER_ADMIN = "super_admin"      # Platform owner - global access
    ORG_ADMIN = "org_admin"          # Hospital IT admin - org-level access
    DOCTOR = "doctor"                # Medical doctor - patient care access
    LAB_TECH = "lab_tech"            # Lab technician - scan access only
    NURSE = "nurse"                  # Nursing staff - limited patient access
    RECEPTIONIST = "receptionist"   # Front desk - appointments only
    PATIENT = "patient"              # Patient - own data only


class AppointmentStatus(enum.Enum):
    """Appointment workflow status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class ScanStatus(enum.Enum):
    """Medical scan processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"


class RiskLevel(enum.Enum):
    """AI-detected risk classification."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ReminderType(enum.Enum):
    """Patient reminder categories."""
    MEDICATION = "medication"
    FOLLOW_UP = "follow_up"
    SCREENING = "screening"
    APPOINTMENT = "appointment"
    LAB_RESULT = "lab_result"
    PRESCRIPTION_REFILL = "prescription_refill"


class NotificationChannel(enum.Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class AuditAction(enum.Enum):
    """Types of auditable actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    DOWNLOAD = "download"
    SHARE = "share"
    ANALYZE = "analyze"
    PRESCRIBE = "prescribe"
    SIGN = "sign"


class PrescriptionStatus(enum.Enum):
    """Prescription lifecycle status."""
    DRAFT = "draft"
    SIGNED = "signed"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Gender(enum.Enum):
    """Patient gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# ==================== CORE MODELS ====================

class Tenant(Base):
    """
    Healthcare Organization (Hospital/Lab/Clinic).
    
    This is the root of the multi-tenancy model. All patient data,
    users, and scans are isolated by tenant_id.
    """
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Organization Details
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    type = Column(Enum(TenantType), default=TenantType.HOSPITAL)
    
    # Contact Information
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="USA")
    
    # Subscription & Billing
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    trial_ends_at = Column(DateTime)
    subscription_starts_at = Column(DateTime)
    subscription_ends_at = Column(DateTime)
    
    # Usage Limits
    max_users = Column(Integer, default=10)
    max_patients = Column(Integer, default=100)
    max_scans_per_month = Column(Integer, default=500)
    current_month_scans = Column(Integer, default=0)
    
    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#1E40AF")
    
    # Compliance
    hipaa_baa_signed = Column(Boolean, default=False)
    hipaa_baa_signed_at = Column(DateTime)
    
    # Integration Keys (encrypted in production)
    fhir_endpoint = Column(String(500))
    hl7_enabled = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    patients = relationship("Patient", back_populates="tenant", lazy="dynamic")
    departments = relationship("Department", back_populates="tenant", lazy="dynamic")
    
    def __repr__(self):
        return f"<Tenant {self.name} ({self.type.value})>"


class Department(Base):
    """
    Hospital departments for organizational hierarchy.
    """
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    description = Column(Text)
    
    head_user_id = Column(Integer, ForeignKey("users.id"))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="departments")
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_department_tenant_code'),
        Index('ix_department_tenant', 'tenant_id'),
    )


class User(Base):
    """
    System users with role-based access control.
    
    Supports all 4 hierarchy levels:
    - super_admin: Platform-wide access (tenant_id = NULL)
    - org_admin: Organization-wide access
    - doctor/lab_tech/nurse: Department-level access
    - patient: Own data only (linked via patient_profile)
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant association (NULL for super_admin)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Role & Permissions
    role = Column(Enum(UserRole), nullable=False)
    permissions = Column(JSON, default=list)  # Additional granular permissions
    
    # Profile
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(100))  # Dr., Prof., etc.
    phone = Column(String(50))
    avatar_url = Column(String(500))
    
    # Professional Details (for medical staff)
    license_number = Column(String(100))
    specialty = Column(String(100))
    qualifications = Column(JSON, default=list)  # ["MD", "FACP", etc.]
    signature_url = Column(String(500))  # Digital signature for prescriptions
    
    # Preferences
    preferences = Column(JSON, default=dict)
    timezone = Column(String(50), default="UTC")
    locale = Column(String(10), default="en-US")
    theme = Column(String(20), default="dark")
    
    # Security
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    
    # Session Tracking
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    patient_profile = relationship("Patient", back_populates="user_account", uselist=False, 
                                   foreign_keys="Patient.user_id")
    
    # Medical staff relationships
    appointments_as_doctor = relationship("Appointment", back_populates="doctor",
                                          foreign_keys="Appointment.doctor_id")
    prescriptions_written = relationship("Prescription", back_populates="doctor",
                                         foreign_keys="Prescription.doctor_id")
    scans_performed = relationship("Scan", back_populates="performed_by",
                                   foreign_keys="Scan.performed_by_id")
    
    __table_args__ = (
        Index('ix_user_tenant', 'tenant_id'),
        Index('ix_user_role', 'role'),
        Index('ix_user_email', 'email'),
    )
    
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_org_admin(self):
        return self.role == UserRole.ORG_ADMIN
    
    @property
    def is_medical_staff(self):
        return self.role in [UserRole.DOCTOR, UserRole.LAB_TECH, UserRole.NURSE]
    
    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


class Patient(Base):
    """
    Patient records with comprehensive medical history.
    
    Linked to tenant for multi-tenancy isolation.
    Can optionally have a User account for patient portal access.
    """
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant & User Links
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Portal access
    
    # Identification
    medical_record_number = Column(String(50), nullable=False)
    external_id = Column(String(100))  # External system ID
    fhir_id = Column(String(100))  # FHIR resource ID for interoperability
    
    # Demographics
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    
    # Contact
    email = Column(String(255))
    phone_primary = Column(String(50))
    phone_secondary = Column(String(50))
    preferred_contact = Column(String(20), default="phone")
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="USA")
    
    # Emergency Contact
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(50))
    emergency_contact_relationship = Column(String(50))
    
    # Insurance
    insurance_provider = Column(String(255))
    insurance_policy_number = Column(String(100))
    insurance_group_number = Column(String(100))
    
    # Medical History (JSONB for flexibility)
    medical_history = Column(JSON, default=dict)
    # Structure: {
    #   "conditions": ["Type 2 Diabetes", "Hypertension"],
    #   "allergies": ["Penicillin"],
    #   "medications": ["Metformin 500mg"],
    #   "surgeries": ["Appendectomy 2015"],
    #   "family_history": {"cancer": true, "diabetes": true}
    # }
    
    # Breast Cancer Specific
    breast_cancer_history = Column(JSON, default=dict)
    # Structure: {
    #   "previous_screenings": [],
    #   "family_history": true,
    #   "genetic_testing": {"brca1": "negative", "brca2": "not_tested"},
    #   "risk_factors": ["age", "family_history"]
    # }
    
    # Preferences
    notification_preferences = Column(JSON, default=dict)
    # Structure: {
    #   "email": true, "sms": true, "whatsapp": false,
    #   "medication_reminders": true, "appointment_reminders": true
    # }
    
    # Consent & Compliance
    consent_signed = Column(Boolean, default=False)
    consent_signed_at = Column(DateTime)
    hipaa_acknowledgment = Column(Boolean, default=False)
    marketing_opt_in = Column(Boolean, default=False)
    
    # Portal Access
    portal_enabled = Column(Boolean, default=False)
    portal_last_login = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deceased = Column(Boolean, default=False)
    deceased_at = Column(Date)
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="patients")
    user_account = relationship("User", back_populates="patient_profile", foreign_keys=[user_id])
    appointments = relationship("Appointment", back_populates="patient", lazy="dynamic")
    scans = relationship("Scan", back_populates="patient", lazy="dynamic")
    prescriptions = relationship("Prescription", back_populates="patient", lazy="dynamic")
    reminders = relationship("Reminder", back_populates="patient", lazy="dynamic")
    medication_logs = relationship("MedicationLog", back_populates="patient", lazy="dynamic")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'medical_record_number', name='uq_patient_mrn'),
        Index('ix_patient_tenant', 'tenant_id'),
        Index('ix_patient_name', 'last_name', 'first_name'),
    )
    
    @property
    def full_name(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def __repr__(self):
        return f"<Patient {self.full_name} (MRN: {self.medical_record_number})>"


class Appointment(Base):
    """
    Patient appointments with doctors.
    """
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant isolation
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Participants
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Scheduling
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    
    # Details
    appointment_type = Column(String(100), default="consultation")
    reason = Column(Text)
    notes = Column(Text)
    
    # Status
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    
    # Check-in tracking
    checked_in_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Cancellation
    cancelled_at = Column(DateTime)
    cancelled_by = Column(Integer, ForeignKey("users.id"))
    cancellation_reason = Column(Text)
    
    # Reminders
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User", back_populates="appointments_as_doctor", foreign_keys=[doctor_id])
    
    __table_args__ = (
        Index('ix_appointment_tenant', 'tenant_id'),
        Index('ix_appointment_date', 'scheduled_date'),
        Index('ix_appointment_doctor', 'doctor_id', 'scheduled_date'),
        Index('ix_appointment_patient', 'patient_id'),
    )


class Scan(Base):
    """
    Medical imaging scans and AI analysis results.
    """
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant isolation
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Patient & Staff
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Linked appointment (optional)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    
    # Image Data
    scan_type = Column(String(50), default="mammogram")
    modality = Column(String(50))  # DICOM modality (MG, US, MRI, etc.)
    image_path = Column(String(500), nullable=False)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    file_format = Column(String(20))
    
    # DICOM Metadata
    dicom_metadata = Column(JSON, default=dict)
    # Structure: {
    #   "study_uid": "...",
    #   "series_uid": "...",
    #   "sop_instance_uid": "...",
    #   "patient_position": "...",
    #   "laterality": "L" or "R",
    #   "view_position": "CC" or "MLO"
    # }
    
    # AI Analysis Results
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    prediction_result = Column(String(50))  # "Benign", "Malignant"
    confidence_score = Column(Float)
    malignant_probability = Column(Float)
    benign_probability = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    
    # Detailed Findings
    findings = Column(JSON, default=dict)
    # Structure: {
    #   "masses": [{"location": "...", "size": "...", "shape": "..."}],
    #   "calcifications": [],
    #   "architectural_distortion": false,
    #   "asymmetry": false,
    #   "birads_category": "2"
    # }
    
    # Image Statistics
    image_width = Column(Integer)
    image_height = Column(Integer)
    mean_intensity = Column(Float)
    std_intensity = Column(Float)
    brightness = Column(Float)
    contrast = Column(Float)
    
    # Visualization
    heatmap_path = Column(String(500))
    overlay_path = Column(String(500))
    
    # Clinical Notes
    doctor_notes = Column(Text)
    clinical_impression = Column(Text)
    recommendations = Column(Text)
    
    # Review & Approval
    reviewed_at = Column(DateTime)
    approved_at = Column(DateTime)
    
    # Disclaimer
    disclaimer_accepted = Column(Boolean, default=False)
    disclaimer_accepted_at = Column(DateTime)
    disclaimer_accepted_by = Column(Integer, ForeignKey("users.id"))
    
    # Report
    report_generated = Column(Boolean, default=False)
    report_path = Column(String(500))
    report_generated_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="scans")
    performed_by = relationship("User", back_populates="scans_performed", foreign_keys=[performed_by_id])
    
    __table_args__ = (
        Index('ix_scan_tenant', 'tenant_id'),
        Index('ix_scan_patient', 'patient_id'),
        Index('ix_scan_date', 'created_at'),
        Index('ix_scan_status', 'status'),
    )


class Prescription(Base):
    """
    Medical prescriptions with digital signing.
    """
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant isolation
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Patient & Doctor
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Linked scan (if prescription is based on scan results)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    # Prescription Details
    prescription_number = Column(String(50), unique=True)
    
    # Medications (JSON array)
    medications = Column(JSON, nullable=False)
    # Structure: [
    #   {
    #     "name": "Tamoxifen",
    #     "dosage": "20mg",
    #     "frequency": "once daily",
    #     "duration": "5 years",
    #     "instructions": "Take with food",
    #     "quantity": 30,
    #     "refills": 11
    #   }
    # ]
    
    # Clinical Context
    diagnosis = Column(Text)
    notes = Column(Text)
    special_instructions = Column(Text)
    
    # Status & Workflow
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.DRAFT)
    
    # Digital Signature
    signed_at = Column(DateTime)
    signature_hash = Column(String(255))
    signature_image_path = Column(String(500))
    
    # Dispensing
    dispensed_at = Column(DateTime)
    dispensed_by = Column(String(255))  # Pharmacy name
    dispensing_notes = Column(Text)
    
    # PDF
    pdf_path = Column(String(500))
    pdf_generated_at = Column(DateTime)
    
    # Validity
    valid_from = Column(Date, default=func.current_date())
    valid_until = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", back_populates="prescriptions_written", foreign_keys=[doctor_id])
    
    __table_args__ = (
        Index('ix_prescription_tenant', 'tenant_id'),
        Index('ix_prescription_patient', 'patient_id'),
        Index('ix_prescription_doctor', 'doctor_id'),
    )


class Reminder(Base):
    """
    Patient reminders for medications, follow-ups, and screenings.
    """
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Tenant isolation
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    # Reminder Details
    type = Column(Enum(ReminderType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    
    # Scheduling
    trigger_time = Column(DateTime, nullable=False)
    recurrence = Column(String(50))  # "daily", "weekly", "monthly", etc.
    recurrence_end = Column(DateTime)
    
    # Delivery
    channels = Column(JSON, default=["in_app"])
    
    # Status
    is_active = Column(Boolean, default=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    
    # Related entities
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("Patient", back_populates="reminders")
    
    __table_args__ = (
        Index('ix_reminder_tenant', 'tenant_id'),
        Index('ix_reminder_patient', 'patient_id'),
        Index('ix_reminder_trigger', 'trigger_time', 'is_active', 'is_sent'),
    )


class MedicationLog(Base):
    """
    Patient medication tracking - marks when meds are taken.
    """
    __tablename__ = "medication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    
    # Medication Details
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    scheduled_time = Column(DateTime, nullable=False)
    
    # Status
    taken = Column(Boolean, default=False)
    taken_at = Column(DateTime)
    skipped = Column(Boolean, default=False)
    skip_reason = Column(String(255))
    
    # Notes
    notes = Column(Text)
    side_effects = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medication_logs")
    
    __table_args__ = (
        Index('ix_medication_log_patient', 'patient_id', 'scheduled_time'),
    )


class Notification(Base):
    """
    In-app notifications for users.
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info, warning, error, success
    
    # Action
    action_url = Column(String(500))
    action_text = Column(String(100))
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # Related entities
    related_type = Column(String(50))  # scan, appointment, prescription
    related_id = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_notification_user', 'user_id', 'is_read'),
    )


class AuditLog(Base):
    """
    Comprehensive audit logging for HIPAA compliance.
    
    Tracks all access to patient data and system changes.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Actor
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Action
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=False)  # patient, scan, prescription
    resource_id = Column(Integer)
    
    # Details
    description = Column(Text)
    old_values = Column(JSON)  # Before change
    new_values = Column(JSON)  # After change
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(100))
    
    # Request Details
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_params = Column(JSON)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('ix_audit_tenant', 'tenant_id'),
        Index('ix_audit_user', 'user_id'),
        Index('ix_audit_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_date', 'created_at'),
        Index('ix_audit_action', 'action'),
    )


class SystemSettings(Base):
    """
    Global system configuration settings.
    """
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, int, bool, json
    description = Column(Text)
    
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TenantSettings(Base):
    """
    Tenant-specific configuration settings.
    """
    __tablename__ = "tenant_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    key = Column(String(100), nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default="string")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'key', name='uq_tenant_setting'),
    )

