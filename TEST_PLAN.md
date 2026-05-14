# VantageTube AI – Comprehensive Test Plan

## Overview

This document outlines the complete testing strategy for the **VantageTube AI** platform, covering both the **FastAPI backend** and the **vanilla JS frontend**. The plan is structured into **phases**, each with specific test cases, expected outcomes, and prioritization.

---

## Table of Contents

1. [Existing Test Infrastructure](#1-existing-test-infrastructure)
2. [Phase 1: Backend Unit Tests](#2-phase-1-backend-unit-tests)
3. [Phase 2: Backend Service Tests](#3-phase-2-backend-service-tests)
4. [Phase 3: API Integration Tests](#4-phase-3-api-integration-tests)
5. [Phase 4: Frontend Tests](#5-phase-4-frontend-tests)
6. [Phase 5: End-to-End Tests](#6-phase-5-end-to-end-tests)
7. [Phase 6: Performance & Edge Cases](#7-phase-6-performance--edge-cases)
8. [Running the Tests](#8-running-the-tests)
9. [Test Coverage Matrix](#9-test-coverage-matrix)

---

## 1. Existing Test Infrastructure

### Current Test Files

| File | Lines | Coverage | Status |
|------|-------|----------|--------|
| `backend/tests/test_ai_orchestrator.py` | 325 | AIOrchestrator internals, bundles, parsing, 429 handling, caching | ✅ Existing |
| `backend/tests/test_ai_orchestrator_properties.py` | 492 | Property-based (Hypothesis) tests for orchestrator | ✅ Existing |
| `backend/tests/__init__.py` | Empty | Package init | ✅ Existing |
| `backend/test_connection.py` | - | Supabase connection verification | ✅ Existing |
| `backend/test_all_apis.py` | - | Manual API endpoint testing script | ✅ Existing |
| `backend/test_nano_api.py` | - | Nano API thumbnail testing | ✅ Existing |

### Existing Test Coverage (Backend)

- `AIOrchestrator` – 12 property-based tests + 25 unit tests
- `VideoAnalysisBundle` / `GeneratorBundle` – factory tests
- `_parse_batch_response` – JSON parsing, missing fields, invalid JSON
- `_handle_429` – cooldown timing, error message parsing
- `_hash_bundle` / `_hash_task` – deterministic hashing, order independence
- `/generate/video-analysis` endpoint schema validation
- Quota error classification (exhaustive for known phrases)
- Per-user serialization (concurrent access)
- Cache hit/miss behavior
- Backward-compatible response schemas

---

## 2. Phase 1: Backend Unit Tests

### 2.1 Core Configuration (`app/core/`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 1.1 | `config.py` – Load settings from `.env` | All required fields populated with correct types | `tests/test_core.py` |
| 1.2 | `config.py` – `cors_origins` property parses comma-separated string | Returns `List[str]` with trimmed values | `tests/test_core.py` |
| 1.3 | `config.py` – Default values when env vars missing | Falls back to defaults where applicable | `tests/test_core.py` |
| 1.4 | `security.py` – `create_access_token` generates valid JWT | Token decodable, contains `sub` and `exp` | `tests/test_core.py` |
| 1.5 | `security.py` – `decode_access_token` returns payload for valid token | Returns dict with correct claims | `tests/test_core.py` |
| 1.6 | `security.py` – `decode_access_token` returns `None` for expired token | Returns `None` | `tests/test_core.py` |
| 1.7 | `security.py` – `decode_access_token` returns `None` for invalid signature | Returns `None` | `tests/test_core.py` |
| 1.8 | `security.py` – `hash_password` / `verify_password` round-trip | `verify_password(plain, hash) == True` | `tests/test_core.py` |
| 1.9 | `security.py` – Different passwords not verified | `verify_password(wrong, hash) == False` | `tests/test_core.py` |

### 2.2 Model Validation (`app/models/`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 2.1 | `UserCreate` – Valid data passes validation | Model created with all fields | `tests/test_models.py` |
| 2.2 | `UserCreate` – Invalid email raises `ValidationError` | `pydantic.ValidationError` | `tests/test_models.py` |
| 2.3 | `UserCreate` – Short password (< 8 chars) raises error | `ValidationError` | `tests/test_models.py` |
| 2.4 | `UserCreate` – Password/confirm_password mismatch not enforced at model (API-level) | Model allows mismatch (API enforces) | `tests/test_models.py` |
| 2.5 | `UserLogin` – Valid email/password | Model created | `tests/test_models.py` |
| 2.6 | `VideoAnalysisRequest` – Default values correct | `count=5`, `tone="engaging"`, `keywords=[]` | `tests/test_models.py` |
| 2.7 | `VideoAnalysisRequest` – `count` out of range (0 or 11) | `ValidationError` | `tests/test_models.py` |
| 2.8 | `VideoAnalysisRequest` – Empty topic | `ValidationError` | `tests/test_models.py` |
| 2.9 | `TitleGenerationRequest` – Count 1-10 validation | Valid boundary checks | `tests/test_models.py` |
| 2.10 | `TagsGenerationRequest` – Count 1-30 validation | Valid boundary checks | `tests/test_models.py` |
| 2.11 | `UserSettingsUpdate` – Theme must be 'dark' or 'light' | `ValidationError` for invalid values | `tests/test_models.py` |
| 2.12 | `PasswordChange` – New password must be 8+ chars | `ValidationError` | `tests/test_models.py` |
| 2.13 | `SEOAnalysisRequest` – Score range 0-100 | Boundary tests | `tests/test_models.py` |
| 2.14 | All response models – Serialize/Deserialize round-trip | JSON → Model → JSON is identity | `tests/test_models.py` |

### 2.3 Content Generation Models (`app/models/content.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 2.15 | `GeneratedTitle` – Score field 0-100 | Boundary: -1 invalid, 0 valid, 100 valid, 101 invalid | `tests/test_models.py` |
| 2.16 | `GeneratedTitles` – Required fields check | `titles`, `topic`, `keywords`, `generated_at` present | `tests/test_models.py` |
| 2.17 | `GeneratedDescription` – `word_count` auto-calculated | Matches `len(description.split())` | `tests/test_models.py` |
| 2.18 | `VideoAnalysisResponse` – Full response shape | All 6 fields present | `tests/test_models.py` |

---

## 3. Phase 2: Backend Service Tests

### 3.1 AI Orchestrator (`ai_orchestrator.py`) – Extend Existing Tests

| # | Test Case | Expected Result | File |
|---|-----------|-----------------|------|
| 3.1 | Empty task bundle raises `ValueError` | `submit_bundle()` raises `ValueError` | `test_ai_orchestrator.py` (add) |
| 3.2 | `_build_batch_prompt` includes all task types | Prompt JSON contains `titles`, `description`, `tags` | `test_ai_orchestrator.py` (add) |
| 3.3 | `_build_batch_prompt` respects `count` and `count_tags` | Prompt requests exact counts | `test_ai_orchestrator.py` (add) |
| 3.4 | `_build_batch_prompt` with unknown task type | Unknown type included as free-form string field | `test_ai_orchestrator.py` (add) |
| 3.5 | `_enforce_rate_limit` waits minimum interval | At least 2s between consecutive calls | `test_ai_orchestrator.py` (add) |
| 3.6 | `_check_cooldown` raises 429 when cooldown active | HTTPException with status 429 | `test_ai_orchestrator.py` (add) |
| 3.7 | `_check_cooldown` passes when no cooldown | No exception raised | `test_ai_orchestrator.py` (add) |
| 3.8 | L1 cache miss falls through to L2 | L2 checked when L1 misses | `test_ai_orchestrator.py` (add) |
| 3.9 | L2 cache miss returns None | `_get_cached` returns `None` | `test_ai_orchestrator.py` (add) |
| 3.10 | Cache write to L1 + L2 succeeds | Both layers contain data | `test_ai_orchestrator.py` (add) |

### 3.2 AI Quota Manager (`ai_quota_manager.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.11 | `check_quota` returns `AVAILABLE` when under limit | `(QuotaStatus.AVAILABLE, "OK")` | `tests/test_ai_quota_manager.py` |
| 3.12 | `check_quota` returns `PER_MINUTE_LIMIT` when exceeded | `(QuotaStatus.PER_MINUTE_LIMIT, ...)` | `tests/test_ai_quota_manager.py` |
| 3.13 | `check_quota` returns `DAILY_LIMIT` when daily quota exhausted | `(QuotaStatus.DAILY_LIMIT, ...)` | `tests/test_ai_quota_manager.py` |
| 3.14 | `record_request` increments token counter | Counter increases by `tokens_used` | `tests/test_ai_quota_manager.py` |
| 3.15 | Quota resets after time window | Minute counter resets after 60s | `tests/test_ai_quota_manager.py` |
| 3.16 | `get_quota_info` returns correct stats | Returns dict with remaining, used, limit | `tests/test_ai_quota_manager.py` |
| 3.17 | RetryStrategy – max retries not exceeded | Stops after configured max_retries | `tests/test_ai_quota_manager.py` |
| 3.18 | RetryStrategy – exponential backoff increases delay | Each retry waits longer | `tests/test_ai_quota_manager.py` |

### 3.3 Auth Service (`auth_service.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.19 | `register_user` – Creates user in Supabase Auth | Returns Token with access_token, user | `tests/test_auth_service.py` |
| 3.20 | `register_user` – Duplicate email raises 409 | HTTPException with status 409 | `tests/test_auth_service.py` |
| 3.21 | `login_user` – Valid credentials returns token | Token with correct user data | `tests/test_auth_service.py` |
| 3.22 | `login_user` – Wrong password raises 401 | HTTPException with status 401 | `tests/test_auth_service.py` |
| 3.23 | `login_user` – Nonexistent email raises 401 | HTTPException with status 401 | `tests/test_auth_service.py` |
| 3.24 | `get_current_user` – Valid user ID returns profile | UserResponse with all fields | `tests/test_auth_service.py` |
| 3.25 | `get_current_user` – Invalid user ID raises 404 | HTTPException with status 404 | `tests/test_auth_service.py` |

### 3.4 User Service (`user_service.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.26 | `update_profile` – Partial update merges correctly | Only provided fields updated | `tests/test_user_service.py` |
| 3.27 | `update_profile` – Invalid username (too short) raises error | ValidationError or HTTPException 400 | `tests/test_user_service.py` |
| 3.28 | `change_password` – Correct current password succeeds | Success message returned | `tests/test_user_service.py` |
| 3.29 | `change_password` – Wrong current password raises 401 | HTTPException 401 | `tests/test_user_service.py` |
| 3.30 | `get_settings` – Returns defaults when no settings exist | Default settings created | `tests/test_user_service.py` |
| 3.31 | `update_settings` – Valid theme values accepted | Settings updated correctly | `tests/test_user_service.py` |
| 3.32 | `update_settings` – Invalid theme rejected | Error returned | `tests/test_user_service.py` |

### 3.5 SEO Service (`seo_service.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.33 | `analyze_video` – Valid video returns SEO analysis | VideoAnalysisResponse with score 0-100 | `tests/test_seo_service.py` |
| 3.34 | `analyze_video` – Missing video raises 404 | HTTPException 404 | `tests/test_seo_service.py` |
| 3.35 | `analyze_video` – Cached analysis returns without recomputing | Same result, `force_reanalysis=False` | `tests/test_seo_service.py` |
| 3.36 | `analyze_video` – `force_reanalysis=True` recomputes | New analysis with fresh timestamp | `tests/test_seo_service.py` |
| 3.37 | `get_video_reports` – Returns history ordered by date | Newest first | `tests/test_seo_service.py` |
| 3.38 | `get_video_reports` – No reports returns empty list | `[]` | `tests/test_seo_service.py` |
| 3.39 | Title length scoring – Short titles penalized | Score reduction for < 30 chars | `tests/test_seo_service.py` |
| 3.40 | Description scoring – Missing timestamps/CTAs penalized | Score reduction | `tests/test_seo_service.py` |

### 3.6 Content Service (`content_service.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.41 | `save_generated_content` stores content in DB | Returns saved record with ID | `tests/test_content_service.py` |
| 3.42 | `get_content_history` returns paginated results | Respects `limit` and `offset` | `tests/test_content_service.py` |
| 3.43 | `get_content_history` filters by `content_type` | Only matching types returned | `tests/test_content_service.py` |
| 3.44 | `get_content_by_id` returns specific record | Correct content returned | `tests/test_content_service.py` |
| 3.45 | `get_content_by_id` – Wrong user raises 404 | Record not found for other user | `tests/test_content_service.py` |
| 3.46 | `delete_content` removes from DB | Returns success | `tests/test_content_service.py` |
| 3.47 | `delete_content` – Nonexistent ID returns 404 | Not found | `tests/test_content_service.py` |
| 3.48 | `get_content_stats` returns aggregate stats | Count by type, total, recent | `tests/test_content_service.py` |

### 3.7 YouTube Service (`youtube_service.py` / `youtube_service_improved.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.49 | `get_oauth_url` returns valid Google OAuth URL | Starts with `https://accounts.google.com/o/oauth2/auth` | `tests/test_youtube_service.py` |
| 3.50 | `handle_oauth_callback` – Valid code exchanges for token | Channel data returned | `tests/test_youtube_service.py` |
| 3.51 | `handle_oauth_callback` – Invalid code raises error | HTTPException with detail | `tests/test_youtube_service.py` |
| 3.52 | `get_user_channels` returns connected channels | List of YouTubeChannelResponse | `tests/test_youtube_service.py` |
| 3.53 | `get_user_channels` – No channels returns `[]` | Empty list | `tests/test_youtube_service.py` |
| 3.54 | `sync_channel_videos` – Syncs new videos | Upserts into DB, returns count | `tests/test_youtube_service.py` |
| 3.55 | `sync_channel_videos` – Respects `max_results` | At most `max_results` videos fetched | `tests/test_youtube_service.py` |
| 3.56 | `get_channel_videos` – Returns videos ordered by date | Newest first | `tests/test_youtube_service.py` |
| 3.57 | `get_channel_videos` – Respects `limit` parameter | At most `limit` items | `tests/test_youtube_service.py` |

### 3.8 Trending Service (`trending_service.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.58 | `fetch_trending_videos` – Valid region returns videos | List of TrendingVideoResponse | `tests/test_trending_service.py` |
| 3.59 | `fetch_trending_videos` – Invalid region raises error | ValueError or HTTPException 400 | `tests/test_trending_service.py` |
| 3.60 | `get_trending_videos` – Filters by keywords | Only matching videos returned | `tests/test_trending_service.py` |
| 3.61 | `get_trending_videos` – Filters by `min_views` | Only videos with views >= threshold | `tests/test_trending_service.py` |
| 3.62 | `get_trending_videos` – Filters by `min_viral_score` | Only videos with score >= threshold | `tests/test_trending_service.py` |
| 3.63 | `analyze_trending_video` – Returns detailed analysis | Contains viral_score, niche_match, opportunity | `tests/test_trending_service.py` |
| 3.64 | `analyze_trending_video` – Missing video returns 404 | HTTPException 404 | `tests/test_trending_service.py` |
| 3.65 | `identify_content_opportunities` – Returns opportunities for niche | Opportunites with scores, competition, titles | `tests/test_trending_service.py` |
| 3.66 | `get_trending_stats` – Returns aggregate stats | Contains avg_views, top_categories, etc. | `tests/test_trending_service.py` |

### 3.9 Thumbnail Services (`nano_service.py`, `thumbnail_composer.py`, `thumbnail_template.py`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 3.67 | `nano_service.generate_thumbnail` – Valid input returns URL | Returns object with `image_url` | `tests/test_thumbnail_service.py` |
| 3.68 | `nano_service.generate_thumbnail` – API failure handled | Graceful error message | `tests/test_thumbnail_service.py` |
| 3.69 | `thumbnail_composer` – Composes valid thumbnail | Returns PIL Image object | `tests/test_thumbnail_service.py` |
| 3.70 | `thumbnail_template` – Templates have required fields | All templates have valid schema | `tests/test_thumbnail_service.py` |
| 3.71 | Thumbnail text generation (rule-based) – Returns suggestions | Always returns 3 suggestions | (Covered by `content.py` tests) |

---

## 4. Phase 3: API Integration Tests

### 4.1 Auth API (`/api/auth/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.1 | `POST /api/auth/register` – Full valid registration | 201 + Token with user data | `tests/test_api_auth.py` |
| 4.2 | `POST /api/auth/register` – Missing required fields | 422 Validation Error | `tests/test_api_auth.py` |
| 4.3 | `POST /api/auth/register` – Duplicate email | 409 Conflict | `tests/test_api_auth.py` |
| 4.4 | `POST /api/auth/login` – Valid credentials | 200 + Token | `tests/test_api_auth.py` |
| 4.5 | `POST /api/auth/login` – Wrong password | 401 Unauthorized | `tests/test_api_auth.py` |
| 4.6 | `POST /api/auth/login` – Nonexistent email | 401 Unauthorized | `tests/test_api_auth.py` |
| 4.7 | `GET /api/auth/me` – Valid token | 200 + UserResponse | `tests/test_api_auth.py` |
| 4.8 | `GET /api/auth/me` – Missing/expired token | 401 Unauthorized | `tests/test_api_auth.py` |
| 4.9 | `POST /api/auth/logout` – Authenticated | 200 + success message | `tests/test_api_auth.py` |
| 4.10 | `POST /api/auth/logout` – Unauthenticated | 401 | `tests/test_api_auth.py` |
| 4.11 | `POST /api/auth/refresh` – Valid token | 200 + new Token | `tests/test_api_auth.py` |
| 4.12 | `GET /api/auth/check` – Authenticated | 200 + `{"authenticated": true}` | `tests/test_api_auth.py` |

### 4.2 User API (`/api/users/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.13 | `GET /api/users/me` – Authenticated | 200 + UserResponse | `tests/test_api_users.py` |
| 4.14 | `PUT /api/users/me` – Update display_name | 200 + updated UserResponse | `tests/test_api_users.py` |
| 4.15 | `PUT /api/users/me` – Partial update | Only specified fields changed | `tests/test_api_users.py` |
| 4.16 | `PUT /api/users/me` – Unauthenticated | 401 | `tests/test_api_users.py` |
| 4.17 | `POST /api/users/change-password` – Correct current | 200 + success | `tests/test_api_users.py` |
| 4.18 | `POST /api/users/change-password` – Wrong current | 401 | `tests/test_api_users.py` |
| 4.19 | `POST /api/users/change-password` – Mismatch confirm | 422 | `tests/test_api_users.py` |
| 4.20 | `POST /api/users/avatar` – Valid image upload | 200 + avatar_url | `tests/test_api_users.py` |
| 4.21 | `POST /api/users/avatar` – File too large | 413 / 422 | `tests/test_api_users.py` |
| 4.22 | `DELETE /api/users/avatar` – Avatar exists | 200 + success | `tests/test_api_users.py` |
| 4.23 | `DELETE /api/users/avatar` – No avatar | 404 | `tests/test_api_users.py` |
| 4.24 | `GET /api/users/settings` – Authenticated | 200 + UserSettingsResponse | `tests/test_api_users.py` |
| 4.25 | `PUT /api/users/settings` – Update theme | 200 + updated settings | `tests/test_api_users.py` |
| 4.26 | `PUT /api/users/settings` – Invalid theme value | 422 | `tests/test_api_users.py` |

### 4.3 Content API (`/api/content/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.27 | `POST /api/content/generate/video-analysis` – Valid topic | 200 + VideoAnalysisResponse | `tests/test_api_content.py` |
| 4.28 | `POST /api/content/generate/video-analysis` – Empty topic | 400 Bad Request | `tests/test_api_content.py` |
| 4.29 | `POST /api/content/generate/video-analysis` – Quota exceeded | 429 + Retry-After header | `tests/test_api_content.py` |
| 4.30 | `POST /api/content/generate/video-analysis` – Cache hit | 200 + `cache_hit: true` | `tests/test_api_content.py` |
| 4.31 | `POST /api/content/generate/titles` – Valid request | 200 + GeneratedTitles | `tests/test_api_content.py` |
| 4.32 | `POST /api/content/generate/titles` – `count=0` | 400 | `tests/test_api_content.py` |
| 4.33 | `POST /api/content/generate/titles` – `count=10` (boundary) | 200 with 10 titles | `tests/test_api_content.py` |
| 4.34 | `POST /api/content/generate/description` – Valid request | 200 + GeneratedDescription | `tests/test_api_content.py` |
| 4.35 | `POST /api/content/generate/description` – `include_cta=false` | `includes_cta: false` | `tests/test_api_content.py` |
| 4.36 | `POST /api/content/generate/tags` – Valid request | 200 + GeneratedTags | `tests/test_api_content.py` |
| 4.37 | `POST /api/content/generate/tags` – `count=30` (max) | 200 with up to 30 tags | `tests/test_api_content.py` |
| 4.38 | `POST /api/content/generate/tags` – `count=0` | 400 | `tests/test_api_content.py` |
| 4.39 | `POST /api/content/generate/thumbnail-text` – Valid topic | 200 with 3 suggestions | `tests/test_api_content.py` |
| 4.40 | `POST /api/content/generate/thumbnail` – Valid request | 200 with image result | `tests/test_api_content.py` |
| 4.41 | `POST /api/content/generate/thumbnail` – Topic > 50 chars | 400 | `tests/test_api_content.py` |
| 4.42 | `GET /api/content/history` – Authenticated | 200 + list of history | `tests/test_api_content.py` |
| 4.43 | `GET /api/content/history` – Filter by content_type | Only matching type returned | `tests/test_api_content.py` |
| 4.44 | `GET /api/content/history` – Pagination (limit/offset) | Respects parameters | `tests/test_api_content.py` |
| 4.45 | `GET /api/content/history/{id}` – Existing content | 200 + content record | `tests/test_api_content.py` |
| 4.46 | `GET /api/content/history/{id}` – Wrong user | 404 | `tests/test_api_content.py` |
| 4.47 | `DELETE /api/content/history/{id}` – Existing content | 200 + success | `tests/test_api_content.py` |
| 4.48 | `GET /api/content/stats` – Authenticated | 200 with stats + quota | `tests/test_api_content.py` |
| 4.49 | `GET /api/content/quota/info` – Authenticated | 200 with quota info | `tests/test_api_content.py` |

### 4.4 SEO API (`/api/seo/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.50 | `POST /api/seo/analyze` – Valid video_id | 200 + VideoAnalysisResponse | `tests/test_api_seo.py` |
| 4.51 | `POST /api/seo/analyze` – Nonexistent video_id | 404 | `tests/test_api_seo.py` |
| 4.52 | `POST /api/seo/analyze` – `force_reanalysis=true` | Fresh analysis | `tests/test_api_seo.py` |
| 4.53 | `GET /api/seo/videos/{id}/reports` – Has reports | 200 + list | `tests/test_api_seo.py` |
| 4.54 | `GET /api/seo/videos/{id}/reports` – No reports | 200 + `[]` | `tests/test_api_seo.py` |
| 4.55 | `GET /api/seo/dashboard/stats` – Has analyzed videos | 200 with stats | `tests/test_api_seo.py` |
| 4.56 | `GET /api/seo/dashboard/stats` – No videos | 200 with `analyzed_videos: 0` | `tests/test_api_seo.py` |

### 4.5 YouTube API (`/api/youtube/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.57 | `GET /api/youtube/oauth/authorize` – With user_id | 302 redirect to Google OAuth URL | `tests/test_api_youtube.py` |
| 4.58 | `GET /api/youtube/oauth/authorize` – Missing user_id | 400 | `tests/test_api_youtube.py` |
| 4.59 | `GET /api/youtube/oauth/callback` – Valid code+state | 302 redirect to oauth-callback.html | `tests/test_api_youtube.py` |
| 4.60 | `GET /api/youtube/oauth/callback` – Error parameter | 302 with `?error=` | `tests/test_api_youtube.py` |
| 4.61 | `GET /api/youtube/oauth/callback` – Missing code | 302 with `?error=missing_parameters` | `tests/test_api_youtube.py` |
| 4.62 | `POST /api/youtube/oauth/exchange` – Valid code | 200 + channel data | `tests/test_api_youtube.py` |
| 4.63 | `POST /api/youtube/oauth/exchange` – Invalid code | 500 | `tests/test_api_youtube.py` |
| 4.64 | `GET /api/youtube/channels` – Has channels | 200 + list | `tests/test_api_youtube.py` |
| 4.65 | `GET /api/youtube/channels` – No channels | 200 + `[]` | `tests/test_api_youtube.py` |
| 4.66 | `POST /api/youtube/channels/{id}/sync` – Valid channel | 200 + ChannelSyncResponse | `tests/test_api_youtube.py` |
| 4.67 | `POST /api/youtube/channels/{id}/sync` – max_results=500 | 200, up to 500 synced | `tests/test_api_youtube.py` |
| 4.68 | `GET /api/youtube/channels/{id}/videos` – Has videos | 200 + list ordered by date | `tests/test_api_youtube.py` |
| 4.69 | `GET /api/youtube/channels/{id}/videos` – Empty | 200 + `[]` | `tests/test_api_youtube.py` |
| 4.70 | `DELETE /api/youtube/channels/{id}` – Own channel | 200 + success | `tests/test_api_youtube.py` |
| 4.71 | `DELETE /api/youtube/channels/{id}` – Not own channel | 404 (not found for this user) | `tests/test_api_youtube.py` |
| 4.72 | `DELETE /api/youtube/channels/{id}` – Nonexistent | 404 | `tests/test_api_youtube.py` |

### 4.6 Trending API (`/api/trending/*`)

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.73 | `POST /api/trending/fetch` – Valid region (US) | 200 + list of trending videos | `tests/test_api_trending.py` |
| 4.74 | `POST /api/trending/fetch` – With category_id | Filtered results | `tests/test_api_trending.py` |
| 4.75 | `POST /api/trending/fetch` – max_results=1 | Single result | `tests/test_api_trending.py` |
| 4.76 | `POST /api/trending/filter` – By keywords | Filtered results | `tests/test_api_trending.py` |
| 4.77 | `POST /api/trending/filter` – By min_views | Only high-view videos | `tests/test_api_trending.py` |
| 4.78 | `POST /api/trending/filter` – Combined filters | All filters applied | `tests/test_api_trending.py` |
| 4.79 | `GET /api/trending/videos/{id}/analyze` – With niche | 200 + TrendingAnalysis | `tests/test_api_trending.py` |
| 4.80 | `GET /api/trending/videos/{id}/analyze` – Without niche | 200 + analysis (no niche_match) | `tests/test_api_trending.py` |
| 4.81 | `GET /api/trending/videos/{id}/analyze` – Not found | 404 | `tests/test_api_trending.py` |
| 4.82 | `GET /api/trending/stats` – Region US | 200 + TrendingStatsResponse | `tests/test_api_trending.py` |
| 4.83 | `GET /api/trending/dashboard` – Region US | 200 + TrendingDashboardResponse | `tests/test_api_trending.py` |
| 4.84 | `GET /api/trending/opportunities` – Valid niche | 200 + list of ContentOpportunity | `tests/test_api_trending.py` |
| 4.85 | `GET /api/trending/opportunities` – `limit=1` | Single opportunity | `tests/test_api_trending.py` |
| 4.86 | `GET /api/trending/categories` | 200 + sorted categories list | `tests/test_api_trending.py` |
| 4.87 | `GET /api/trending/regions` | 200 + 15 regions | `tests/test_api_trending.py` |

### 4.7 Middleware & Error Handling

| # | Test Case | Expected Result | File to Create |
|---|-----------|-----------------|----------------|
| 4.88 | `GET /health` – Always returns healthy | 200 + `{"status": "healthy"}` | `tests/test_api_root.py` |
| 4.89 | `GET /` – Returns welcome message | 200 + `{"message": "Welcome to..."}` | `tests/test_api_root.py` |
| 4.90 | CORS headers present for allowed origin | `Access-Control-Allow-Origin` set | `tests/test_middleware.py` |
| 4.91 | CORS blocked for disallowed origin (production) | Origin not reflected in response | `tests/test_middleware.py` |
| 4.92 | 429 response includes `Retry-After` header | Header present in 429 response | `tests/test_middleware.py` |
| 4.93 | `X-Request-ID` header present in all responses | Header set for all requests | `tests/test_middleware.py` |
| 4.94 | Request logging middleware logs to stdout | Log entries for each request | `tests/test_middleware.py` |
| 4.95 | Unauthenticated request to protected endpoint → 401 | 401 + WWW-Authenticate header | `tests/test_api_auth.py` |
| 4.96 | Validation error for malformed JSON body | 422 with `errors` array | `tests/test_middleware.py` |

---

## 5. Phase 4: Frontend Tests

### 5.1 Authentication Flow (JS)

| # | Test Case | Expected Result | File |
|---|-----------|-----------------|------|
| 5.1 | `isAuthenticated()` – Token cookie present | Returns `true` | `js/auth.js` |
| 5.2 | `isAuthenticated()` – No token cookie | Returns `false` | `js/auth.js` |
| 5.3 | `isAuthenticated()` – Empty token | Returns `false` | `js/auth.js` |
| 5.4 | `getCurrentUserData()` – Valid user cookie | Returns parsed JSON | `js/auth.js` |
| 5.5 | `getCurrentUserData()` – No cookie | Returns `null` | `js/auth.js` |
| 5.6 | `saveUserData()` – Saves to cookie and localStorage | Both storage locations updated | `js/auth.js` |
| 5.7 | `clearAuthData()` – Clears all auth cookies/storage | All auth data removed | `js/auth.js` |
| 5.8 | `isTokenExpired()` – Token not expired | Returns `false` | `js/auth.js` |
| 5.9 | `isTokenExpired()` – Token expired | Returns `true` | `js/auth.js` |
| 5.10 | `requireAuth()` – Authenticated | Returns `true`, no redirect | `js/auth.js` |
| 5.11 | `requireAuth()` – Not authenticated | Redirects to `/auth.html` | `js/auth.js` |
| 5.12 | `redirectIfAuthenticated()` – Authenticated | Redirects to dashboard | `js/auth.js` |
| 5.13 | `redirectIfAuthenticated()` – Not authenticated | Returns `false`, no redirect | `js/auth.js` |
| 5.14 | `register()` – Success | Saves token, redirects to dashboard | `js/auth.js` |
| 5.15 | `register()` – API error | Shows error message | `js/auth.js` |
| 5.16 | `login()` – Success | Saves token, redirects to dashboard/saved page | `js/auth.js` |
| 5.17 | `login()` – API error | Shows error message | `js/auth.js` |
| 5.18 | `logout()` – API call + clear data | Redirects to `/auth.html` | `js/auth.js` |
| 5.19 | `validateRegistrationForm()` – Password too short | Throws Error | `js/auth.js` |
| 5.20 | `validateRegistrationForm()` – Invalid email | Throws Error | `js/auth.js` |
| 5.21 | `validateLoginForm()` – Missing password | Throws Error | `js/auth.js` |

### 5.2 API Client (`js/api.js`)

| # | Test Case | Expected Result | File |
|---|-----------|-----------------|------|
| 5.22 | `api.login()` – Sends POST with correct body | Calls `/api/auth/login` with JSON | `js/api.js` |
| 5.23 | `api.register()` – Sends POST with correct body | Calls `/api/auth/register` with JSON | `js/api.js` |
| 5.24 | `api.refreshToken()` – Sends POST with auth | Calls `/api/auth/refresh` | `js/api.js` |
| 5.25 | `api.getCurrentUser()` – Sends GET with auth | Calls `/api/auth/me` | `js/api.js` |
| 5.26 | `api.generateTitles()` – Sends POST with topic | Calls `/api/content/generate/titles` | `js/api.js` |
| 5.27 | `api.analyzeSEO()` – Sends POST with video data | Calls `/api/seo/analyze` | `js/api.js` |
| 5.28 | `api` – Sets Authorization header when token present | Header included | `js/api.js` |
| 5.29 | `api` – Handles 401 response | Calls `clearAuthData()`, redirects | `js/api.js` |
| 5.30 | `api` – Handles 429 response | Extracts Retry-After, notifies user | `js/api.js` |
| 5.31 | `api` – Handles network error | Returns/throws descriptive error | `js/api.js` |

### 5.3 Page Rendering & UI Logic

| # | Test Case | Expected Result | File |
|---|-----------|-----------------|------|
| 5.32 | `auth.html` – Tab switching (login ↔ signup) | Correct form shown, labels updated | `auth.html` |
| 5.33 | `auth.html` – Password visibility toggle | Password field toggles type | `auth.html` |
| 5.34 | `auth.html` – Password strength indicator | Bar updates on input | `auth.html` |
| 5.35 | `auth.html` – Google auth button shows toast | "Not yet configured" message | `auth.html` |
| 5.36 | `index.html` – Hero score ring animation | Ring animates on load | `index.html` |
| 5.37 | `dashboard.html` – Loads user data | Displays user name, email | `js/dashboard.js` |
| 5.38 | `dashboard.html` – Shows SEO stats | Dashboard metrics render | `js/dashboard.js` |
| 5.39 | `dashboard.html` – Error state | Shows error message gracefully | `js/dashboard.js` |
| 5.40 | `generator.html` – Generate titles button | Calls API, displays results | `js/generator.js` |
| 5.41 | `generator.html` – Loading state | Spinner shown during API call | `js/generator.js` |
| 5.42 | `generator.html` – Error state | Error message shown, not blank | `js/generator.js` |
| 5.43 | `analyzer.html` – Paste video URL → analysis form | URL parsed, form populated | `js/analyzer.js` |
| 5.44 | `analyzer.html` – SEO score visualization | Score ring/circle renders | `js/analyzer.js` |
| 5.45 | `trending.html` – Fetches trending data | Videos list rendered | `js/trending.js` |
| 5.46 | `trending.html` – Filter by category | Results filtered correctly | `js/trending.js` |
| 5.47 | `trending.html` – Error/no data state | Graceful empty state | `js/trending.js` |
| 5.48 | `channel.html` – OAuth redirect button | Redirects to `/api/youtube/oauth/authorize` | `js/channel.js` |
| 5.49 | `channel.html` – Connected channel display | Channel data rendered | `js/channel.js` |
| 5.50 | `oauth-callback.html` – Token exchange | Calls `/oauth/exchange`, saves channel | `pages/oauth-callback.html` |

### 5.4 Cookie Manager

| # | Test Case | Expected Result | File |
|---|-----------|-----------------|------|
| 5.51 | `CookieManager.setCookie()` – Creates cookie | Cookie with correct name, value, expiry | `js/cookie-manager.js` |
| 5.52 | `CookieManager.getCookie()` – Existing cookie | Returns value | `js/cookie-manager.js` |
| 5.53 | `CookieManager.getCookie()` – Missing cookie | Returns `null` | `js/cookie-manager.js` |
| 5.54 | `CookieManager.deleteCookie()` – Removes cookie | Cookie expired/removed | `js/cookie-manager.js` |
| 5.55 | `CookieManager.setCookie()` – Secure flag in production | `Secure` attribute set | `js/cookie-manager.js` |

---

## 6. Phase 5: End-to-End Tests

These test the full user journey through the application.

| # | Test Scenario | Steps | Expected Result |
|---|---------------|-------|-----------------|
| 6.1 | **User Registration → Login → Dashboard** | 1. Visit landing page → 2. Click "Get Started" → 3. Fill signup form → 4. Submit → 5. Dashboard loads | User created, logged in, dashboard shows empty state |
| 6.2 | **Login → AI Content Generation** | 1. Login → 2. Navigate to Generator → 3. Enter topic → 4. Click Generate → 5. View titles/desc/tags | All three outputs rendered within 10s |
| 6.3 | **Login → SEO Analysis** | 1. Login → 2. Navigate to Analyzer → 3. Enter video URL → 4. Click Analyze → 5. View SEO score | Score, criteria breakdown, suggestions shown |
| 6.4 | **Login → Trending Topics** | 1. Login → 2. Navigate to Trending → 3. Select region → 4. Browse trending → 5. Filter by category | Trending videos load, filter works |
| 6.5 | **YouTube Channel Connection** | 1. Login → 2. Click "Connect YouTube" → 3. Google OAuth consent → 4. Authorize → 5. Redirect to app | Channel appears in channels list |
| 6.6 | **Full Content Workflow** | 1. Connect YouTube → 2. Sync videos → 3. Analyze a video → 4. Generate optimized titles/desc/tags → 5. View history | Complete workflow succeeds |
| 6.7 | **Quota Exhaustion** | 1. Generate content until quota exceeded → 2. See 429 error → 3. Retry-After countdown → 4. Wait → 5. Retry succeeds | 429 shown, countdown UI, retry works |
| 6.8 | **Session Expiry** | 1. Login → 2. Wait 30+ minutes (or manipulate token) → 3. Try to access dashboard → 4. Redirected to login | Auto-redirect to auth page |
| 6.9 | **Password Change** | 1. Login → 2. Go to Settings → 3. Change password → 4. Logout → 5. Login with new password | New password works, old password fails |
| 6.10 | **Mobile Responsiveness** | Resize browser to mobile widths on all pages | All pages readable, nav collapses to hamburger |

---

## 7. Phase 6: Performance & Edge Cases

### 7.1 Performance Tests

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 7.1 | Concurrent auth registrations (10 simultaneous) | All succeed or rate-limited gracefully |
| 7.2 | Content generation with very long topic (1000 chars) | 400 error (reasonable limit) |
| 7.3 | Content generation with special characters/emoji | Handles gracefully |
| 7.4 | Trending API with all regions simultaneously | Returns data without timeout |
| 7.5 | Video sync with 500 max_results | Completes within reasonable time |
| 7.6 | Cache L1 hit time < 5ms | In-memory cache is near-instant |
| 7.7 | Cache L2 hit time < 100ms | DB lookup is fast |

### 7.2 Security Tests

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 7.8 | JWT token tampering (modified payload) | `decode_access_token` returns `None` |
| 7.9 | JWT token replay (old token after password change) | Rejected (or logged out) |
| 7.10 | SQL injection in user_id parameter | Supabase client sanitizes |
| 7.11 | XSS in topic/description fields | Frontend escapes HTML |
| 7.12 | CORS: production origin restriction | Origins not in ALLOWED_ORIGINS blocked |
| 7.13 | Rate limiting: too many rapid requests | 429 returned with Retry-After |

### 7.3 Edge Cases

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 7.14 | Empty string topic | 400 error |
| 7.15 | Topic with only whitespace | 400 error or trimmed |
| 7.16 | Extremely long title count (1000) | API validates and rejects |
| 7.17 | Unicode/emoji in topic | Handled correctly |
| 7.18 | Supabase connection timeout | Service returns meaningful error |
| 7.19 | Gemini API returns empty response | Fallback to `null` for each field |
| 7.20 | Gemini API returns malformed JSON | `_parse_batch_response` returns all `None` |
| 7.21 | Gemini API returns markdown-wrapped JSON | Parsed correctly |
| 7.22 | Duplicate keyword submission | Deduplicated or accepted |
| 7.23 | Avatar upload with unsupported format (SVG) | Rejected with 422 |
| 7.24 | Avatar upload with 0-byte file | Rejected |

---

## 8. Running the Tests

### 8.1 Backend Tests (pytest)

```bash
# Navigate to backend directory
cd vantagetube-ai/backend

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_ai_orchestrator.py -v

# Run specific test class
python -m pytest tests/test_ai_orchestrator.py::TestVideoAnalysisBundle -v

# Run property-based tests (more examples)
python -m pytest tests/test_ai_orchestrator_properties.py -v --hypothesis-show-statistics

# Run tests matching keyword
python -m pytest tests/ -v -k "quota"

# Run with xdist (parallel execution)
python -m pytest tests/ -v -n 4
```

### 8.2 Manual API Testing

```bash
# Test all APIs sequentially
cd vantagetube-ai/backend
python test_all_apis.py

# Test specific endpoints
python test_connection.py    # Supabase connection
python test_nano_api.py      # Nano thumbnail API
```

### 8.3 Frontend Testing (Manual / Browser)

```bash
# Open pages in browser for visual testing
cd vantagetube-ai/frontend

# Using Python's HTTP server
python -m http.server 3000

# Using Live Server (VS Code extension)
# Right-click index.html → Open with Live Server
```

### 8.4 Supabase Verification

```bash
# Test Supabase connection
cd vantagetube-ai/backend
python test_connection.py

# Expected output:
# ✅ Connected to Supabase
# ✅ Auth connection verified
# ✅ Database schema present (tables: users, youtube_channels, etc.)
```

### 8.5 Swagger UI Testing

```bash
# Start backend server
cd vantagetube-ai/backend
uvicorn app.main:app --reload --port 8000

# Open in browser
# http://localhost:8000/docs
# http://localhost:8000/redoc
```

---

## 9. Test Coverage Matrix

### Legend: ✅ = Tests written, ⬜ = Tests needed, 🔄 = Tests partially exist

| Module | Unit Tests | Integration | Total Cases | Priority |
|--------|-----------|-------------|-------------|----------|
| **Core Configuration** | ⬜ | ⬜ | 3 | High |
| **Security (JWT/Password)** | ⬜ | ⬜ | 6 | High |
| **Models** | ⬜ | - | 18 | High |
| **Auth API** | ⬜ | ⬜ | 12 | Critical |
| **Users API** | ⬜ | ⬜ | 14 | High |
| **Content API** | ⬜ | ⬜ | 23 | Critical |
| **Content Models** | ⬜ | - | 4 | High |
| **SEO API** | ⬜ | ⬜ | 8 | High |
| **YouTube API** | ⬜ | ⬜ | 16 | Medium |
| **Trending API** | ⬜ | ⬜ | 15 | Medium |
| **AI Orchestrator** | ✅/🔄 | ⬜ | 10 new | Critical |
| **AI Quota Manager** | ⬜ | ⬜ | 8 | Critical |
| **Auth Service** | ⬜ | - | 7 | Critical |
| **User Service** | ⬜ | - | 7 | High |
| **SEO Service** | ⬜ | - | 8 | High |
| **Content Service** | ⬜ | - | 8 | High |
| **YouTube Service** | ⬜ | - | 9 | Medium |
| **Trending Service** | ⬜ | - | 9 | Medium |
| **Thumbnail Service** | ⬜ | - | 5 | Low |
| **Middleware** | - | ⬜ | 6 | High |
| **Frontend Auth JS** | - | ⬜ | 21 | High |
| **Frontend API JS** | - | ⬜ | 10 | High |
| **Frontend Pages** | - | ⬜ | 19 | Medium |
| **Cookie Manager** | - | ⬜ | 5 | Medium |
| **E2E Scenarios** | - | ⬜ | 10 | Medium |
| **Performance/Security** | - | ⬜ | 15 | Low |
| **Edge Cases** | - | ⬜ | 11 | Medium |

### Priority Guide

| Priority | Meaning | Estimated Tests |
|----------|---------|-----------------|
| **Critical** | Must pass for core functionality | ~60 |
| **High** | Important for reliability | ~50 |
| **Medium** | Nice-to-have validation | ~70 |
| **Low** | Polish and edge cases | ~30 |

### Current vs Target Coverage

| Metric | Current | Target |
|--------|---------|--------|
| Backend unit+integration tests | 2 files (37 tests) | 12+ files (210 tests) |
| Frontend tests | 0 | 60+ test cases |
| E2E scenarios | 0 | 10 |
| Property-based tests | 1 file (12 properties) | 2 files (20+ properties) |
| Code coverage (backend) | ~15% | >80% |

---

## Test File Structure (Proposed)

```
vantagetube-ai/backend/tests/
├── __init__.py
├── test_core.py                 # Config, security, supabase
├── test_models.py               # All Pydantic model validation
├── test_api_auth.py             # Auth endpoints (register, login, me, etc.)
├── test_api_users.py            # User endpoints
├── test_api_content.py          # Content generation endpoints
├── test_api_seo.py              # SEO analysis endpoints
├── test_api_youtube.py          # YouTube integration endpoints
├── test_api_trending.py         # Trending topics endpoints
├── test_api_root.py             # Health, root, middleware
├── test_middleware.py           # CORS, logging, 429 handler
├── test_auth_service.py         # AuthService unit tests
├── test_user_service.py         # UserService unit tests
├── test_seo_service.py          # SEOService unit tests
├── test_content_service.py      # ContentService unit tests
├── test_youtube_service.py      # YouTubeService unit tests
├── test_trending_service.py     # TrendingService unit tests
├── test_thumbnail_service.py    # Thumbnail/nano service tests
├── test_ai_quota_manager.py     # QuotaManager + RetryStrategy
├── test_ai_orchestrator.py      # Existing + new tests (extend)
├── test_ai_orchestrator_properties.py  # Existing (keep as-is)
├── conftest.py                  # Fixtures (test client, auth headers, mock DB)
└── ...
```

---

## Quick Start: Running the First Batch of Tests

### Step 1: Run existing tests to verify environment

```bash
cd vantagetube-ai/backend
python -m pytest tests/test_ai_orchestrator.py -v
python -m pytest tests/test_ai_orchestrator_properties.py -v
```

### Step 2: Create `conftest.py` with shared fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "test-user-id", "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_topic():
    return "How to learn Python programming in 2024"
```

### Step 3: Run a first integration test

```bash
# After creating test_api_auth.py
python -m pytest tests/test_api_auth.py -v
```

---

## Conclusion

This test plan covers **~210 test cases** across all layers of the VantageTube AI platform:

- **Backend unit tests**: 60+ model, service, and orchestrator tests  
- **API integration tests**: 96 endpoint tests covering all 6 router groups  
- **Frontend tests**: 55+ JS logic and page rendering tests  
- **End-to-end**: 10 full user journey scenarios  
- **Performance/Security/Edge Cases**: 30+ additional scenarios  

**Priority order for implementation:**
1. Auth API tests (critical for all other endpoints)  
2. AI Orchestrator extension tests (core AI engine)  
3. Content API tests (primary user-facing feature)  
4. User API tests  
5. SEO API tests  
6. Frontend auth + API JS tests  
7. YouTube + Trending API tests  
8. Performance and edge cases