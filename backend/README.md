# 🎬 VantageTube AI - Backend API

**FastAPI + Supabase Backend for YouTube Creator Optimization Platform**

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication endpoints (6 endpoints)
│   │   ├── users.py        # User profile endpoints (7 endpoints)
│   │   ├── youtube.py      # YouTube integration (6 endpoints)
│   │   ├── seo.py          # SEO analysis (3 endpoints)
│   │   └── content.py      # AI content generation (8 endpoints)
│   ├── core/               # Core configuration
│   │   ├── config.py       # Settings & environment variables
│   │   ├── security.py     # JWT & password hashing
│   │   └── supabase.py     # Supabase client
│   ├── models/             # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py         # User models
│   │   ├── settings.py     # User settings models
│   │   ├── youtube.py      # YouTube models
│   │   ├── seo.py          # SEO analysis models
│   │   └── content.py      # AI content generation models
│   ├── services/           # Business logic
│   │   ├── auth_service.py     # Authentication service
│   │   ├── user_service.py     # User profile service
│   │   ├── storage_service.py  # File storage service
│   │   ├── youtube_service.py  # YouTube API service
│   │   ├── seo_service.py      # SEO analysis service
│   │   ├── ai_service.py       # OpenAI integration
│   │   └── content_service.py  # Content storage service
│   ├── utils/              # Utility functions
│   ├── __init__.py
│   └── main.py             # FastAPI application
├── database_schema.sql     # Supabase database schema
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore
├── README.md              # This file
├── QUICK_START.md         # Quick start guide
├── PHASE_2.2_COMPLETE.md  # Phase 2.2 documentation
├── PHASE_2.3_COMPLETE.md  # Phase 2.3 documentation
├── PHASE_2.4_COMPLETE.md  # Phase 2.4 documentation
├── PHASE_2.5_COMPLETE.md  # Phase 2.5 documentation
├── PHASE_2.5_QUICKSTART.md # Phase 2.5 quick start
└── AI_GENERATION_EXAMPLES.md # AI generation examples
```

---

## 🚀 Phase 2: Backend Setup Guide

### **Step 1: Set Up Supabase Project**

1. **Create Supabase Account**
   - Go to [https://supabase.com](https://supabase.com)
   - Sign up for a free account
   - Create a new project

2. **Get Your Credentials**
   - Go to Project Settings → API
   - Copy the following:
     - `Project URL` (SUPABASE_URL)
     - `anon public` key (SUPABASE_KEY)
     - `service_role` key (SUPABASE_SERVICE_KEY)

3. **Set Up Database Schema**
   - Go to SQL Editor in Supabase dashboard
   - Copy the contents of `database_schema.sql`
   - Run the SQL script
   - Verify tables are created in Table Editor

4. **Configure Authentication**
   - Go to Authentication → Providers
   - Enable **Email** provider
   - (Optional) Enable **Google OAuth** for social login
   - Configure redirect URLs if using OAuth

---

### **Step 2: Install Python Dependencies**

1. **Create Virtual Environment**
   ```bash
   # Navigate to backend directory
   cd backend

   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

### **Step 3: Configure Environment Variables**

1. **Create .env File**
   ```bash
   # Copy example file
   cp .env.example .env
   ```

