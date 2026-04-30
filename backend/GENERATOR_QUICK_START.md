# AI Content Generator API - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Run Database Migration (1 minute)

```bash
# Navigate to backend directory
cd VantageTube-AI/vantagetube-ai/backend

# Run migration
psql -U postgres -d vantagetube_db -f database_migrations_generator.sql
```

**What it does:**
- Creates 5 database tables
- Sets up indexes for performance
- Enables row-level security
- Adds automatic timestamp triggers

### Step 2: Verify Environment Variables (1 minute)

Check your `.env` file has:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### Step 3: Start the Server (1 minute)

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

### Step 4: Test the API (1 minute)

```bash
# Health check
curl http://localhost:8000/api/generator/health

# View API documentation
# Open in browser: http://localhost:8000/docs
```

### Step 5: Make Your First Request (1 minute)

```bash
# Analyze a niche (requires authentication token)
curl -X POST "http://localhost:8000/api/generator/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "python tutorials",
    "region": "US",
    "limit": 20
  }'
```

---

## 📚 API Endpoints Reference

### Analysis
```bash
POST /api/generator/analyze
# Analyze trending videos in a niche
```

### Generation
```bash
POST /api/generator/titles          # Generate titles
POST /api/generator/tags            # Generate tags
POST /api/generator/description     # Generate description
POST /api/generator/thumbnail-text  # Generate thumbnail text
POST /api/generator/generate-all    # Generate all at once
```

### Management
```bash
GET  /api/generator/history         # Get generation history
GET  /api/generator/history/{id}    # Get specific content
DELETE /api/generator/history/{id}  # Delete content
GET  /api/generator/stats           # Get statistics
```

### Additional
```bash
POST /api/generator/regenerate      # Regenerate content
POST /api/generator/feedback        # Submit feedback
GET  /api/generator/health          # Health check
```

---

## 🔑 Authentication

All endpoints (except `/health`) require JWT authentication:

```bash
curl -X POST "http://localhost:8000/api/generator/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Get a token:**
1. Use the auth endpoint: `POST /api/auth/login`
2. Or use an existing user token from your auth system

---

## 📋 Common Use Cases

### Use Case 1: Analyze a Niche

```bash
curl -X POST "http://localhost:8000/api/generator/analyze" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "machine learning tutorials",
    "region": "US",
    "category_id": "28",
    "limit": 50
  }'
```

**Response includes:**
- Top keywords with frequency and engagement
- Common title patterns
- Average viral score and engagement rate
- Content opportunities

### Use Case 2: Generate Titles

```bash
curl -X POST "http://localhost:8000/api/generator/titles" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Machine Learning",
    "keywords": ["machine learning", "python", "tutorial"],
    "tone": "educational",
    "target_audience": "beginners",
    "count": 5
  }'
```

**Response includes:**
- 5 title variations
- SEO score for each
- Reasoning for each title

### Use Case 3: Batch Generate Everything

```bash
curl -X POST "http://localhost:8000/api/generator/generate-all" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Machine Learning",
    "keywords": ["machine learning", "python", "tutorial"],
    "tone": "educational",
    "target_audience": "beginners",
    "video_length": "medium",
    "title_count": 5,
    "tag_count": 15,
    "include_timestamps": true,
    "include_links": true,
    "include_cta": true,
    "thumbnail_count": 5
  }'
```

**Response includes:**
- 5 titles
- 15 tags (categorized)
- 1 description (200-300 words)
- 5 thumbnail text suggestions
- Quality scores for each

### Use Case 4: Get Generation History

```bash
curl -X GET "http://localhost:8000/api/generator/history?content_type=title&limit=20" \
  -H "Authorization: Bearer TOKEN"
```

**Response includes:**
- All previously generated titles
- Timestamps and quality scores
- Pagination info

### Use Case 5: Get Statistics

```bash
curl -X GET "http://localhost:8000/api/generator/stats" \
  -H "Authorization: Bearer TOKEN"
```

**Response includes:**
- Total generations
- Breakdown by content type
- Average quality score
- Most used keywords and tones
- Generation trends

---

## 🛠️ Troubleshooting

### Issue: "Database connection failed"
```bash
# Check Supabase connection
python -c "from app.core.supabase import get_supabase; print(get_supabase())"

