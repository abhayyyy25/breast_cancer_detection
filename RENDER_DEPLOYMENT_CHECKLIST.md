# Render Deployment Checklist

## ✅ Quick Deployment Guide

Follow these steps to deploy your updated code to Render with proper CORS and URL configuration.

---

## 📦 Step 1: Backend Deployment

### **1.1 Verify Environment Variables**

Go to Render Dashboard → Your Backend Service → Environment

Ensure these variables are set:

```bash
# CORS Configuration (Optional - has default)
ALLOWED_ORIGINS=https://breast-cancer-detection-frontend.onrender.com,http://localhost:3000

# Database (Required for production)
DATABASE_URL=postgresql://user:password@host:5432/database

# JWT Secret (Required)
SECRET_KEY=your-secret-key-min-32-characters-long

# Token Expiration (Optional)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### **1.2 Deploy Backend**

**Option A: Auto-Deploy (Recommended)**
- Render detects your GitHub push automatically
- Wait for "Deploy succeeded" message
- Check logs for: `[CORS] Allowed origins: [...]`

**Option B: Manual Deploy**
1. Go to Backend Service
2. Click **"Manual Deploy"**
3. Select **"Deploy latest commit"**
4. Wait for deployment to complete

### **1.3 Verify Backend**

Test these URLs in your browser or with curl:

```bash
# Health check
https://breast-cancer-detection-ra6i.onrender.com/api/health

# API docs
https://breast-cancer-detection-ra6i.onrender.com/api/docs
```

Expected response from health check:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "platform": "Multi-Tenant SaaS",
  "service": "Breast Cancer Detection"
}
```

---

## 🎨 Step 2: Frontend Deployment

### **2.1 Set Environment Variable**

Go to Render Dashboard → Your Frontend Service → Environment

Add this variable:

```bash
REACT_APP_API_URL=https://breast-cancer-detection-ra6i.onrender.com/api
```

⚠️ **IMPORTANT:** 
- Must start with `REACT_APP_`
- Must include `/api` at the end
- Use `https://` not `http://`
- No trailing slash after `/api`

### **2.2 Deploy Frontend**

**Option A: Auto-Deploy**
- Render detects environment variable change
- Automatically rebuilds and redeploys
- Wait for "Deploy succeeded"

**Option B: Manual Deploy**
1. Go to Frontend Service
2. Click **"Manual Deploy"**
3. Select **"Clear build cache & deploy"** (recommended for env changes)
4. Wait for deployment to complete

### **2.3 Verify Frontend**

Open in browser:
```
https://breast-cancer-detection-frontend.onrender.com
```

Check browser console (F12):
- ✅ Should see NO CORS errors
- ✅ API calls should go to production backend
- ✅ Login should work

---

## 🧪 Step 3: Testing

### **Test 1: CORS Headers**

Open browser DevTools (F12) → Network tab

1. Go to your frontend URL
2. Try to login
3. Check the login request:
   - Request URL: `https://breast-cancer-detection-ra6i.onrender.com/api/auth/login`
   - Response Headers should include:
     ```
     access-control-allow-origin: https://breast-cancer-detection-frontend.onrender.com
     access-control-allow-credentials: true
     ```

### **Test 2: API Calls**

Test these features:
- [ ] Login works
- [ ] Dashboard loads
- [ ] Patient list loads
- [ ] Can create new patient
- [ ] Can upload scan
- [ ] Can view patient history
- [ ] Can download reports

### **Test 3: Error Check**

Browser Console (F12) should show:
- ✅ NO CORS errors
- ✅ NO 404 errors on API calls
- ✅ NO "Failed to fetch" errors
- ✅ Successful API responses

---

## 🔍 Troubleshooting

### **Issue: CORS Error Still Appears**

```
Access to fetch at '...' has been blocked by CORS policy
```

**Solution:**
1. Clear browser cache: `Ctrl + Shift + Delete`
2. Hard reload: `Ctrl + Shift + R`
3. Try incognito mode
4. Check backend logs show correct CORS origins
5. Verify backend deployed successfully
6. Restart backend service if needed

---

### **Issue: API Calls Go to localhost**

```
Failed to fetch http://localhost:8000/api/...
```

**Solution:**
1. Check frontend environment variable is set:
   ```bash
   REACT_APP_API_URL=https://breast-cancer-detection-ra6i.onrender.com/api
   ```
2. Redeploy frontend (env changes require rebuild)
3. Clear browser cache
4. Hard reload page

---

### **Issue: 404 Not Found**

```
GET https://breast-cancer-detection-ra6i.onrender.com/api/health 404
```

**Solution:**
1. Verify backend is running (check Render dashboard)
2. Check backend logs for errors
3. Verify backend URL is correct
4. Test API docs URL: `/api/docs`

---

### **Issue: 401 Unauthorized**

```
POST /api/auth/login 401
```

**Solution:**
1. Check credentials are correct
2. Verify database is accessible
3. Check backend logs for authentication errors
4. Ensure SECRET_KEY is set in backend environment

---

## 📋 Deployment Checklist

Before marking deployment as complete:

### Backend:
- [ ] Code pushed to GitHub
- [ ] Backend service deployed on Render
- [ ] Environment variables configured
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] Logs show correct CORS origins
- [ ] Database connected (if using PostgreSQL)

### Frontend:
- [ ] Code pushed to GitHub
- [ ] Frontend service deployed on Render
- [ ] `REACT_APP_API_URL` environment variable set
- [ ] Build completed successfully
- [ ] Frontend loads in browser
- [ ] No console errors
- [ ] API calls go to production backend

### Testing:
- [ ] Login works
- [ ] No CORS errors
- [ ] All features functional
- [ ] Network tab shows correct URLs
- [ ] Response headers include CORS headers
- [ ] Tested in multiple browsers
- [ ] Tested on mobile (if applicable)

---

## 🎯 Quick Commands

### Check Backend Logs:
```bash
# In Render Dashboard
Backend Service → Logs → View recent logs
```

### Check Frontend Logs:
```bash
# In Render Dashboard
Frontend Service → Logs → View recent logs
```

### Test Backend Health:
```bash
curl https://breast-cancer-detection-ra6i.onrender.com/api/health
```

### Test CORS:
```bash
curl -H "Origin: https://breast-cancer-detection-frontend.onrender.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://breast-cancer-detection-ra6i.onrender.com/api/auth/login
```

---

## 📞 Support Resources

- **Render Documentation:** https://render.com/docs
- **CORS Guide:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- **React Environment Variables:** https://create-react-app.dev/docs/adding-custom-environment-variables/

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ Backend accessible at production URL
2. ✅ Frontend accessible at production URL
3. ✅ No CORS errors in browser console
4. ✅ Login works from production frontend
5. ✅ All API calls succeed
6. ✅ All features work as expected
7. ✅ Network tab shows correct request URLs
8. ✅ Response headers include CORS headers

---

**Last Updated:** January 6, 2026  
**Status:** Ready for Deployment  
**Commit:** c19a04f

