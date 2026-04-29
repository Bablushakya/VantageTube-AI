# VantageTube AI - API Testing Guide

## Overview

Your VantageTube backend has **6 main API modules** with **40+ endpoints** covering:
- Authentication & User Management
- Content Generation (AI-powered)
- SEO Analysis
- Trending Topics
- YouTube Integration

---

## Quick Start

### Option 1: Import Postman Collection (Recommended)

1. **Open Postman** → Click "Import"
2. **Select file**: `VantageTube_API_Collection.postman_collection.json`
3. **Create Environment** with variables:
   - `base_url`: `http://localhost:8000/api`
   - `access_token`: (will be filled after login)

### Option 2: Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "confirm_password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

---

## API Modules Breakdown

### 1. Authentication (`/auth`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/auth/register` | POST | ❌ | Create new user account |
| `/auth/login` | POST | ❌ | Get access token |
| `/auth/me` | GET | ✅ | Get current user profile |
| `/auth/check` | GET | ✅ | Verify token validity |
| `/auth/refresh` | POST | ✅ | Refresh access token |
| `/auth/logout` | POST | ✅ | Logout user |

**Test Flow:**
1. Register → Get user ID
2. Login → Get access token
3. Use token for all other requests

---

### 2. Users (`/users`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/users/me` | GET | ✅ | Get user profile |
| `/users/me` | PUT | ✅ | Update profile |
| `/users/change-password` | POST | ✅ | Change password |
| `/users/avatar` | POST | ✅ | Upload avatar |
| `/users/avatar` | DELETE | ✅ | Delete avatar |
| `/users/settings` | GET | ✅ | Get user settings |
| `/users/settings` | PUT | ✅ | Update settings |

**Settings Include:**
- Theme (dark/light)
- Notifications (email, weekly reports, alerts)
- Privacy (profile visibility, analytics sharing)

---

### 3. Content Generation (`/content`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/content/generate/titles` | POST | ✅ | Generate video titles (AI) |
| `/content/generate/description` | POST | ✅ | Generate video description (AI) |
| `/content/generate/tags` | POST | ✅ | Generate video tags (AI) |
| `/content/generate/thumbnail-text` | POST | ✅ | Generate thumbnail text (AI) |
| `/content/history` | GET | ✅ | Get generation history |
| `/content/history/{id}` | GET | ✅ | Get specific content |
| `/content/history/{id}` | DELETE | ✅ | Delete content |
| `/content/stats` | GET | ✅ | Get generation stats |

**Example Request (Generate Titles):**
```json
{
  "topic": "How to learn Python programming",
  "keywords": ["python", "programming", "tutorial"],
  "tone": "educational",
  "target_audience": "beginners",
  "count": 5
}
```

---

### 4. SEO Analysis (`/seo`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/seo/analyze` | POST | ✅ | Analyze video SEO |
| `/seo/videos/{id}/reports` | GET | ✅ | Get SEO reports history |
| `/seo/dashboard/stats` | GET | ✅ | Get SEO dashboard stats |

**Analysis Includes:**
- Title optimization (length, keywords, power words)
- Description optimization (links, timestamps, CTAs)
- Tags optimization (count, relevance)
- Thumbnail optimization
- Engagement metrics
- Overall score (0-100) + grade

---

### 5. Trending Topics (`/trending`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/trending/fetch` | POST | ✅ | Fetch trending videos from YouTube |
| `/trending/filter` | POST | ✅ | Filter trending videos |
| `/trending/videos/{id}/analyze` | GET | ✅ | Analyze trending video |
| `/trending/stats` | GET | ✅ | Get trending statistics |
| `/trending/dashboard` | GET | ✅ | Get trending dashboard |
| `/trending/opportunities` | GET | ✅ | Get content opportunities |
| `/trending/categories` | GET | ✅ | Get YouTube categories |
| `/trending/regions` | GET | ✅ | Get supported regions |

