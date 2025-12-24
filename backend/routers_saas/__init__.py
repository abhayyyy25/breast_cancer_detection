"""
SaaS Multi-Tenant Routers Package
"""

from . import super_admin, hospital_admin, medical_staff, patient_portal

__all__ = ["super_admin", "hospital_admin", "medical_staff", "patient_portal"]

