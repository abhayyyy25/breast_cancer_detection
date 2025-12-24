# 🏥 Breast Cancer Detection - Multi-Tenant SaaS Platform

## 🎯 Overview

A **Professional Multi-Tenant SaaS Platform** for AI-powered breast cancer detection, designed for hospitals, pathology labs, and diagnostic centers.

---

## ✨ Key Features

### 🏢 **Multi-Tenancy**
- Complete data isolation per organization
- Subscription-based access control
- Usage tracking and limits
- Custom branding per tenant

### 👥 **Role-Based Access**
- **Super Admin**: Platform management
- **Organization Admin**: Tenant management
- **Doctor**: Medical staff access
- **Lab Tech**: Technician access
- **Patient**: Personal health dashboard

### 🎨 **Professional Dashboards**
- Modern, responsive UI
- Real-time analytics
- Interactive data visualization
- Mobile-friendly design

### 🔒 **Security & Compliance**
- HIPAA-compliant audit logging
- GDPR-ready data management
- JWT authentication
- Role-based permissions

---

## 🚀 Quick Start

### **1. Initialize Database**

```powershell
cd backend
python init_db_saas.py --with-sample
```

### **2. Start Backend**

```powershell
cd backend
python -m uvicorn main_saas:app --reload --host 0.0.0.0 --port 8001
```

### **3. Start Frontend**

```powershell
cd frontend
npm start
```

### **4. Access Application**

Open browser: `http://localhost:3000`

---

## 🔐 Default Credentials

### **Super Admin**
```
Username: superadmin
Password: SuperAdmin@123
```

### **Hospital Admin** (Apollo Hospitals)
```
Username: admin.apollo
Password: Apollo@123
```

### **Doctor** (Apollo)
```
Username: dr.rajesh.sharma
Password: Doctor@123
```

### **Patient** (Apollo)
```
Username: priya.patel
Password: Patient@123
```

⚠️ **Change all passwords before production use!**

---

## 📊 What's Included

### **Backend (SaaS Version)**
- ✅ Multi-tenant database models
- ✅ Role-based API endpoints
- ✅ Subscription management
- ✅ Audit logging
- ✅ JWT authentication

### **Frontend (SaaS Version)**
- ✅ Super Admin Dashboard
- ✅ Hospital Admin Dashboard
- ✅ Patient Dashboard (NEW!)
- ✅ Responsive design
- ✅ Modern UI/UX

### **Sample Data**
- ✅ 2 Tenants (Apollo Hospitals, Dr. Lal PathLabs)
- ✅ 5 Users (Admins, Doctors, Lab Techs)
- ✅ 3 Patients with medical records

---

## 📁 Project Structure

```
BreastCancerDetect_updated-main/
├── backend/
│   ├── main_saas.py              # SaaS application
│   ├── models_saas.py            # Multi-tenant models
│   ├── database_saas.py          # Database config
│   ├── init_db_saas.py           # Database initialization
│   ├── routers_saas/             # API endpoints
│   │   ├── auth.py
│   │   ├── super_admin.py
│   │   ├── hospital_admin.py
│   │   ├── medical_staff.py
│   │   └── patient_portal.py
│   └── breast_cancer_saas.db     # SQLite database
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SuperAdminDashboard.js
│   │   │   ├── HospitalAdminDashboard.js
│   │   │   ├── PatientDashboard.js    # NEW!
│   │   │   └── ...
│   │   ├── context/
│   │   │   ├── AuthContextSaaS.js
│   │   │   └── ThemeContext.js
│   │   └── theme/
│   │       └── colors.js
│   └── .env                      # API configuration
│
├── SAAS_IMPLEMENTATION_GUIDE.md  # Full documentation
├── QUICK_START.md                # Quick start guide
├── IMPLEMENTATION_COMPLETE.md    # Implementation summary
└── README_SAAS.md                # This file
```

---

## 🎨 Screenshots

### **Super Admin Dashboard**
- View all tenants
- Platform analytics
- Subscription management
- System health monitoring

### **Hospital Admin Dashboard**
- Staff management
- Patient registration
- Usage tracking
- Recent activity

### **Patient Dashboard** (NEW!)
- Personal scan history
- Report downloads
- Profile management
- Health summary

---

## 📖 Documentation