**Supported Regions:** US, GB, CA, AU, IN, DE, FR, JP, KR, BR, MX, ES, IT, RU, NL

---

### 6. YouTube Integration (`/youtube`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/youtube/oauth/authorize` | GET | ✅ | Start OAuth flow |
| `/youtube/oauth/callback` | GET | ✅ | Handle OAuth callback |
| `/youtube/channels` | GET | ✅ | Get connected channels |
| `/youtube/channels/{id}/sync` | POST | ✅ | Sync channel videos |
| `/youtube/channels/{id}/videos` | GET | ✅ | Get channel videos |
| `/youtube/channels/{id}` | DELETE | ✅ | Disconnect channel |

---

## Testing Checklist

### Phase 1: Authentication ✅
- [ ] Register new user
- [ ] Login with credentials
- [ ] Get current user profile
- [ ] Check auth status
- [ ] Refresh token
- [ ] Logout

### Phase 2: User Management ✅
- [ ] Get user profile
- [ ] Update profile (name, niche, bio)
- [ ] Change password
- [ ] Get user settings
- [ ] Update settings (theme, notifications)
- [ ] Upload avatar
- [ ] Delete avatar

### Phase 3: Content Generation ✅
- [ ] Generate titles
- [ ] Generate description
- [ ] Generate tags
- [ ] Generate thumbnail text
- [ ] Get content history
- [ ] Get content stats
- [ ] Delete content

### Phase 4: SEO Analysis ✅
- [ ] Analyze video SEO
- [ ] Get SEO reports
- [ ] Get dashboard stats

### Phase 5: Trending Topics ✅
- [ ] Fetch trending videos
- [ ] Filter trending videos
- [ ] Get trending stats
- [ ] Get trending dashboard
- [ ] Get content opportunities
- [ ] Get YouTube categories
- [ ] Get supported regions

### Phase 6: YouTube Integration ✅
- [ ] Get connected channels
- [ ] Sync channel videos
- [ ] Get channel videos

---

## Common Issues & Solutions

### Issue: "Not authenticated"
**Solution:** Make sure you're including the Bearer token in Authorization header
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Issue: "Invalid or expired token"
**Solution:** Login again to get a fresh token, or use refresh endpoint

### Issue: "YouTube API key not configured"
**Solution:** Add `YOUTUBE_API_KEY` to `.env` file

### Issue: "OpenAI API key not configured"
**Solution:** Add `OPENAI_API_KEY` to `.env` file for AI content generation

### Issue: "Supabase connection failed"
**Solution:** Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

---

## Environment Variables Required

```env
# Supabase
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# JWT
SECRET_KEY=your_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# YouTube API
YOUTUBE_API_KEY=your_key
YOUTUBE_CLIENT_ID=your_id
YOUTUBE_CLIENT_SECRET=your_secret

# OpenAI
OPENAI_API_KEY=your_key

# App Settings
APP_NAME=VantageTube AI
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
```

---

## Running Tests with Postman

1. **Start Backend:**
   ```bash
   cd vantagetube-ai/backend
   python -m uvicorn app.main:app --reload
   ```

2. **Import Collection** in Postman

3. **Create Environment** with:
   - `base_url`: `http://localhost:8000/api`
   - `access_token`: (empty, will be filled)

4. **Run Collection:**
   - Click "Run" button
   - Select all requests
   - Click "Run VantageTube AI API"

5. **Review Results:**
   - Check response status codes
   - Verify response data
   - Check for errors

---

## API Response Format

### Success Response (200)
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Error Response (400/401/500)
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Next Steps

1. **Set up Postman API Key** (optional, for automation)
2. **Start backend server**
3. **Import collection** into Postman
4. **Run tests** to verify all endpoints
5. **Fix any issues** found during testing
6. **Document API** for frontend team

---

## Support

For issues or questions:
1. Check `.env` configuration
2. Verify backend is running
3. Check Supabase connection
4. Review error messages in console
5. Check API documentation in code comments

