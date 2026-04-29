# VantageTube AI - Complete API Endpoints Map

## 📍 API Structure

```
BASE_URL: http://localhost:8000/api

├── /auth (Authentication)
│   ├── POST   /register              → Create new user
│   ├── POST   /login                 → Get access token
│   ├── GET    /me                    → Get current user
│   ├── GET    /check                 → Verify token
│   ├── POST   /refresh               → Refresh token
│   └── POST   /logout                → Logout user
│
├── /users (User Management)
│   ├── GET    /me                    → Get profile
│   ├── PUT    /me                    → Update profile
│   ├── POST   /change-password       → Change password
│   ├── POST   /avatar                → Upload avatar
│   ├── DELETE /avatar                → Delete avatar
│   ├── GET    /settings              → Get settings
│   └── PUT    /settings              → Update settings
│
├── /content (Content Generation)
│   ├── POST   /generate/titles       → Generate video titles
│   ├── POST   /generate/description  → Generate description
│   ├── POST   /generate/tags         → Generate tags
│   ├── POST   /generate/thumbnail-text → Generate thumbnail text
│   ├── GET    /history               → Get generation history
│   ├── GET    /history/{id}          → Get specific content
│   ├── DELETE /history/{id}          → Delete content
│   └── GET    /stats                 → Get generation stats
│
├── /seo (SEO Analysis)
│   ├── POST   /analyze               → Analyze video SEO
│   ├── GET    /videos/{id}/reports   → Get SEO reports
│   └── GET    /dashboard/stats       → Get dashboard stats
│
├── /trending (Trending Topics)
│   ├── POST   /fetch                 → Fetch trending videos
│   ├── POST   /filter                → Filter trending videos
│   ├── GET    /videos/{id}/analyze   → Analyze trending video
│   ├── GET    /stats                 → Get trending stats
│   ├── GET    /dashboard             → Get trending dashboard
│   ├── GET    /opportunities         → Get content opportunities
│   ├── GET    /categories            → Get YouTube categories
│   └── GET    /regions               → Get supported regions
│
└── /youtube (YouTube Integration)
    ├── GET    /oauth/authorize       → Start OAuth flow
    ├── GET    /oauth/callback        → Handle OAuth callback
    ├── GET    /channels              → Get connected channels
    ├── POST   /channels/{id}/sync    → Sync channel videos
    ├── GET    /channels/{id}/videos  → Get channel videos
    └── DELETE /channels/{id}         → Disconnect channel
```

---

## 🔐 Authentication Requirements

### Public Endpoints (No Auth Required)
```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/health
GET    /api/
```

### Protected Endpoints (Auth Required)
All other endpoints require:
```
Authorization: Bearer {access_token}
```

---

## 📝 Detailed Endpoint Reference

### AUTHENTICATION MODULE

#### 1. Register User
```
POST /auth/register
Status: 201 Created

Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe"
}

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "avatar_url": null,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 2. Login User
```
POST /auth/login
Status: 200 OK

Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": { ... }
}
```

#### 3. Get Current User
```
GET /auth/me
Status: 200 OK
Auth: Required

Response:
{
  "id": "user-123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "avatar_url": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 4. Check Auth Status
```
GET /auth/check
Status: 200 OK
Auth: Required

Response:
{
  "authenticated": true,
  "user_id": "user-123"
}
```

#### 5. Refresh Token
```
POST /auth/refresh
Status: 200 OK
Auth: Required

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": { ... }
}
```

#### 6. Logout
```
POST /auth/logout
Status: 200 OK
Auth: Required

Response:
{
  "message": "Logged out successfully",
  "user_id": "user-123"
}
```

---

### USERS MODULE

#### 1. Get User Profile
```
GET /users/me
Status: 200 OK
Auth: Required

Response:
{
  "id": "user-123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "username": "johndoe",
  "country": "us",
  "niche": "tech",
  "bio": "I create tech content",
  "avatar_url": "https://...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Update User Profile
```
PUT /users/me
Status: 200 OK
Auth: Required

Request:
{
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "username": "johndoe",
  "country": "us",
  "niche": "tech",
  "bio": "I create tech content"
}

Response: Updated user object
```

#### 3. Change Password
```
POST /users/change-password
Status: 200 OK
Auth: Required

Request:
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!",
  "confirm_password": "NewPass123!"
}

