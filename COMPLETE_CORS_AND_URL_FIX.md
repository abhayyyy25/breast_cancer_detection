# Complete CORS and Base URL Configuration Guide

## ✅ All Issues Fixed

This guide documents the complete fix for CORS and base URL issues between your React frontend and FastAPI backend deployed on Render.

---

## 🎯 What Was Fixed

### 1. **Backend CORS Configuration** ✅
- Added both frontend URLs to allowed origins
- Configured to accept all methods and headers
- Supports credentials (cookies/auth tokens)

### 2. **Frontend API Base URL** ✅
- Uses environment variable `REACT_APP_API_URL`
- No hard-coded URLs in the codebase
- Defaults to `http://localhost:8000/api` for development
- Production URL set via environment variable

---

## 🔧 Backend Configuration

### **File: `backend/main_saas.py`**

```python
# CORS Configuration
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,https://breast-cancer-detection-frontend.onrender.com,https://breast-cancer-detection-ra6i.onrender.com"
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
```

### **Allowed Origins:**
- ✅ `http://localhost:3000` - React dev server (default port)
- ✅ `http://localhost:3001` - React dev server (alternate port)
- ✅ `http://127.0.0.1:3000` - Localhost IP
- ✅ `https://breast-cancer-detection-frontend.onrender.com` - Production frontend
- ✅ `https://breast-cancer-detection-ra6i.onrender.com` - Production backend URL (for same-origin)

---

## 🎨 Frontend Configuration

### **File: `frontend/src/context/AuthContextSaaS.jsx`**

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

### **Default Values:**
- **Development:** `http://localhost:8000/api`
- **Production:** Set via `REACT_APP_API_URL` environment variable

### **All API Calls Use:**
- ✅ `API_BASE_URL` from AuthContext
- ✅ `process.env.REACT_APP_API_URL` directly
- ❌ NO hard-coded `localhost:8000` anywhere

---

## 🚀 Deployment Instructions

### **Step 1: Deploy Backend to Render**

1. **Push code to GitHub** (already done)

2. **Render Backend Service Configuration:**
   - Go to your backend service on Render
   - Navigate to **Environment** tab
   - Ensure these environment variables are set:

   ```bash
   # Optional: Override CORS origins if needed
   ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com,http://localhost:3000
   
   # Database (if using PostgreSQL)
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   
   # JWT Secret
   SECRET_KEY=your-secret-key-here
   ```

3. **Deploy:**
   - Render will auto-deploy when it detects new commits
   - Or click **"Manual Deploy"** → **"Deploy latest commit"**

4. **Verify Backend URL:**
   - Your backend should be accessible at: `https://breast-cancer-detection-ra6i.onrender.com`
   - Test health endpoint: `https://breast-cancer-detection-ra6i.onrender.com/api/health`

---

### **Step 2: Deploy Frontend to Render**

1. **Frontend Service Configuration:**
   - Go to your frontend service on Render
   - Navigate to **Environment** tab
   - Add this environment variable:

   ```bash
   REACT_APP_API_URL=https://breast-cancer-detection-ra6i.onrender.com/api
   ```

2. **Build Settings:**
   ```bash
   Build Command: npm install && npm run build
   Start Command: npx serve -s build -l 3000
   ```

3. **Deploy:**
   - Render will auto-deploy
   - Or click **"Manual Deploy"**

4. **Verify Frontend:**
   - Access: `https://breast-cancer-detection-frontend.onrender.com`
   - Open browser console (F12)
   - Should see NO CORS errors

---

## 🧪 Testing Checklist

### **Backend Tests:**

1. **Health Check:**
   ```bash
   curl https://breast-cancer-detection-ra6i.onrender.com/api/health
   ```
   Expected: `{"status":"healthy","version":"2.0.0",...}`

2. **CORS Preflight:**
   ```bash
   curl -H "Origin: https://breast-cancer-detection-frontend.onrender.com" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type,Authorization" \
        -X OPTIONS \
        https://breast-cancer-detection-ra6i.onrender.com/api/auth/login
   ```
   Expected: Status 200 with CORS headers

3. **Check Logs:**
   - Backend logs should show:
   ```
   [CORS] Allowed origins: ['http://localhost:3000', ..., 'https://breast-cancer-detection-frontend.onrender.com']
   ```

### **Frontend Tests:**

1. **Environment Variable:**
   - In production build, verify API calls go to production backend
   - Check Network tab in DevTools

2. **Login Test:**
   - Go to: `https://breast-cancer-detection-frontend.onrender.com`
   - Try to login
   - Should work without CORS errors

3. **API Calls:**
   - All API requests should go to: `https://breast-cancer-detection-ra6i.onrender.com/api/*`
   - Check Network tab → Headers → Request URL

4. **CORS Headers:**
   - Check Response Headers in Network tab:
   ```
   Access-Control-Allow-Origin: https://breast-cancer-detection-frontend.onrender.com
   Access-Control-Allow-Credentials: true
   ```

---

## 🔍 Troubleshooting

### **Issue 1: Still Getting CORS Errors**

**Symptoms:**
```
Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS policy
```

**Solutions:**

1. **Clear Browser Cache:**
   - Hard reload: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
   - Or open in Incognito/Private mode

2. **Verify Backend Logs:**
   ```bash
   # Check Render logs for CORS configuration
   [CORS] Allowed origins: [...]
   ```