2. **Fill in Your Credentials**
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_here
   SUPABASE_SERVICE_KEY=your_service_role_key_here

   # JWT Configuration
   SECRET_KEY=your_secret_key_here  # Generate with: openssl rand -hex 32
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # YouTube API (Optional for now)
   YOUTUBE_API_KEY=
   YOUTUBE_CLIENT_ID=
   YOUTUBE_CLIENT_SECRET=

   # OpenAI API (Optional for now)
   OPENAI_API_KEY=

   # Application Settings
   DEBUG=True
   ENVIRONMENT=development
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500
   ```

3. **Generate Secret Key**
   ```bash
   # On Windows (PowerShell):
   python -c "import secrets; print(secrets.token_hex(32))"

   # On macOS/Linux:
   openssl rand -hex 32
   ```

---

### **Step 4: Run the Backend Server**

1. **Start Development Server**
   ```bash
   # Make sure you're in the backend directory with venv activated
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify Server is Running**
   - Open browser: [http://localhost:8000](http://localhost:8000)
   - You should see: `{"message": "Welcome to VantageTube AI API"}`

3. **Access API Documentation**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔐 API Endpoints (Phase 2.1 - Authentication)

### **Authentication Endpoints**

#### **1. Register New User**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "confirm_password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "plan": "free",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### **2. Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as register

#### **3. Get Current User**
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "username": null,
  "country": null,
  "niche": null,
  "bio": null,
  "avatar_url": null,
  "plan": "free",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

#### **4. Logout**
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

#### **5. Refresh Token**
```http
POST /api/auth/refresh
Authorization: Bearer <access_token>
```

#### **6. Check Authentication**
```http
GET /api/auth/check
Authorization: Bearer <access_token>
```

---

## 🧪 Testing the API

### **Using Swagger UI (Recommended)**

1. Open [http://localhost:8000/docs](http://localhost:8000/docs)
2. Click on any endpoint to expand
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. View the response

### **Using cURL**

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Get current user (replace TOKEN with actual token)
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer TOKEN"
```

### **Using Postman**

1. Import the API endpoints from Swagger JSON
2. Create a new environment with `base_url = http://localhost:8000`
3. Test each endpoint

---

## 🔄 Next Steps (Phase 2.2 - 2.4)

### **Phase 2.2: User Profile Management**
- [ ] Update user profile endpoint
- [ ] Change password endpoint
- [ ] Upload avatar endpoint
- [ ] User settings CRUD

### **Phase 2.3: YouTube Integration**
- [ ] YouTube OAuth flow
- [ ] Fetch channel data
- [ ] Fetch videos
- [ ] Sync channel statistics

### **Phase 2.4: SEO Analysis**
- [ ] Video SEO scoring algorithm
- [ ] Generate SEO reports
- [ ] Store analysis results
- [ ] Improvement suggestions

### **Phase 2.5: AI Content Generation**
- [ ] OpenAI integration
- [ ] Generate titles
- [ ] Generate descriptions
- [ ] Generate tags
- [ ] Thumbnail suggestions

### **Phase 2.6: Trending Topics**
- [ ] Fetch trending data
- [ ] Filter by niche
- [ ] Viral score calculation
- [ ] Cache trending data

---

## 🛠️ Development Tips

### **Hot Reload**
The server automatically reloads when you save changes to Python files (thanks to `--reload` flag).

### **Debugging**
- Check logs in terminal where server is running
- Use `print()` statements or Python debugger
- Check Supabase logs in dashboard

### **Database Changes**
- Make changes in `database_schema.sql`
- Run the updated SQL in Supabase SQL Editor
- Restart the server

### **Environment Variables**
- Never commit `.env` file to Git
- Always update `.env.example` when adding new variables
- Restart server after changing `.env`

---

## 📚 Tech Stack

- **FastAPI**: Modern Python web framework
- **Supabase**: Backend-as-a-Service (PostgreSQL + Auth)
- **Pydantic**: Data validation
- **JWT**: Token-based authentication
- **Uvicorn**: ASGI server
- **Python 3.10+**: Programming language

---

## 🐛 Troubleshooting

### **Server won't start**
- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check `.env` file exists and has correct values

### **Database connection errors**
- Verify Supabase URL and keys are correct
- Check if database schema is created
- Ensure RLS policies are set up

### **Authentication errors**
- Verify SECRET_KEY is set in `.env`
- Check if user exists in Supabase Auth
- Verify token is being sent in Authorization header

### **CORS errors**
- Add your frontend URL to `ALLOWED_ORIGINS` in `.env`
- Restart the server after changing CORS settings

---

## 📝 Notes

- This is Phase 2.1 - Basic authentication is complete
- YouTube API and OpenAI integration will be added in later phases
- All endpoints are documented in Swagger UI
- Database schema includes all tables for future features

---

## 🎯 Current Status

✅ **Phase 2.1 Complete**: Authentication & User Management
- User registration
- User login
- JWT token generation
- Protected routes
- Supabase integration

🔄 **Next**: Phase 2.2 - User Profile Management

---

**Happy Coding! 🚀**
