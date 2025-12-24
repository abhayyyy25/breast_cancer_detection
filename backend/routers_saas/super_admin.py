"""
Super Admin Router - Global Platform Management
Manages tenants (hospitals/labs) and system-wide statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import EmailStr

from database_saas import get_db
from auth_saas import require_super_admin, create_audit_log, create_user_with_credentials, hash_password, generate_username, generate_secure_password
from schemas_saas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantStats,
    SuperAdminDashboard, UserResponse, MessageResponse
)
from models_saas import (
    Tenant, User, Patient, Scan, AuditLog, SystemStatistics,
    UserRole, SubscriptionStatus
)


router = APIRouter(prefix="/super-admin", tags=["Super Admin"])


# ============================================================================
# TENANT MANAGEMENT
# ============================================================================

@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Create a new organization (Hospital/Lab) with its admin
    Only accessible by Super Admin
    """
    
    # Check if tenant with same email already exists
    existing = db.query(Tenant).filter(Tenant.contact_email == tenant_data.contact_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this email already exists"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == tenant_data.admin_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different username."
        )
    
    # Create tenant
    tenant = Tenant(
        name=tenant_data.name,
        organization_type=tenant_data.organization_type,
        contact_email=tenant_data.contact_email,
        contact_phone=tenant_data.contact_phone,
        address=tenant_data.address,
        city=tenant_data.city,
        state=tenant_data.state,
        country=tenant_data.country,
        postal_code=tenant_data.postal_code,
        monthly_scan_limit=tenant_data.monthly_scan_limit,
        subscription_status=tenant_data.subscription_status
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    # Create organization admin with manual credentials
    admin_user = User(
        username=tenant_data.admin_username,
        email=tenant_data.contact_email,
        password_hash=hash_password(tenant_data.admin_password),
        full_name=tenant_data.admin_full_name,
        role=UserRole.ORGANIZATION_ADMIN,
        tenant_id=tenant.id,
        is_active=True,
        is_verified=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Audit logs
    await create_audit_log(
        db=db,
        user=current_user,
        action="create",
        resource_type="tenant",
        resource_id=tenant.id,
        description=f"Created new organization: {tenant.name}",
        request=request
    )
    
    await create_audit_log(
        db=db,
        user=current_user,
        action="create",
        resource_type="user",
        resource_id=admin_user.id,
        description=f"Created admin for {tenant.name}: {tenant_data.admin_full_name}",
        request=request
    )
    
    return tenant


@router.get("/tenants", response_model=List[TenantResponse])
async def list_all_tenants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    List all organizations in the system
    """
    query = db.query(Tenant)
    
    if active_only:
        query = query.filter(Tenant.is_active == True)
    
    tenants = query.offset(skip).limit(limit).all()
    return tenants


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant_details(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Get detailed information about a specific tenant
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Update tenant information
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    update_data = tenant_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    tenant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tenant)
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="update",
        resource_type="tenant",
        resource_id=tenant.id,
        description=f"Updated organization: {tenant.name}",
        request=request
    )
    
    return tenant


@router.delete("/tenants/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Delete a tenant (use with extreme caution!)
    This will cascade delete all users, patients, scans, and audit logs
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    tenant_name = tenant.name
    
    # Audit log before deletion
    await create_audit_log(
        db=db,
        user=current_user,
        action="delete",
        resource_type="tenant",
        resource_id=tenant.id,
        description=f"Deleted organization: {tenant_name}",
        request=request
    )
    
    db.delete(tenant)
    db.commit()
    
    return MessageResponse(
        message=f"Organization '{tenant_name}' and all associated data deleted successfully",
        success=True
    )


@router.get("/tenants/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_statistics(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Get detailed statistics for a specific tenant
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Calculate statistics
    total_users = db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar()
    total_patients = db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar()
    total_scans = db.query(func.count(Scan.id)).filter(Scan.tenant_id == tenant_id).scalar()
    
    # Current month scans
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = db.query(func.count(Scan.id)).filter(
        and_(
            Scan.tenant_id == tenant_id,
            Scan.created_at >= first_day_of_month
        )
    ).scalar()
    
    # Active medical staff
    active_doctors = db.query(func.count(User.id)).filter(
        and_(
            User.tenant_id == tenant_id,
            User.role == UserRole.DOCTOR,
            User.is_active == True
        )
    ).scalar()
    
    active_lab_techs = db.query(func.count(User.id)).filter(
        and_(
            User.tenant_id == tenant_id,
            User.role == UserRole.LAB_TECH,
            User.is_active == True
        )
    ).scalar()
    
    return TenantStats(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        total_users=total_users,
        total_patients=total_patients,
        total_scans=total_scans,
        scans_this_month=scans_this_month,
        active_doctors=active_doctors,
        active_lab_techs=active_lab_techs
    )


# ============================================================================
# GLOBAL DASHBOARD & STATISTICS
# ============================================================================

@router.get("/dashboard", response_model=SuperAdminDashboard)
async def get_super_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Get comprehensive system-wide statistics for Super Admin dashboard
    """
    
    # Tenant statistics
    total_tenants = db.query(func.count(Tenant.id)).scalar()
    active_tenants = db.query(func.count(Tenant.id)).filter(
        and_(
            Tenant.is_active == True,
            Tenant.subscription_status == SubscriptionStatus.ACTIVE
        )
    ).scalar()
    trial_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.subscription_status == SubscriptionStatus.TRIAL
    ).scalar()
    suspended_tenants = db.query(func.count(Tenant.id)).filter(
        Tenant.subscription_status == SubscriptionStatus.SUSPENDED
    ).scalar()
    
    # User statistics
    total_users = db.query(func.count(User.id)).scalar()
    total_patients = db.query(func.count(Patient.id)).scalar()
    
    # Scan statistics
    total_scans_processed = db.query(func.count(Scan.id)).scalar()
    
    # Today's scans
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    scans_today = db.query(func.count(Scan.id)).filter(
        Scan.created_at >= today_start
    ).scalar()
    
    # This month's scans
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = db.query(func.count(Scan.id)).filter(
        Scan.created_at >= first_day_of_month
    ).scalar()
    
    # Revenue (placeholder - integrate with billing system later)
    monthly_revenue = 0.0
    total_revenue = 0.0
    
    # Recent tenants
    recent_tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).limit(5).all()
    
    # Top tenants by usage
    top_tenants_data = db.query(
        Tenant,
        func.count(Scan.id).label('scan_count')
    ).join(Scan, Tenant.id == Scan.tenant_id)\
     .group_by(Tenant.id)\
     .order_by(func.count(Scan.id).desc())\
     .limit(10)\
     .all()
    
    top_tenants_by_usage = []
    for tenant, scan_count in top_tenants_data:
        total_users_count = db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar()
        total_patients_count = db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant.id).scalar()
        
        scans_this_month_count = db.query(func.count(Scan.id)).filter(
            and_(
                Scan.tenant_id == tenant.id,
                Scan.created_at >= first_day_of_month
            )
        ).scalar()
        
        active_doctors_count = db.query(func.count(User.id)).filter(
            and_(
                User.tenant_id == tenant.id,
                User.role == UserRole.DOCTOR,
                User.is_active == True
            )
        ).scalar()
        
        active_lab_techs_count = db.query(func.count(User.id)).filter(
            and_(
                User.tenant_id == tenant.id,
                User.role == UserRole.LAB_TECH,
                User.is_active == True
            )
        ).scalar()
        
        top_tenants_by_usage.append(TenantStats(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            total_users=total_users_count,
            total_patients=total_patients_count,
            total_scans=scan_count,
            scans_this_month=scans_this_month_count,
            active_doctors=active_doctors_count,
            active_lab_techs=active_lab_techs_count
        ))
    
    return SuperAdminDashboard(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        suspended_tenants=suspended_tenants,
        total_users=total_users,
        total_patients=total_patients,
        total_scans_processed=total_scans_processed,
        scans_today=scans_today,
        scans_this_month=scans_this_month,
        monthly_revenue=monthly_revenue,
        total_revenue=total_revenue,
        recent_tenants=recent_tenants,
        top_tenants_by_usage=top_tenants_by_usage
    )


# ============================================================================
# GLOBAL USER MANAGEMENT
# ============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = None,
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    List all users across all tenants (with optional filtering)
    """
    query = db.query(User)
    
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.post("/create-org-admin/{tenant_id}", response_model=MessageResponse)
async def create_organization_admin(
    tenant_id: int,
    full_name: str,
    email: EmailStr,
    request: Request,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Create an Organization Admin for a specific tenant
    This is typically done when onboarding a new hospital/lab
    """
    from pydantic import EmailStr
    
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create organization admin
    user, plain_password = create_user_with_credentials(
        db=db,
        email=email,
        full_name=full_name,
        role=UserRole.ORGANIZATION_ADMIN,
        tenant_id=tenant_id,
        phone=phone,
        created_by_user_id=current_user.id
    )
    
    # Audit log
    await create_audit_log(
        db=db,
        user=current_user,
        action="create",
        resource_type="user",
        resource_id=user.id,
        description=f"Created Organization Admin for {tenant.name}: {full_name}",
        request=request
    )
    
    return MessageResponse(
        message=f"Organization Admin created successfully. Username: {user.username}, Password: {plain_password}",
        success=True
    )

