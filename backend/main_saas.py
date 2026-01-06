"""
Multi-Tenant SaaS Platform - Main Application
Breast Cancer Detection System for PATH Labs & Hospitals
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time

from database_saas import engine, Base
from routers_saas import super_admin, hospital_admin, medical_staff, patient_portal, report_settings
from routers_saas.auth import router as auth_router


# ============================================================================
# CREATE APPLICATION
# ============================================================================

app = FastAPI(
    title="Breast Cancer Detection - Multi-Tenant SaaS Platform",
    description="Enterprise-grade AI-powered breast cancer detection system for hospitals and pathology labs",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
).split(",")

# Clean up and deduplicate origins
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring and debugging"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request (in production, use proper logging)
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "Internal server error"
        }
    )


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Authentication (Public)
app.include_router(auth_router, prefix="/api")

# Super Admin
app.include_router(super_admin.router, prefix="/api")

# Hospital/Lab Admin
app.include_router(hospital_admin.router, prefix="/api")

# Medical Staff (Doctors & Lab Techs)
app.include_router(medical_staff.router, prefix="/api")

# Patient Portal
app.include_router(patient_portal.router, prefix="/api")

# Report Settings (Medical Staff)
app.include_router(report_settings.router, prefix="/api")


# ============================================================================
# STATIC FILES (Uploads)
# ============================================================================

upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(upload_dir, exist_ok=True)

# Mount uploads directory (protected - should add auth middleware in production)
# app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "platform": "Multi-Tenant SaaS",
        "service": "Breast Cancer Detection"
    }


@app.get("/api/system-info")
async def system_info():
    """System information endpoint"""
    return {
        "application": "Breast Cancer Detection SaaS Platform",
        "version": "2.0.0",
        "architecture": "Multi-Tenant",
        "supported_roles": [
            "super_admin",
            "organization_admin",
            "doctor",
            "lab_tech",
            "patient"
        ],
        "features": [
            "Multi-tenant isolation",
            "Role-based access control",
            "AI-powered breast cancer detection",
            "Comprehensive audit logging",
            "Patient portal",
            "Report generation"
        ]
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Breast Cancer Detection - Multi-Tenant SaaS Platform",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("=" * 80)
    print("[*] Breast Cancer Detection - Multi-Tenant SaaS Platform")
    print("=" * 80)
    print("[*] Starting server...")
    
    # Import all models to ensure they're registered with Base
    from models_saas import User, Tenant, Patient, Scan, ReportSettings
    
    # Get database URL for logging
    db_url = os.getenv("DATABASE_URL", "sqlite:///./breast_cancer_saas.db")
    db_type = "PostgreSQL" if db_url.startswith("postgresql") else "SQLite"
    print(f"[*] Database: {db_type}")
    print(f"[*] CORS origins: {allowed_origins}")
    print(f"[*] Upload directory: {upload_dir}")
    print(f"[*] API Documentation: http://localhost:8001/api/docs")
    print("=" * 80)
    
    # Create tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables initialized successfully")
        print(f"[OK] Tables: {', '.join(Base.metadata.tables.keys())}")
    except Exception as e:
        print(f"[ERROR] Failed to create database tables: {e}")
        raise


# ============================================================================
# SHUTDOWN EVENT
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("=" * 80)
    print("🛑 Shutting down server...")
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_saas:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