Response:
{
  "message": "Password changed successfully"
}
```

#### 4. Upload Avatar
```
POST /users/avatar
Status: 200 OK
Auth: Required
Content-Type: multipart/form-data

Request:
- file: (image file, max 5MB)

Response:
{
  "message": "Avatar uploaded successfully",
  "avatar_url": "https://..."
}
```

#### 5. Delete Avatar
```
DELETE /users/avatar
Status: 200 OK
Auth: Required

Response:
{
  "message": "Avatar deleted successfully"
}
```

#### 6. Get User Settings
```
GET /users/settings
Status: 200 OK
Auth: Required

Response:
{
  "id": "settings-123",
  "user_id": "user-123",
  "theme": "dark",
  "accent_color": "#6C63FF",
  "font_size": "normal",
  "compact_mode": false,
  "email_notifications": true,
  "weekly_seo_report": true,
  "trending_alerts": true,
  "feature_updates": true,
  "milestone_alerts": true,
  "profile_visibility": true,
  "analytics_sharing": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### 7. Update User Settings
```
PUT /users/settings
Status: 200 OK
Auth: Required

Request:
{
  "theme": "dark",
  "accent_color": "#6C63FF",
  "font_size": "normal",
  "compact_mode": false,
  "email_notifications": true,
  "weekly_seo_report": true,
  "trending_alerts": true,
  "feature_updates": true,
  "milestone_alerts": true,
  "profile_visibility": true,
  "analytics_sharing": false
}

Response: Updated settings object
```

---

### CONTENT GENERATION MODULE

#### 1. Generate Titles
```
POST /content/generate/titles
Status: 200 OK
Auth: Required

Request:
{
  "topic": "How to learn Python programming",
  "keywords": ["python", "programming", "tutorial"],
  "tone": "educational",
  "target_audience": "beginners",
  "count": 5,
  "video_id": "optional-video-id"
}

Response:
{
  "titles": [
    {
      "title": "Python for Beginners: Complete Tutorial 2024",
      "seo_score": 92,
      "reasoning": "Includes year, clear intent, keyword-rich"
    },
    ...
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Generate Description
```
POST /content/generate/description
Status: 200 OK
Auth: Required

Request:
{
  "topic": "How to learn Python programming",
  "title": "Python for Beginners - Complete Tutorial",
  "keywords": ["python", "programming", "tutorial"],
  "tone": "educational",
  "target_audience": "beginners",
  "video_length": "long",
  "include_timestamps": true,
  "include_links": true,
  "include_cta": true,
  "video_id": "optional-video-id"
}

Response:
{
  "description": "In this comprehensive Python tutorial...",
  "seo_tips": ["Include timestamps", "Add relevant links"],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 3. Generate Tags
```
POST /content/generate/tags
Status: 200 OK
Auth: Required

Request:
{
  "topic": "How to learn Python programming",
  "title": "Python for Beginners - Complete Tutorial",
  "keywords": ["python", "programming"],
  "count": 15,
  "video_id": "optional-video-id"
}

Response:
{
  "primary_tags": ["python", "programming", "tutorial"],
  "secondary_tags": ["coding", "beginners", "education"],
  "long_tail_tags": ["how to learn python", "python for beginners"],
  "broad_tags": ["education", "technology"],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 4. Generate Thumbnail Text
```
POST /content/generate/thumbnail-text
Status: 200 OK
Auth: Required

Request:
{
  "topic": "How to learn Python programming",
  "title": "Python for Beginners - Complete Tutorial",
  "count": 5,
  "video_id": "optional-video-id"
}

Response:
{
  "suggestions": [
    {
      "text": "PYTHON 101",
      "style": "bold",
      "design_tips": "Use contrasting colors"
    },
    ...
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 5. Get Content History
```
GET /content/history?content_type=title&limit=50
Status: 200 OK
Auth: Required

Query Parameters:
- content_type: (optional) title, description, tags, thumbnail_text
- video_id: (optional) filter by video
- limit: (optional) default 50

Response:
{
  "items": [
    {
      "id": "content-123",
      "user_id": "user-123",
      "content_type": "title",
      "content": { ... },
      "video_id": "video-123",
      "prompt_used": "Topic: ...",
      "created_at": "2024-01-15T10:30:00Z"
    },
    ...
  ],
  "total": 150
}
```

#### 6. Get Content Stats
```
GET /content/stats
Status: 200 OK
Auth: Required

Response:
{
  "total_generated": 150,
  "by_type": {
    "title": 50,
    "description": 40,
    "tags": 40,
    "thumbnail_text": 20
  },
  "recent": [
    { ... },
    ...
  ]
}
```

---

### SEO ANALYSIS MODULE

#### 1. Analyze Video SEO
```
POST /seo/analyze
Status: 200 OK
Auth: Required

Request:
{
  "video_id": "video-123",
  "force_reanalysis": false
}

Response:
{
  "video_id": "video-123",
  "overall_score": 85,
  "grade": "B",
  "criteria": {
    "title": {
      "score": 90,
      "feedback": "Good length and keywords"
    },
    "description": {
      "score": 80,
      "feedback": "Add more links"
    },
    "tags": {
      "score": 85,
      "feedback": "Good variety"
    },
    "thumbnail": {
      "score": 75,
      "feedback": "Could be more eye-catching"
    },
    "engagement": {
      "score": 80,
      "feedback": "Good engagement rate"
    }
  },
  "suggestions": [
    "Add more relevant tags",
    "Include timestamps in description"
  ],
  "analyzed_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Get Video SEO Reports
```
GET /seo/videos/video-123/reports
Status: 200 OK
Auth: Required

Response:
{
  "video_id": "video-123",
  "reports": [
    {
      "id": "report-123",
      "overall_score": 85,
      "grade": "B",
      "criteria": { ... },
      "suggestions": [ ... ],
      "analyzed_at": "2024-01-15T10:30:00Z"
    },
    ...
  ]
}
```

#### 3. Get SEO Dashboard Stats
```
GET /seo/dashboard/stats
Status: 200 OK
Auth: Required

Response:
{
  "total_videos": 50,
  "analyzed_videos": 45,
  "average_score": 78,
  "score_distribution": {
    "excellent": 10,
    "good": 20,
    "average": 12,
    "poor": 3,
    "critical": 0
  },
  "recent_analyses": [
    { ... },
    ...
  ]
}
```

---

### TRENDING TOPICS MODULE

#### 1. Fetch Trending Videos
```
POST /trending/fetch
Status: 200 OK
Auth: Required

Request:
{
  "region": "US",
  "category_id": "28",
  "max_results": 50
}

Response:
[
  {
    "id": "trending-123",
    "youtube_id": "dQw4w9WgXcQ",
    "title": "Trending Video Title",
    "channel": "Channel Name",
    "views": 1000000,
    "likes": 50000,
    "comments": 5000,
    "viral_score": 85,
    "category_id": "28",
    "region": "US",
    "fetched_at": "2024-01-15T10:30:00Z"
  },
  ...
]
```

#### 2. Filter Trending Videos
```
POST /trending/filter
Status: 200 OK
Auth: Required

Request:
{
  "keywords": ["python", "programming"],
  "min_views": 100000,
  "min_viral_score": 50,
  "category_id": "28",
  "region": "US",
  "limit": 20
}

Response: Array of trending videos
```

#### 3. Get Trending Stats
```
GET /trending/stats?region=US
Status: 200 OK
Auth: Required

Response:
{
  "total_trending": 500,
  "average_views": 500000,
  "average_viral_score": 72,
  "top_categories": {
    "Music": 150,
    "Entertainment": 120,
    "Gaming": 100
  },
  "trending_keywords": ["viral", "trending", "challenge"],
  "last_fetch": "2024-01-15T10:30:00Z"
}
```

#### 4. Get Trending Dashboard
```
GET /trending/dashboard?region=US
Status: 200 OK
Auth: Required

Response:
{
  "total_trending": 500,
  "by_category": {
    "Music": 150,
    "Entertainment": 120,
    "Gaming": 100
  },
  "top_viral_videos": [ ... ],
  "average_viral_score": 72,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### 5. Get YouTube Categories
```
GET /trending/categories
Status: 200 OK
Auth: Required

Response:
[
  { "id": "1", "name": "Film & Animation" },
  { "id": "2", "name": "Autos & Vehicles" },
  { "id": "10", "name": "Music" },
  { "id": "15", "name": "Pets & Animals" },
  { "id": "17", "name": "Sports" },
  { "id": "18", "name": "Short Movies" },
  { "id": "19", "name": "Travel & Events" },
  { "id": "20", "name": "Gaming" },
  { "id": "21", "name": "Videoblogging" },
  { "id": "22", "name": "People & Blogs" },
  { "id": "23", "name": "Comedy" },
  { "id": "24", "name": "Entertainment" },
  { "id": "25", "name": "News & Politics" },
  { "id": "26", "name": "Howto & Style" },
  { "id": "27", "name": "Education" },
  { "id": "28", "name": "Science & Technology" },
  { "id": "29", "name": "Nonprofits & Activism" }
]
```

#### 6. Get Supported Regions
```
GET /trending/regions
Status: 200 OK
Auth: Required

Response:
[
  { "code": "US", "name": "United States" },
  { "code": "GB", "name": "United Kingdom" },
  { "code": "CA", "name": "Canada" },
  { "code": "AU", "name": "Australia" },
  { "code": "IN", "name": "India" },
  { "code": "DE", "name": "Germany" },
  { "code": "FR", "name": "France" },
  { "code": "JP", "name": "Japan" },
  { "code": "KR", "name": "South Korea" },
  { "code": "BR", "name": "Brazil" },
  { "code": "MX", "name": "Mexico" },
  { "code": "ES", "name": "Spain" },
  { "code": "IT", "name": "Italy" },
  { "code": "RU", "name": "Russia" },
  { "code": "NL", "name": "Netherlands" }
]
```

---

### YOUTUBE INTEGRATION MODULE

#### 1. Get YouTube Channels
```
GET /youtube/channels
Status: 200 OK
Auth: Required

Response:
[
  {
    "id": "channel-123",
    "user_id": "user-123",
    "youtube_id": "UCxxxxxx",
    "title": "My Channel",
    "description": "Channel description",
    "subscriber_count": 10000,
    "video_count": 50,
    "view_count": 500000,
    "is_connected": true,
    "connected_at": "2024-01-15T10:30:00Z"
  },
  ...
]
```

#### 2. Sync Channel Videos
```
POST /youtube/channels/channel-123/sync?max_results=50
Status: 200 OK
Auth: Required

Response:
{
  "message": "Sync completed",
  "channel_id": "channel-123",
  "videos_synced": 50,
  "new_videos": 10,
  "updated_videos": 40,
  "synced_at": "2024-01-15T10:30:00Z"
}
```

#### 3. Get Channel Videos
```
GET /youtube/channels/channel-123/videos
Status: 200 OK
Auth: Required

Response:
[
  {
    "id": "video-123",
    "channel_id": "channel-123",
    "youtube_id": "dQw4w9WgXcQ",
    "title": "Video Title",
    "description": "Video description",
    "published_at": "2024-01-15T10:30:00Z",
    "view_count": 100000,
    "like_count": 5000,
    "comment_count": 500,
    "seo_score": 85,
    "last_analyzed_at": "2024-01-15T10:30:00Z"
  },
  ...
]
```

#### 4. Disconnect Channel
```
DELETE /youtube/channels/channel-123
Status: 200 OK
Auth: Required

Response:
{
  "message": "Channel disconnected successfully",
  "channel_id": "channel-123"
}
```

---

## 🔄 Common Request/Response Patterns

### Pagination
```
Query Parameters:
- limit: Number of results (default: 50)
- offset: Number of results to skip (default: 0)

Response:
{
  "items": [ ... ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Filtering
```
Query Parameters:
- keyword: Search keyword
- sort_by: Field to sort by
- sort_order: asc or desc
- filter_field: Value to filter by
```

### Error Responses
```
400 Bad Request:
{
  "detail": "Invalid request parameters"
}

401 Unauthorized:
{
  "detail": "Not authenticated"
}

404 Not Found:
{
  "detail": "Resource not found"
}

500 Internal Server Error:
{
  "detail": "Internal server error"
}
```

---

## 📊 Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Successful, no response body |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

---

## 🚀 Quick Reference

### Get Started
```bash
# 1. Register
POST /auth/register

# 2. Login
POST /auth/login

# 3. Use token for all requests
Authorization: Bearer {access_token}
```

### Generate Content
```bash
# Generate titles
POST /content/generate/titles

# Generate description
POST /content/generate/description

# Generate tags
POST /content/generate/tags
```

### Analyze SEO
```bash
# Analyze video
POST /seo/analyze

# Get dashboard stats
GET /seo/dashboard/stats
```

### Check Trending
```bash
# Get trending videos
POST /trending/fetch

# Get opportunities
GET /trending/opportunities
```

---

**Last Updated**: 2024-01-15
**API Version**: 1.0.0
**Total Endpoints**: 40+