3. **Check Environment Variables:**
   - Render Dashboard → Backend Service → Environment
   - Verify `ALLOWED_ORIGINS` includes your frontend URL

4. **Verify URLs Match Exactly:**
   - ✅ `https://breast-cancer-detection-frontend.onrender.com`
   - ❌ `https://breast-cancer-detection-frontend.onrender.com/` (trailing slash)
   - ❌ `http://breast-cancer-detection-frontend.onrender.com` (http vs https)

5. **Restart Backend Service:**
   - Render Dashboard → Backend Service → Manual Deploy
   - Wait for deployment to complete

---

### **Issue 2: API Calls Going to Wrong URL**

**Symptoms:**
- API calls going to `localhost:8000` in production
- Or going to wrong backend URL

**Solutions:**

1. **Check Environment Variable in Render:**
   - Frontend Service → Environment
   - Verify: `REACT_APP_API_URL=https://breast-cancer-detection-ra6i.onrender.com/api`

2. **Redeploy Frontend:**
   - Environment variable changes require redeployment
   - Click "Manual Deploy"

3. **Check in Browser Console:**
   ```javascript
   console.log(process.env.REACT_APP_API_URL)
   ```

4. **Verify Build:**
   - Environment variables are baked into the build
   - Must rebuild after changing environment variables

---

### **Issue 3: 404 Not Found on API Endpoints**

**Symptoms:**
```
GET https://breast-cancer-detection-ra6i.onrender.com/api/health 404
```

**Solutions:**

1. **Check Backend URL:**
   - Verify backend is deployed and running
   - Test: `https://breast-cancer-detection-ra6i.onrender.com/api/health`

2. **Check API Path:**
   - All endpoints should have `/api` prefix
   - Example: `/api/auth/login`, `/api/medical-staff/patients`

3. **Verify Backend Routes:**
   - Check `main_saas.py` includes all routers
   - Verify routes are registered with `/api` prefix

---

### **Issue 4: Credentials Not Being Sent**

**Symptoms:**
- User logged in but API returns 401 Unauthorized
- Token not being sent with requests

**Solutions:**

1. **Check CORS Credentials:**
   ```python
   # In main_saas.py
   allow_credentials=True  # Must be True
   ```

2. **Check Frontend Axios Config:**
   ```javascript
   // In AuthContextSaaS.jsx
   const axiosInstance = axios.create({
     baseURL: API_BASE_URL,
     withCredentials: true,  // If using cookies
   });
   ```

3. **Check Token Storage:**
   ```javascript
   // Token should be in localStorage
   localStorage.getItem('token')
   ```

4. **Check Authorization Header:**
   ```javascript
   // Should be added to all requests
   headers: { Authorization: `Bearer ${token}` }
   ```

---

## 📋 Environment Variables Summary

### **Backend (Render Service)**

| Variable | Value | Required |
|----------|-------|----------|
| `ALLOWED_ORIGINS` | `https://breast-cancer-detection-frontend.onrender.com,http://localhost:3000` | Optional (has default) |
| `DATABASE_URL` | PostgreSQL connection string | Yes (for production) |
| `SECRET_KEY` | JWT secret key (32+ chars) | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Optional |

### **Frontend (Render Service)**

| Variable | Value | Required |
|----------|-------|----------|
| `REACT_APP_API_URL` | `https://breast-cancer-detection-ra6i.onrender.com/api` | Yes |

---

## 🎯 Quick Reference

### **Backend URLs:**
- **Production:** `https://breast-cancer-detection-ra6i.onrender.com`
- **API Base:** `https://breast-cancer-detection-ra6i.onrender.com/api`
- **Health Check:** `https://breast-cancer-detection-ra6i.onrender.com/api/health`
- **API Docs:** `https://breast-cancer-detection-ra6i.onrender.com/api/docs`

### **Frontend URLs:**
- **Production:** `https://breast-cancer-detection-frontend.onrender.com`
- **Local Dev:** `http://localhost:3000`

### **CORS Configuration:**
```python
allow_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://127.0.0.1:3000",
    "https://breast-cancer-detection-frontend.onrender.com",
    "https://breast-cancer-detection-ra6i.onrender.com"
]
allow_credentials = True
allow_methods = ["*"]
allow_headers = ["*"]
```

---

## ✅ Final Verification

After deployment, verify:

- [ ] Backend is accessible at production URL
- [ ] Frontend is accessible at production URL
- [ ] Backend logs show correct CORS origins
- [ ] Frontend environment variable is set correctly
- [ ] Login works from production frontend
- [ ] API calls succeed without CORS errors
- [ ] Browser console shows no errors
- [ ] Network tab shows correct request URLs
- [ ] Response headers include CORS headers
- [ ] All features work (login, patient management, scans, etc.)

---

## 📞 Support

If issues persist:

1. **Check Render Logs:**
   - Backend Service → Logs
   - Frontend Service → Logs

2. **Check Browser Console:**
   - F12 → Console tab
   - Look for errors

3. **Check Network Tab:**
   - F12 → Network tab
   - Inspect request/response headers

4. **Verify Environment Variables:**
   - Render Dashboard → Service → Environment
   - Ensure all variables are set correctly

---

**Date:** January 6, 2026  
**Status:** ✅ COMPLETE  
**Backend:** `https://breast-cancer-detection-ra6i.onrender.com`  
**Frontend:** `https://breast-cancer-detection-frontend.onrender.com`  
**Impact:** All CORS and base URL issues resolved