### **Comprehensive Guides**
- **`SAAS_IMPLEMENTATION_GUIDE.md`**: Complete implementation details
- **`QUICK_START.md`**: Get started in 5 minutes
- **`IMPLEMENTATION_COMPLETE.md`**: What's been implemented

### **API Documentation**
- **Swagger UI**: `http://localhost:8001/api/docs`
- **ReDoc**: `http://localhost:8001/api/redoc`

---

## 🔧 Configuration

### **Backend Configuration**
File: `backend/.env` (optional)

```env
DATABASE_URL=sqlite:///./breast_cancer_saas.db
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000
```

### **Frontend Configuration**
File: `frontend/.env`

```env
REACT_APP_API_URL=http://localhost:8001/api
```

---

## 🧪 Testing

### **Test Super Admin**
1. Login as `superadmin`
2. Create a new tenant
3. View platform analytics

### **Test Hospital Admin**
1. Login as `admin.apollo`
2. Add a new doctor
3. Register a new patient

### **Test Patient**
1. Login as `priya.patel`
2. View scan history
3. Download reports

---

## 🚀 Deployment

### **Development**
```bash
# Backend
cd backend
python -m uvicorn main_saas:app --reload --port 8001

# Frontend
cd frontend
npm start
```

### **Production** (Example: AWS)
```bash
# Backend (EC2 + RDS PostgreSQL)
gunicorn main_saas:app --workers 4 --bind 0.0.0.0:8001

# Frontend (S3 + CloudFront)
npm run build
aws s3 sync build/ s3://your-bucket/
```

---

## 📊 Database Schema

### **Key Tables**
- `tenants`: Organizations (Hospitals/Labs)
- `users`: All user roles with tenant isolation
- `patients`: Patient records per tenant
- `scans`: Scan results per tenant
- `audit_logs`: HIPAA-compliant logging

---

## 🔒 Security Features

- ✅ JWT Authentication
- ✅ Password Hashing (bcrypt)
- ✅ Role-Based Access Control
- ✅ Tenant Data Isolation
- ✅ Audit Logging
- ✅ CORS Protection
- ✅ SQL Injection Prevention

---

## 📈 Subscription Management

### **Plans** (Example)
- **Trial**: 50 scans/month, Free, 30 days
- **Starter**: 100 scans/month, ₹4,999/month
- **Professional**: 500 scans/month, ₹19,999/month
- **Enterprise**: Unlimited, Custom pricing

### **Ready for Integration**
- Stripe/Razorpay webhooks
- Invoice generation
- Payment history
- Automatic renewal

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Validation**: Pydantic

### **Frontend**
- **Framework**: React 18
- **Routing**: React Router v6
- **State Management**: Context API
- **Styling**: CSS Modules
- **HTTP Client**: Axios

---

## 📞 Support

- **Email**: support@yourcompany.com
- **Documentation**: See `SAAS_IMPLEMENTATION_GUIDE.md`
- **API Docs**: `http://localhost:8001/api/docs`

---

## 🎯 Roadmap

### **Completed** ✅
- [x] Multi-tenant architecture
- [x] Role-based access control
- [x] Super Admin Dashboard
- [x] Hospital Admin Dashboard
- [x] Patient Dashboard
- [x] Subscription management
- [x] Audit logging

### **Upcoming** 🚧
- [ ] Multi-Factor Authentication (MFA)
- [ ] Billing integration (Stripe/Razorpay)
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Appointment scheduling
- [ ] Mobile app (React Native)

---

## 📄 License

Proprietary - All Rights Reserved

---

## 🙏 Acknowledgments

Built with ❤️ for Healthcare Professionals

**Ready to Save Lives! 🏥✨**

---

## 📝 Changelog

### **Version 2.0.0** (Current)
- ✅ Multi-tenant SaaS architecture
- ✅ Professional dashboards for all roles
- ✅ Patient Dashboard with personal health tracking
- ✅ Subscription and usage management
- ✅ HIPAA-compliant audit logging
- ✅ Modern, responsive UI

### **Version 1.0.0** (Previous)
- Basic single-tenant system
- Admin and doctor roles only
- Simple patient management
- Basic AI analysis

---

**For detailed implementation guide, see `SAAS_IMPLEMENTATION_GUIDE.md`**