# Verify .env variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### Issue: "Tables don't exist"
```bash
# Re-run migration
psql -U postgres -d vantagetube_db -f database_migrations_generator.sql

# Verify tables were created
psql -U postgres -d vantagetube_db -c "\dt"
```

### Issue: "Unauthorized" error
```bash
# Verify token format
# Should be: Authorization: Bearer YOUR_TOKEN

# Check token is valid
# Token should include user_id claim
```

### Issue: "AI service unavailable"
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Verify API quota
# Check OpenAI dashboard for rate limits
```

---

## 📊 Response Format

### Success Response
```json
{
  "titles": [
    {
      "text": "Machine Learning for Beginners: Complete Python Guide",
      "score": 87,
      "reasoning": "Front-loads keywords, includes power word 'Complete', targets audience"
    }
  ],
  "topic": "Introduction to Machine Learning",
  "keywords": ["machine learning", "python", "tutorial"],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "error_id": "gen_error_12345",
  "message": "Failed to generate titles",
  "details": {
    "reason": "AI service temporarily unavailable"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔍 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Full Documentation
- **Implementation Guide**: `GENERATOR_IMPLEMENTATION.md`
- **Summary**: `GENERATOR_SUMMARY.md`

---

## 📁 File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── generator.py          # ← API endpoints
│   │   └── ...
│   ├── services/
│   │   ├── generator_service.py  # ← Generation logic
│   │   ├── analysis_service.py   # ← Analysis logic
│   │   ├── content_service.py    # ← Storage logic
│   │   └── ...
│   ├── models/
│   │   ├── generator.py          # ← Data models
│   │   └── ...
│   └── main.py                   # ← FastAPI app
├── database_migrations_generator.sql  # ← Database schema
├── GENERATOR_IMPLEMENTATION.md        # ← Full guide
├── GENERATOR_SUMMARY.md               # ← Summary
└── GENERATOR_QUICK_START.md           # ← This file
```

---

## 🎯 Next Steps

### For Development
1. ✅ Run database migration
2. ✅ Start the server
3. ✅ Test endpoints with Swagger UI
4. → Proceed to Phase 4: Quality Validation

### For Integration
1. ✅ Get JWT token from auth system
2. ✅ Make API requests with token
3. ✅ Handle responses and errors
4. → Update frontend to use new endpoints

### For Deployment
1. ✅ Set environment variables
2. ✅ Run database migration
3. ✅ Start server in production mode
4. → Monitor logs and performance

---

## 💡 Tips & Tricks

### Tip 1: Use Swagger UI for Testing
- Go to `http://localhost:8000/docs`
- Click "Authorize" and enter your token
- Try endpoints directly in the browser

### Tip 2: Save Common Requests
```bash
# Save as analyze.sh
#!/bin/bash
curl -X POST "http://localhost:8000/api/generator/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "python tutorials",
    "region": "US",
    "limit": 20
  }'
```

### Tip 3: Monitor Logs
```bash
# Watch logs in real-time
tail -f app.log

# Filter for errors
grep ERROR app.log
```

### Tip 4: Check Database
```bash
# Connect to database
psql -U postgres -d vantagetube_db

# View generated content
SELECT * FROM generated_content LIMIT 10;

# View statistics
SELECT user_id, COUNT(*) as total FROM generated_content GROUP BY user_id;
```

---

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Review `GENERATOR_IMPLEMENTATION.md` for detailed info
3. Check API documentation at `/docs`
4. Review error messages and error IDs

### Reporting Issues
Include:
- Error ID from response
- Request details
- Response received
- Steps to reproduce

---

## ✅ Checklist

Before going to production:
- [ ] Database migration completed
- [ ] Environment variables set
- [ ] Server starts without errors
- [ ] Health check endpoint works
- [ ] Can authenticate with token
- [ ] Can make API requests
- [ ] Responses are correct
- [ ] Error handling works
- [ ] Logs are being written
- [ ] Performance is acceptable

---

**Ready to go!** 🚀

Start with the 5-minute setup above, then explore the API using Swagger UI at `http://localhost:8000/docs`

For detailed information, see `GENERATOR_IMPLEMENTATION.md`
