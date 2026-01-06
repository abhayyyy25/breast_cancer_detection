# CORS Fix - Deployment Guide

## ✅ Issue Fixed

**Problem:** Frontend deployed on `https://breast-cancer-detection-frontend.onrender.com` was blocked by CORS policy when making requests to the backend API.

**Solution:** Added production frontend URL to the allowed CORS origins.

---

## 🔧 Changes Made

### 1. Updated `backend/main_saas.py`

```python
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,https://breast-cancer-detection-frontend.onrender.com"
).split(",")
```

**What this does:**
- Allows requests from localhost (development)
- Allows requests from your production frontend on Render
- Can be overridden by setting the `ALLOWED_ORIGINS` environment variable

---

## 🚀 Deployment Instructions

### **Option 1: Using Default Configuration (Recommended)**

The backend code now includes your production URL by default. Simply:

1. **Deploy the updated backend code**
2. **Restart your backend service** on Render/Railway/Heroku
3. ✅ CORS errors should be resolved!

---

### **Option 2: Using Environment Variables (More Flexible)**

If you want to manage CORS origins via environment variables:

#### **For Render.com:**

1. Go to your backend service dashboard
2. Navigate to **Environment** section
3. Add a new environment variable:
   ```
   Key: ALLOWED_ORIGINS
   Value: https://breast-cancer-detection-frontend.onrender.com,https://your-custom-domain.com
   ```
4. Click **Save Changes**
5. Render will automatically redeploy

#### **For Railway:**

1. Open your backend project
2. Go to **Variables** tab
3. Add new variable:
   ```
   ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com
   ```
4. Railway will auto-redeploy

#### **For Heroku:**

```bash
heroku config:set ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com -a your-app-name
```

---

## 🔍 Verify CORS Configuration

After deployment, check the backend logs. You should see:

```
[CORS] Allowed origins: ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'https://breast-cancer-detection-frontend.onrender.com']
```

---

## 🌐 Multiple Frontend Domains

If you have multiple frontend deployments (staging, production, custom domains), add them all:

```bash
# Environment Variable Format
ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com,https://staging.yourdomain.com,https://www.yourdomain.com
```

---

## 🔒 Security Notes

### ✅ **DO THIS:**
- ✅ List specific domains (e.g., `https://your-frontend.com`)
- ✅ Use HTTPS in production
- ✅ Keep the list minimal (only trusted domains)

### ❌ **AVOID THIS:**
- ❌ Using `*` (wildcard) in production
- ❌ Using `http://` in production (use `https://`)
- ❌ Adding untrusted domains

---

## 🧪 Testing CORS After Deployment

### Test 1: Browser Console
Open your frontend in browser and check console for CORS errors:
```
✅ Should see successful API calls
❌ Should NOT see: "blocked by CORS policy"
```

### Test 2: Network Tab
1. Open DevTools → Network tab
2. Make an API request (e.g., login)
3. Check Response Headers should include:
   ```
   Access-Control-Allow-Origin: https://breast-cancer-detection-frontend.onrender.com
   Access-Control-Allow-Credentials: true
   ```

### Test 3: curl Command
```bash
curl -H "Origin: https://breast-cancer-detection-frontend.onrender.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://your-backend-api.com/api/health
```

Should return status `200` with CORS headers.

---

## 🐛 Troubleshooting

### **Still Getting CORS Errors?**

1. **Clear browser cache and hard reload** (`Ctrl + Shift + R`)

2. **Check environment variables:**
   ```bash
   # On your backend server
   echo $ALLOWED_ORIGINS
   ```

3. **Check backend logs for CORS configuration:**
   Look for: `[CORS] Allowed origins: [...]`

4. **Verify frontend URL is exact:**
   - ✅ `https://breast-cancer-detection-frontend.onrender.com`
   - ❌ `https://breast-cancer-detection-frontend.onrender.com/` (trailing slash)
   - ❌ `http://breast-cancer-detection-frontend.onrender.com` (http vs https)

5. **Check for subdomain/www:**
   - If frontend is at `www.yourdomain.com`, add both:
     ```
     ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
     ```

6. **Backend not restarted:**
   - Make sure to redeploy or restart the backend service
   - Changes only take effect after restart

---

## 📝 Current CORS Configuration

**Allowed Origins (Default):**
- ✅ `http://localhost:3000` (React dev server)
- ✅ `http://localhost:3001` (Alternate port)
- ✅ `http://127.0.0.1:3000` (Localhost IP)
- ✅ `https://breast-cancer-detection-frontend.onrender.com` (Production)

**CORS Settings:**
- ✅ `allow_credentials: true` (cookies/auth supported)
- ✅ `allow_methods: ["*"]` (all HTTP methods)
- ✅ `allow_headers: ["*"]` (all headers)
- ✅ `expose_headers: ["*"]` (all response headers)

---

## 🔄 Updating CORS Origins Later

### **Adding a New Frontend Domain:**

1. **Via Code** (if you have backend access):
   ```python
   # In main_saas.py, update the default value
   allowed_origins = os.getenv(
       "ALLOWED_ORIGINS",
       "...,https://new-domain.com"
   ).split(",")
   ```
   Then commit, push, and redeploy.

2. **Via Environment Variable** (recommended):
   ```bash
   # Add to existing origins
   ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com,https://new-domain.com
   ```
   Update on Render/Railway/Heroku dashboard.

---

## ✅ Checklist

Before deploying to production:

- [ ] Updated `main_saas.py` with production frontend URL
- [ ] Committed and pushed changes to git
- [ ] Deployed backend with new CORS configuration
- [ ] Restarted backend service
- [ ] Tested API calls from frontend
- [ ] Verified no CORS errors in browser console
- [ ] Checked backend logs show correct origins
- [ ] Tested with actual login/API requests
- [ ] Confirmed HTTPS is used (not HTTP)

---

## 📞 Support

If you continue experiencing CORS issues:

1. Check backend logs for `[CORS] Allowed origins`
2. Verify frontend URL matches exactly
3. Clear browser cache completely
4. Try in incognito/private mode
5. Check if backend is publicly accessible

---

**Date:** January 6, 2026  
**Status:** ✅ CORS Configuration Updated  
**Impact:** Production frontend can now communicate with backend API

