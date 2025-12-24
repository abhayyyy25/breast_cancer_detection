"""
Super Admin Router

Platform-wide management endpoints for Super Administrators.

Endpoints:
- GET /super-admin/dashboard: Global statistics
- GET /super-admin/tenants: List all organizations
- POST /super-admin/tenants: Onboard new organization
- GET /super-admin/tenants/{id}: Get tenant details
- PUT /super-admin/tenants/{id}: Update tenant
- DELETE /super-admin/tenants/{id}: Deactivate tenant
- GET /super-admin/audit-logs: View system-wide audit logs
- GET /super-admin/system-stats: System health & usage

Author: Enterprise Healthcare SaaS Platform
Version: 3.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database_enterprise import get_db
from models_enterprise import (
    Tenant, User, Patient, Scan, AuditLog,
    UserRole, TenantType, SubscriptionStatus, SubscriptionPlan, AuditAction
)
from schemas_enterprise import (
    TenantCreate, TenantUpdate, TenantResponse, TenantStats,
    TenantListResponse, OnboardTenantRequest, OnboardTenantResponse,
    SuperAdminDashboard, AuditLogResponse, AuditLogListResponse,
    AuditLogFilter, UserCreateResponse, PaginationParams
)
from auth_enterprise import (
    get_super_admin, log_audit, get_client_ip, get_user_agent,
    get_password_hash, generate_secure_password, generate_username,
    create_user_for_tenant
)

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


# ==================== DASHBOARD ====================

@router.get("/dashboard", response_model=SuperAdminDashboard)
async def get_super_admin_dashboard(
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Get global platform statistics for Super Admin dashboard.
    
    Returns:
    - Tenant counts by status and plan
    - User and patient totals
    - Scan counts and trends
    - Revenue metrics (mocked)
    """
    # Tenant statistics
    total_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.is_deleted == False
    ).scalar()
    
    active_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.is_active == True,
        Tenant.is_deleted == False
    ).scalar()
    
    trial_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.subscription_status == SubscriptionStatus.TRIAL,
        Tenant.is_deleted == False
    ).scalar()
    
    # User and patient counts
    total_users = db.query(func.count(User.id)).filter(
        User.is_deleted == False
    ).scalar()
    
    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.is_deleted == False
    ).scalar()
    
    # Scan statistics
    total_scans = db.query(func.count(Scan.id)).scalar()
    
    this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    scans_this_month = db.query(func.count(Scan.id)).filter(
        Scan.created_at >= this_month_start
    ).scalar()
    
    # Tenants by plan
    tenants_by_plan = {}
    for plan in SubscriptionPlan:
        count = db.query(func.count(Tenant.id)).filter(
            Tenant.subscription_plan == plan,
            Tenant.is_deleted == False
        ).scalar()
        tenants_by_plan[plan.value] = count
    
    # Scans by day (last 7 days)
    scans_by_day = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(func.count(Scan.id)).filter(
            Scan.created_at >= day_start,
            Scan.created_at < day_end
        ).scalar()
        
        scans_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    scans_by_day.reverse()
    
    # Recent tenants
    recent_tenants_query = db.query(Tenant).filter(
        Tenant.is_deleted == False
    ).order_by(Tenant.created_at.desc()).limit(5).all()
    
    recent_tenants = []
    for tenant in recent_tenants_query:
        user_count = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant.id
        ).scalar()
        patient_count = db.query(func.count(Patient.id)).filter(
            Patient.tenant_id == tenant.id
        ).scalar()
        scan_count = db.query(func.count(Scan.id)).filter(
            Scan.tenant_id == tenant.id
        ).scalar()
        
        recent_tenants.append(TenantStats(
            id=tenant.id,
            name=tenant.name,
            type=tenant.type,
            subscription_status=tenant.subscription_status,
            subscription_plan=tenant.subscription_plan,
            user_count=user_count,
            patient_count=patient_count,
            scan_count=scan_count,
            monthly_scans=tenant.current_month_scans,
            created_at=tenant.created_at
        ))
    
    # Mock revenue (in production, integrate with payment system)
    revenue_this_month = len([t for t in tenants_by_plan if tenants_by_plan[t] > 0]) * 500.0
    
    return SuperAdminDashboard(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        total_users=total_users,
        total_patients=total_patients,
        total_scans=total_scans,
        scans_this_month=scans_this_month,
        revenue_this_month=revenue_this_month,
        tenants_by_plan=tenants_by_plan,
        scans_by_day=scans_by_day,
        recent_tenants=recent_tenants
    )


