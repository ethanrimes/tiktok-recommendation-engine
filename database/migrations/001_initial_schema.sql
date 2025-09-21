-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    tag VARCHAR(100) PRIMARY KEY,
    description TEXT NOT NULL,
    keywords JSONB DEFAULT '[]',
    embedding JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create user profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    username VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    sec_uid VARCHAR(100),
    bio TEXT,
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user tags table
CREATE TABLE IF NOT EXISTS user_tags (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) REFERENCES user_profiles(username),
    tag VARCHAR(100) REFERENCES categories(tag),
    affinity FLOAT NOT NULL CHECK (affinity >= 0 AND affinity <= 1),
    reason TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(username, tag)
);

-- Create recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) REFERENCES user_profiles(username),
    video_id VARCHAR(100) NOT NULL,
    description TEXT,
    author VARCHAR(100),
    url TEXT,
    score FLOAT NOT NULL,
    virality_score FLOAT,
    relevance_score FLOAT,
    engagement_score FLOAT,
    matched_tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create API cache table
CREATE TABLE IF NOT EXISTS api_cache (
    key VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create pipeline results table
CREATE TABLE IF NOT EXISTS pipeline_results (
    id SERIAL PRIMARY KEY,
    pipeline VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pipeline, key)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_tags_username ON user_tags(username);
CREATE INDEX IF NOT EXISTS idx_user_tags_tag ON user_tags(tag);
CREATE INDEX IF NOT EXISTS idx_recommendations_username ON recommendations(username);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at ON api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_results_pipeline_key ON pipeline_results(pipeline, key);