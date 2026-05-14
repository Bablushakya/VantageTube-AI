-- VantageTube AI - Supabase Database Migration
-- Run this SQL in the Supabase SQL Editor to create missing tables

-- ============================================================
-- TABLE: api_quota_usage
-- Tracks per-user API quota consumption per time window
-- ============================================================
CREATE TABLE IF NOT EXISTS public.api_quota_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    window_minute TIMESTAMPTZ NOT NULL DEFAULT now(),
    window_hour TIMESTAMPTZ NOT NULL DEFAULT date_trunc('hour', now()),
    window_day TIMESTAMPTZ NOT NULL DEFAULT date_trunc('day', now()),
    request_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, window_minute)
);

-- Index for fast quota lookups
CREATE INDEX IF NOT EXISTS idx_quota_user_window 
    ON public.api_quota_usage(user_id, window_minute DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE public.api_quota_usage ENABLE ROW LEVEL SECURITY;

-- Users can only see their own quota
CREATE POLICY quota_user_policy ON public.api_quota_usage
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================
-- TABLE: ai_cache
-- Caches AI generation results to reduce Gemini API calls
-- ============================================================
CREATE TABLE IF NOT EXISTS public.ai_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, content_type, prompt_hash)
);

-- Index for fast cache lookups
CREATE INDEX IF NOT EXISTS idx_cache_lookup 
    ON public.ai_cache(user_id, content_type, prompt_hash);

-- Cleanup old cache entries (older than 7 days)
CREATE INDEX IF NOT EXISTS idx_cache_created 
    ON public.ai_cache(created_at);

-- Enable RLS
ALTER TABLE public.ai_cache ENABLE ROW LEVEL SECURITY;

-- Users can only access their own cache
CREATE POLICY cache_user_policy ON public.ai_cache
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================
-- TABLE: video_analytics_cache
-- Caches YouTube Analytics API responses per video
-- to reduce API quota consumption and improve load times
-- ============================================================
CREATE TABLE IF NOT EXISTS public.video_analytics_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    analytics_json JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '1 hour'),
    UNIQUE(user_id, video_id)
);

-- Index for fast cache lookups
CREATE INDEX IF NOT EXISTS idx_video_analytics_lookup
    ON public.video_analytics_cache(user_id, video_id);

-- Index for cache cleanup
CREATE INDEX IF NOT EXISTS idx_video_analytics_expires
    ON public.video_analytics_cache(expires_at);

-- Enable RLS
ALTER TABLE public.video_analytics_cache ENABLE ROW LEVEL SECURITY;

-- Users can only access their own analytics cache
CREATE POLICY video_analytics_cache_policy ON public.video_analytics_cache
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================
-- FUNCTION: increment_quota
-- Atomic increment for quota counters (fixes ISSUE-010)
-- ============================================================
CREATE OR REPLACE FUNCTION public.increment_quota(
    p_user_id UUID,
    p_tokens INTEGER DEFAULT 0
) RETURNS VOID AS $$
DECLARE
    v_minute TIMESTAMPTZ := date_trunc('minute', now());
    v_hour TIMESTAMPTZ := date_trunc('hour', now());
    v_day TIMESTAMPTZ := date_trunc('day', now());
BEGIN
    INSERT INTO public.api_quota_usage 
        (user_id, window_minute, window_hour, window_day, request_count, token_count)
    VALUES 
        (p_user_id, v_minute, v_hour, v_day, 1, p_tokens)
    ON CONFLICT (user_id, window_minute) 
    DO UPDATE SET 
        request_count = api_quota_usage.request_count + 1,
        token_count = api_quota_usage.token_count + p_tokens;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCTION: cleanup_expired_analytics_cache
-- Removes stale analytics cache entries
-- ============================================================
CREATE OR REPLACE FUNCTION public.cleanup_expired_analytics_cache()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM public.video_analytics_cache 
    WHERE expires_at < now();
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCTION: cleanup_expired_cache
-- Removes cache entries older than N days
-- ============================================================
CREATE OR REPLACE FUNCTION public.cleanup_expired_cache(
    p_max_age_days INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM public.ai_cache 
    WHERE created_at < now() - (p_max_age_days || ' days')::INTERVAL;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT ALL ON public.api_quota_usage TO authenticated;
GRANT ALL ON public.api_quota_usage TO service_role;
GRANT ALL ON public.ai_cache TO authenticated;
GRANT ALL ON public.ai_cache TO service_role;
GRANT ALL ON public.video_analytics_cache TO authenticated;
GRANT ALL ON public.video_analytics_cache TO service_role;
GRANT EXECUTE ON FUNCTION public.increment_quota TO authenticated;
GRANT EXECUTE ON FUNCTION public.increment_quota TO service_role;
GRANT EXECUTE ON FUNCTION public.cleanup_expired_cache TO service_role;
GRANT EXECUTE ON FUNCTION public.cleanup_expired_analytics_cache TO service_role;

-- Notify
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: api_quota_usage, ai_cache, video_analytics_cache tables created';
END $$;