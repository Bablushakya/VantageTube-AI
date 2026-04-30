-- AI Content Generator API - Database Schema Migration
-- This migration creates all necessary tables for the AI Content Generator feature

-- ==================== Generated Content Table ====================
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id VARCHAR(255),
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('title', 'tags', 'description', 'thumbnail_text')),
    content JSONB NOT NULL,
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 100),
    prompt_used TEXT,
    batch_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (batch_id) REFERENCES generation_batches(id) ON DELETE SET NULL
);

-- ==================== Generation Batches Table ====================
CREATE TABLE IF NOT EXISTS generation_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    batch_type VARCHAR(50) NOT NULL CHECK (batch_type IN ('single', 'batch')),
    topic VARCHAR(500),
    keywords TEXT[],
    tone VARCHAR(50),
    target_audience VARCHAR(255),
    video_length VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================== Generation History Table ====================
CREATE TABLE IF NOT EXISTS generation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_id UUID REFERENCES generated_content(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('generated', 'regenerated', 'edited', 'deleted')),
    content_type VARCHAR(50),
    quality_score FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ==================== User Generation Preferences Table ====================
CREATE TABLE IF NOT EXISTS user_generation_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    preferred_tone VARCHAR(50),
    preferred_keywords TEXT[],
    preferred_audience VARCHAR(255),
    liked_content_ids UUID[],
    disliked_content_ids UUID[],
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================== Generation Statistics Cache Table ====================
CREATE TABLE IF NOT EXISTS generation_stats_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    total_generations INT DEFAULT 0,
    by_type JSONB DEFAULT '{"title": 0, "tags": 0, "description": 0, "thumbnail_text": 0}',
    avg_quality_score FLOAT DEFAULT 0,
    most_used_keywords TEXT[] DEFAULT '{}',
    most_used_tones TEXT[] DEFAULT '{}',
    generation_trends JSONB DEFAULT '{}',
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- ==================== Indexes for Performance ====================

-- Generated Content Indexes
CREATE INDEX IF NOT EXISTS idx_generated_content_user_id ON generated_content(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_created_at ON generated_content(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_content_content_type ON generated_content(content_type);
CREATE INDEX IF NOT EXISTS idx_generated_content_batch_id ON generated_content(batch_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_user_type ON generated_content(user_id, content_type);

-- Generation Batches Indexes
CREATE INDEX IF NOT EXISTS idx_generation_batches_user_id ON generation_batches(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_batches_created_at ON generation_batches(created_at DESC);

-- Generation History Indexes
CREATE INDEX IF NOT EXISTS idx_generation_history_user_id ON generation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_history_timestamp ON generation_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_generation_history_content_id ON generation_history(content_id);

-- User Preferences Indexes
CREATE INDEX IF NOT EXISTS idx_user_generation_preferences_user_id ON user_generation_preferences(user_id);

-- Stats Cache Indexes
CREATE INDEX IF NOT EXISTS idx_generation_stats_cache_user_id ON generation_stats_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_stats_cache_expires_at ON generation_stats_cache(expires_at);

-- ==================== Triggers for Automatic Timestamps ====================

-- Trigger for generated_content updated_at
CREATE OR REPLACE FUNCTION update_generated_content_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generated_content_updated_at
BEFORE UPDATE ON generated_content
FOR EACH ROW
EXECUTE FUNCTION update_generated_content_timestamp();

-- Trigger for generation_batches updated_at
CREATE OR REPLACE FUNCTION update_generation_batches_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generation_batches_updated_at
BEFORE UPDATE ON generation_batches
FOR EACH ROW
EXECUTE FUNCTION update_generation_batches_timestamp();

-- Trigger for user_generation_preferences updated_at
CREATE OR REPLACE FUNCTION update_user_generation_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_generation_preferences_updated_at
BEFORE UPDATE ON user_generation_preferences
FOR EACH ROW
EXECUTE FUNCTION update_user_generation_preferences_timestamp();

-- ==================== Row Level Security (RLS) Policies ====================

-- Enable RLS on all tables
ALTER TABLE generated_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_generation_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_stats_cache ENABLE ROW LEVEL SECURITY;

-- Generated Content RLS Policies
CREATE POLICY "Users can view their own generated content"
ON generated_content FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own generated content"
ON generated_content FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own generated content"
ON generated_content FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own generated content"
ON generated_content FOR DELETE
USING (auth.uid() = user_id);

-- Generation Batches RLS Policies
CREATE POLICY "Users can view their own generation batches"
ON generation_batches FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own generation batches"
ON generation_batches FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own generation batches"
ON generation_batches FOR DELETE
USING (auth.uid() = user_id);

-- Generation History RLS Policies
CREATE POLICY "Users can view their own generation history"
ON generation_history FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own generation history"
ON generation_history FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- User Preferences RLS Policies
CREATE POLICY "Users can view their own preferences"
ON user_generation_preferences FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own preferences"
ON user_generation_preferences FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own preferences"
ON user_generation_preferences FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Stats Cache RLS Policies
CREATE POLICY "Users can view their own stats cache"
ON generation_stats_cache FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own stats cache"
ON generation_stats_cache FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own stats cache"
ON generation_stats_cache FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- ==================== Comments for Documentation ====================

COMMENT ON TABLE generated_content IS 'Stores all generated content (titles, tags, descriptions, thumbnail text) for users';
COMMENT ON TABLE generation_batches IS 'Tracks batch generation requests and their parameters';
COMMENT ON TABLE generation_history IS 'Audit trail of all generation activities';
COMMENT ON TABLE user_generation_preferences IS 'Stores user preferences for content generation';
COMMENT ON TABLE generation_stats_cache IS 'Cached statistics for user generation activity';

COMMENT ON COLUMN generated_content.content_type IS 'Type of generated content: title, tags, description, or thumbnail_text';
COMMENT ON COLUMN generated_content.quality_score IS 'Quality score (0-100) assigned to generated content';
COMMENT ON COLUMN generation_batches.batch_type IS 'Type of batch: single or batch generation';
COMMENT ON COLUMN generation_history.action IS 'Action performed: generated, regenerated, edited, or deleted';
