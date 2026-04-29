# 🚀 Quick Test Guide - Sign Up & Login Flow

## Setup (Do This First)

### Terminal 1: Start Backend
```bash
cd vantagetube-ai/backend
python -m uvicorn app.main:app --reload
```
✅ Backend runs on `http://localhost:8000`

### Terminal 2: Start Frontend
```bash
cd vantagetube-ai/frontend
# Option A: Using Python
python -m http.server 5500

# Option B: Using Node.js
npx http-server -p 5500

# Option C: Using Live Server (VS Code)
# Right-click index.html → Open with Live Server
```
✅ Frontend runs on `http://localhost:5500`

---

## Test 1: Sign Up Flow ✅

### Steps
1. Open `http://localhost:5500/auth.html`
2. Click "Create Account" tab
3. Fill in the form:
   - **Full Name**: Test User
   - **Email**: test@example.com
   - **Password**: TestPassword123!
   - **Confirm Password**: TestPassword123!
4. Click "Create Account" button

### Expected Results
- ✅ Loading spinner appears
- ✅ Success message: "Account created successfully! Redirecting..."
- ✅ After 1 second, redirects to dashboard
- ✅ Dashboard loads with welcome message
- ✅ Backend console shows: `201 Created`

### If It Fails
- Check backend is running: `curl http://localhost:8000/health`
- Check frontend is running: Open `http://localhost:5500`
- Check browser console for errors: F12 → Console tab
- Check backend console for error messages

---

## Test 2: Login Flow ✅

### Steps
1. Open `http://localhost:5500/auth.html`
2. Click "Login" tab
3. Fill in the form:
   - **Email**: test@example.com
   - **Password**: TestPassword123!
4. Click "Login" button

### Expected Results
- ✅ Loading spinner appears
- ✅ Success message: "Login successful! Redirecting..."
- ✅ After 1 second, redirects to dashboard
- ✅ Dashboard loads with welcome message
- ✅ Backend console shows: `200 OK`

### If It Fails
- Check email and password are correct
- Check backend is running
- Check browser console for errors

---

## Test 3: Dashboard Navigation ✅

### Steps
1. After logging in, you should be on dashboard
2. Click on different nav items:
   - Dashboard
   - Channel Overview
   - Video Analyzer
   - AI Generator
   - Trending Ideas
   - Profile
   - Settings

### Expected Results
- ✅ Each page loads without errors
- ✅ Navigation items highlight correctly
- ✅ No "Cannot GET" errors

---

## Test 4: Logout Flow ✅

### Steps
1. From dashboard, click "Log Out" button
2. Confirm logout

### Expected Results
- ✅ Redirects to auth page
- ✅ Token is cleared from localStorage
- ✅ Can log in again with same credentials

---

## Test 5: Protected Routes ✅

### Steps
1. Open `http://localhost:5500/pages/dashboard.html` directly (without logging in)
2. Try to access other protected pages

### Expected Results
- ✅ Should redirect to login page
- ✅ After login, should redirect back to the page you tried to access

---

## Debugging Tips

### Check Backend is Running
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","app":"VantageTube AI","version":"1.0.0"}
```

### Check Frontend is Running
```bash
curl http://localhost:5500/auth.html
# Should return HTML content
```

### Check Browser Console
1. Open DevTools: F12
2. Go to Console tab
3. Look for error messages
4. Check Network tab to see API calls

### Check Backend Console
1. Look at terminal where backend is running
2. Should see request logs
3. Should see response status codes

### Check localStorage
1. Open DevTools: F12
2. Go to Application tab
3. Click localStorage
4. Look for `auth_token` and `user_data`

---

## Common Issues & Solutions

### Issue: "Cannot GET /pages/dashboard.html"
**Solution**: This is fixed! Make sure you're using the updated `auth.js` file.

### Issue: "Cannot connect to server"
**Solution**: 
- Make sure backend is running on port 8000
- Check firewall isn't blocking port 8000
- Try: `curl http://localhost:8000/health`

### Issue: "Invalid email or password"
**Solution**:
- Make sure you registered first
- Check email and password are correct
- Try registering with a new email

### Issue: "CORS error"
**Solution**:
- Backend has CORS enabled for all origins
- This shouldn't happen, but if it does, check backend is running

### Issue: Dashboard doesn't load after login
**Solution**:
- Check browser console for errors
- Check backend console for errors
- Make sure frontend is running on correct port
- Try refreshing the page

---

## Success Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can register new account
- [ ] Account created shows 201 in backend
- [ ] Redirects to dashboard after signup
- [ ] Can login with registered credentials
- [ ] Redirects to dashboard after login
- [ ] Can navigate between pages
- [ ] Can logout
- [ ] Redirects to auth page after logout
- [ ] Can login again with same credentials

---

## Next Steps

Once all tests pass:
1. ✅ Frontend navigation is working
2. ✅ Backend API is working
3. ✅ Authentication flow is working

You can now:
- Test other features (content generation, SEO analysis, etc.)
- Deploy to production
- Add more features
- Optimize performance

---

**All tests passing? Great! Your app is working! 🎉**

