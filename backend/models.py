"""
Database models for Breast Cancer Detection Hospital System.

Implements a complete relational schema for:
- Users (Doctors/Lab Technicians)
- Patients
- Scans (Image analysis records)
- Audit Logs (Compliance tracking)
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles for access control."""
    DOCTOR = "doctor"
    LAB_TECH = "lab_tech"
    ADMIN = "admin"


class RiskLevel(str, enum.Enum):
    """Risk level classifications."""
    VERY_LOW = "Very Low Risk"
    LOW = "Low Risk"
    LOW_MODERATE = "Low-Moderate Risk"
    MODERATE = "Moderate Risk"
    MODERATE_HIGH = "Moderate-High Risk"
    HIGH = "High Risk"
    VERY_HIGH = "Very High Risk"


class User(Base):
    """
    User model for Doctors, Lab Technicians, and Admins.
    
    Security: Passwords are hashed using bcrypt.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DOCTOR)
    license_number = Column(String(100), unique=True, nullable=True)  # Medical license
    department = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)  # Using Integer for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    scans = relationship("Scan", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Patient(Base):
    """
    Patient model for managing patient records.
    
    HIPAA Compliance: All patient data must be handled securely.
    """
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    medical_record_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(20), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scans = relationship("Scan", back_populates="patient", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<Patient {self.medical_record_number}: {self.full_name}>"


class Scan(Base):
    """
    Scan model for storing image analysis results.
    
    Links patients with their diagnostic images and AI predictions.
    """
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Doctor who ordered/reviewed
    
    # Image storage
    image_path = Column(String(500), nullable=False)  # Path to stored image file
    original_filename = Column(String(255), nullable=True)
    
    # AI Analysis Results
    prediction_result = Column(String(50), nullable=False)  # "Malignant" or "Benign"
    confidence_score = Column(Float, nullable=False)  # Model confidence (0-1)
    malignant_probability = Column(Float, nullable=False)
    benign_probability = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    
    # Image statistics
    mean_intensity = Column(Float, nullable=True)
    std_intensity = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    contrast = Column(Float, nullable=True)
    
    # Additional metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    file_format = Column(String(20), nullable=True)
    
    # Clinical notes
    doctor_notes = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)  # AI-generated detailed findings
    
    # Report tracking
    report_generated = Column(Integer, default=0)  # Boolean as Integer
    report_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="scans")
    user = relationship("User", back_populates="scans")
    
    def __repr__(self):
        return f"<Scan {self.id}: Patient {self.patient_id}, {self.prediction_result}>"


class AuditLog(Base):
    """
    Audit log for compliance and security tracking.
    
    HIPAA/GDPR Compliance: Track all access to patient records.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True, index=True)
    
    action = Column(String(100), nullable=False)  # e.g., "VIEW_PATIENT", "CREATE_SCAN", "LOGIN"
    resource_type = Column(String(50), nullable=False)  # e.g., "patient", "scan", "auth"
    resource_id = Column(Integer, nullable=True)  # ID of the accessed resource
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)  # JSON string with additional details
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} by User {self.user_id}>"