# ==================== TENANT MANAGEMENT ====================

@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[SubscriptionStatus] = None,
    plan: Optional[SubscriptionPlan] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    List all tenants (organizations) with pagination and filtering.
    """
    query = db.query(Tenant).filter(Tenant.is_deleted == False)
    
    # Apply filters
    if status:
        query = query.filter(Tenant.subscription_status == status)
    if plan:
        query = query.filter(Tenant.subscription_plan == plan)
    if search:
        query = query.filter(
            Tenant.name.ilike(f"%{search}%") |
            Tenant.email.ilike(f"%{search}%")
        )
    
    # Get total count
    total = query.count()
    
    # Pagination
    skip = (page - 1) * page_size
    tenants = query.order_by(Tenant.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Build response with stats
    items = []
    for tenant in tenants:
        user_count = db.query(func.count(User.id)).filter(
            User.tenant_id == tenant.id
        ).scalar()
        patient_count = db.query(func.count(Patient.id)).filter(
            Patient.tenant_id == tenant.id
        ).scalar()
        scan_count = db.query(func.count(Scan.id)).filter(
            Scan.tenant_id == tenant.id
        ).scalar()
        
        items.append(TenantStats(
            id=tenant.id,
            name=tenant.name,
            type=tenant.type,
            subscription_status=tenant.subscription_status,
            subscription_plan=tenant.subscription_plan,
            user_count=user_count,
            patient_count=patient_count,
            scan_count=scan_count,
            monthly_scans=tenant.current_month_scans,
            created_at=tenant.created_at
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return TenantListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.post("/tenants/onboard", response_model=OnboardTenantResponse)
async def onboard_new_tenant(
    request: Request,
    onboard_data: OnboardTenantRequest,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Onboard a new hospital/organization.
    
    Creates:
    1. New Tenant record
    2. Org Admin user with auto-generated credentials
    
    Returns credentials for sharing with the new org admin.
    """
    # Check if organization email already exists
    existing_tenant = db.query(Tenant).filter(
        Tenant.email == onboard_data.organization_email
    ).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this email already exists"
        )
    
    # Check if admin email already exists
    existing_user = db.query(User).filter(
        User.email == onboard_data.admin_email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create tenant
    trial_end = datetime.utcnow() + timedelta(days=14)
    
    tenant = Tenant(
        name=onboard_data.organization_name,
        type=onboard_data.organization_type,
        email=onboard_data.organization_email,
        phone=onboard_data.organization_phone,
        address_line1=onboard_data.address_line1,
        city=onboard_data.city,
        state=onboard_data.state,
        postal_code=onboard_data.postal_code,
        country=onboard_data.country,
        subscription_status=SubscriptionStatus.TRIAL,
        subscription_plan=onboard_data.subscription_plan,
        trial_ends_at=trial_end,
        hipaa_baa_signed=onboard_data.accept_hipaa_baa,
        hipaa_baa_signed_at=datetime.utcnow() if onboard_data.accept_hipaa_baa else None,
    )
    
    db.add(tenant)
    db.flush()  # Get tenant ID
    
    # Create org admin user
    admin_user, temp_password = await create_user_for_tenant(
        db=db,
        tenant_id=tenant.id,
        email=onboard_data.admin_email,
        full_name=onboard_data.admin_name,
        role=UserRole.ORG_ADMIN,
        created_by=current_user.id
    )
    
    db.commit()
    
    # Log tenant creation
    log_audit(
        db=db,
        action=AuditAction.CREATE,
        resource_type="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        description=f"Onboarded new tenant: {tenant.name}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return OnboardTenantResponse(
        tenant=TenantResponse.model_validate(tenant),
        admin_user=UserCreateResponse(
            id=admin_user.id,
            username=admin_user.username,
            email=admin_user.email,
            temporary_password=temp_password,
            full_name=admin_user.full_name,
            role=admin_user.role,
            message="Credentials generated. Share securely with the organization admin."
        ),
        message=f"Successfully onboarded {tenant.name}. Admin credentials generated."
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """Get tenant details by ID."""
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_deleted == False
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.model_validate(tenant)


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    request: Request,
    tenant_id: int,
    update_data: TenantUpdate,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """Update tenant information."""
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_deleted == False
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    old_values = {k: getattr(tenant, k) for k in update_dict.keys()}
    
    for field, value in update_dict.items():
        setattr(tenant, field, value)
    
    db.commit()
    db.refresh(tenant)
    
    log_audit(
        db=db,
        action=AuditAction.UPDATE,
        resource_type="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        description=f"Updated tenant: {tenant.name}",
        old_values=old_values,
        new_values=update_dict,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return TenantResponse.model_validate(tenant)


@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant(
    request: Request,
    tenant_id: int,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate (soft delete) a tenant.
    
    Does not delete data - marks as inactive.
    """
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_deleted == False
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    tenant.is_active = False
    tenant.is_deleted = True
    tenant.deleted_at = datetime.utcnow()
    
    db.commit()
    
    log_audit(
        db=db,
        action=AuditAction.DELETE,
        resource_type="tenant",
        resource_id=tenant.id,
        user_id=current_user.id,
        description=f"Deactivated tenant: {tenant.name}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=True
    )
    
    return {"message": f"Tenant '{tenant.name}' has been deactivated"}


# ==================== AUDIT LOGS ====================

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_system_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    View system-wide audit logs.
    
    Super Admin can view all audit entries across all tenants.
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if tenant_id:
        query = query.filter(AuditLog.tenant_id == tenant_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    
    skip = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(page_size).all()
    
    items = []
    for log in logs:
        user_name = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            user_name = user.full_name if user else None
        
        items.append(AuditLogResponse(
            id=log.id,
            uuid=log.uuid,
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            user_name=user_name,
            action=log.action.value if log.action else None,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=log.description,
            ip_address=log.ip_address,
            success=log.success,
            created_at=log.created_at
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


# ==================== SYSTEM STATS ====================

@router.get("/system-stats")
async def get_system_statistics(
    current_user: User = Depends(get_super_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed system health and usage statistics.
    """
    # Database stats
    db_stats = {
        "tenants": db.query(func.count(Tenant.id)).scalar(),
        "users": db.query(func.count(User.id)).scalar(),
        "patients": db.query(func.count(Patient.id)).scalar(),
        "scans": db.query(func.count(Scan.id)).scalar(),
        "audit_entries": db.query(func.count(AuditLog.id)).scalar(),
    }
    
    # Subscription breakdown
    subscription_stats = {}
    for status in SubscriptionStatus:
        subscription_stats[status.value] = db.query(func.count(Tenant.id)).filter(
            Tenant.subscription_status == status
        ).scalar()
    
    # Activity (last 24 hours)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    activity_stats = {
        "logins": db.query(func.count(AuditLog.id)).filter(
            AuditLog.action == AuditAction.LOGIN,
            AuditLog.created_at >= last_24h
        ).scalar(),
        "scans_analyzed": db.query(func.count(Scan.id)).filter(
            Scan.created_at >= last_24h
        ).scalar(),
        "new_patients": db.query(func.count(Patient.id)).filter(
            Patient.created_at >= last_24h
        ).scalar(),
    }
    
    return {
        "database": db_stats,
        "subscriptions": subscription_stats,
        "activity_24h": activity_stats,
        "system_health": "operational",
        "api_version": "3.0.0"
    }

