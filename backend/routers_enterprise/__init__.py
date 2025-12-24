"""
Enterprise Healthcare SaaS API Routers

Modular router organization:
- auth.py: Authentication endpoints
- super_admin.py: Platform management (Super Admin)
- org_admin.py: Organization management (Org Admin)
- medical.py: Medical workflows (Doctors, Lab Techs)
- patient_portal.py: Patient self-service
- common.py: Shared endpoints
"""

from .auth import router as auth_router
from .super_admin import router as super_admin_router
from .org_admin import router as org_admin_router
from .medical import router as medical_router
from .patient_portal import router as patient_portal_router

__all__ = [
    "auth_router",
    "super_admin_router", 
    "org_admin_router",
    "medical_router",
    "patient_portal_router"
]

