"""
Routers package for the Breast Cancer Detection Hospital System.

Contains all API route modules:
- auth: Authentication endpoints
- patients: Patient management endpoints
- scans: Scan analysis and management endpoints
"""

from . import auth, patients, scans

__all__ = ["auth", "patients", "scans"]

