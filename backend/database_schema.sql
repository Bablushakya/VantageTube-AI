-- ============================================
-- VantageTube AI - Supabase Database Schema
-- ============================================
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(150),
    username VARCHAR(50) UNIQUE,
    country VARCHAR(2),
    niche VARCHAR(50),
    bio TEXT,
    avatar_url TEXT,
    plan VARCHAR(20) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================
-- YOUTUBE CHANNELS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS youtube_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id VARCHAR(100) UNIQUE NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    channel_handle VARCHAR(100),
    channel_url TEXT,
    thumbnail_url TEXT,
    subscriber_count BIGINT DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    description TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    oauth_access_token TEXT,
    oauth_refresh_token TEXT,
    oauth_token_expires_at TIMESTAMP WITH TIME ZONE,
    is_connected BOOLEAN DEFAULT true,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_youtube_channels_user_id ON youtube_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_youtube_channels_channel_id ON youtube_channels(channel_id);

-- ============================================
-- VIDEOS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES youtube_channels(id) ON DELETE CASCADE,
    video_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    duration INTEGER, -- in seconds
    view_count BIGINT DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[], -- Array of tags
    category_id VARCHAR(50),
    seo_score INTEGER CHECK (seo_score >= 0 AND seo_score <= 100),
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_seo_score ON videos(seo_score);

-- ============================================
-- SEO REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS seo_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    title_score INTEGER CHECK (title_score >= 0 AND title_score <= 100),
    description_score INTEGER CHECK (description_score >= 0 AND description_score <= 100),
    tags_score INTEGER CHECK (tags_score >= 0 AND tags_score <= 100),
    thumbnail_score INTEGER CHECK (thumbnail_score >= 0 AND thumbnail_score <= 100),
    engagement_score INTEGER CHECK (engagement_score >= 0 AND engagement_score <= 100),
    suggestions JSONB, -- Array of improvement suggestions
    criteria_breakdown JSONB, -- Detailed breakdown of each criterion
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_seo_reports_user_id ON seo_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_seo_reports_video_id ON seo_reports(video_id);
CREATE INDEX IF NOT EXISTS idx_seo_reports_created_at ON seo_reports(created_at DESC);

-- ============================================
-- GENERATED CONTENT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('title', 'description', 'tags', 'thumbnail')),
    input_data JSONB, -- Original input provided by user
    generated_data JSONB NOT NULL, -- AI-generated content
    model_used VARCHAR(100), -- e.g., 'gpt-4', 'gpt-3.5-turbo'
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_generated_content_user_id ON generated_content(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_video_id ON generated_content(video_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_type ON generated_content(content_type);
CREATE INDEX IF NOT EXISTS idx_generated_content_created_at ON generated_content(created_at DESC);

-- ============================================
-- TRENDING TOPICS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS trending_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    niche VARCHAR(50) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    description TEXT,
    search_volume INTEGER,
    competition_level VARCHAR(20) CHECK (competition_level IN ('low', 'medium', 'high')),
    viral_score INTEGER CHECK (viral_score >= 0 AND viral_score <= 100),
    trend_type VARCHAR(20) CHECK (trend_type IN ('exploding', 'rising', 'steady', 'declining')),
    keywords TEXT[],
    related_videos JSONB, -- Array of related video data
    data_source VARCHAR(50), -- e.g., 'youtube_api', 'google_trends'
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_trending_topics_niche ON trending_topics(niche);
CREATE INDEX IF NOT EXISTS idx_trending_topics_viral_score ON trending_topics(viral_score DESC);
CREATE INDEX IF NOT EXISTS idx_trending_topics_fetched_at ON trending_topics(fetched_at DESC);

-- ============================================
-- USER SETTINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark' CHECK (theme IN ('dark', 'light')),
    accent_color VARCHAR(7) DEFAULT '#6C63FF',
    font_size VARCHAR(20) DEFAULT 'normal' CHECK (font_size IN ('small', 'normal', 'large')),
    compact_mode BOOLEAN DEFAULT false,
    email_notifications BOOLEAN DEFAULT true,
    weekly_seo_report BOOLEAN DEFAULT true,
    trending_alerts BOOLEAN DEFAULT true,
    feature_updates BOOLEAN DEFAULT false,
    milestone_alerts BOOLEAN DEFAULT true,
    profile_visibility BOOLEAN DEFAULT true,
    analytics_sharing BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE youtube_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- YouTube channels policies
CREATE POLICY "Users can view own channels" ON youtube_channels
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own channels" ON youtube_channels
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own channels" ON youtube_channels
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own channels" ON youtube_channels
    FOR DELETE USING (auth.uid() = user_id);

-- Videos table policies
CREATE POLICY "Users can view own videos" ON videos
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own videos" ON videos
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own videos" ON videos
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own videos" ON videos
    FOR DELETE USING (auth.uid() = user_id);

-- SEO reports policies
CREATE POLICY "Users can view own reports" ON seo_reports
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own reports" ON seo_reports
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Generated content policies
CREATE POLICY "Users can view own generated content" ON generated_content
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own generated content" ON generated_content
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- User settings policies
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

-- Trending topics (public read access)
CREATE POLICY "Anyone can view trending topics" ON trending_topics
    FOR SELECT USING (true);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_youtube_channels_updated_at BEFORE UPDATE ON youtube_channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- Insert some sample trending topics (optional for testing)
-- You can remove this in production
INSERT INTO trending_topics (niche, topic, description, search_volume, competition_level, viral_score, trend_type, keywords)
VALUES 
    ('tech', 'AI Tools for Productivity', 'Latest AI-powered productivity tools and apps', 125000, 'high', 92, 'exploding', ARRAY['AI', 'productivity', 'automation', 'tools']),
    ('tech', 'iPhone 16 Review', 'Comprehensive review of the latest iPhone', 89000, 'high', 85, 'rising', ARRAY['iPhone', 'Apple', 'smartphone', 'review']),
    ('gaming', 'Best Indie Games 2024', 'Top indie games released this year', 45000, 'medium', 78, 'steady', ARRAY['indie games', 'gaming', '2024', 'recommendations'])
ON CONFLICT DO NOTHING;

-- ============================================
-- NOTES
-- ============================================
-- 1. Make sure to enable Row Level Security (RLS) in Supabase dashboard
-- 2. Configure authentication providers (Email, Google OAuth) in Supabase Auth settings
-- 3. Set up storage buckets for avatars and thumbnails if needed
-- 4. Update CORS settings in Supabase to allow your frontend domain
-- 5. Generate and save your Supabase URL and keys in .env file
