-- ==============================================================================
-- SMART BOT OS v5.0 — SUPABASE POSTGRESQL PRODUCTION SCHEMA
-- Run this SQL in the Supabase SQL Editor to initialize all Beta Launch tables.
-- ==============================================================================

-- 1. Beta Users Table (Discord OAuth Accounts)
CREATE TABLE IF NOT EXISTS beta_users (
    id BIGSERIAL PRIMARY KEY,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    avatar TEXT,
    is_owner BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DOUBLE PRECISION NOT NULL
);

-- 2. Beta Servers Table
CREATE TABLE IF NOT EXISTS beta_servers (
    guild_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    member_count INT NOT NULL DEFAULT 0,
    owner_id TEXT,
    plan TEXT NOT NULL DEFAULT 'Free Beta',
    health_score INT NOT NULL DEFAULT 85,
    created_at DOUBLE PRECISION NOT NULL
);

-- 3. Beta Server Memory Table ("What Smart Bot learned")
CREATE TABLE IF NOT EXISTS beta_server_memory (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    type TEXT NOT NULL, -- 'RULE', 'DECISION', 'PROBLEM', 'FAQ', 'EVENT'
    content TEXT NOT NULL,
    summary TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.90,
    status TEXT NOT NULL DEFAULT 'active',
    created_at DOUBLE PRECISION NOT NULL
);

-- 4. Beta Community Reports Table
CREATE TABLE IF NOT EXISTS beta_reports (
    id BIGSERIAL PRIMARY KEY,
    server_id BIGINT NOT NULL,
    report_data JSONB NOT NULL,
    date TEXT NOT NULL,
    created_at DOUBLE PRECISION NOT NULL
);

-- 5. Beta Feedback & Feature Requests Table
CREATE TABLE IF NOT EXISTS beta_feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    server_id BIGINT NOT NULL,
    author_name TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    status TEXT NOT NULL DEFAULT 'open',
    votes INT NOT NULL DEFAULT 1,
    created_at DOUBLE PRECISION NOT NULL
);

-- 6. Beta Events & Telemetry Table
CREATE TABLE IF NOT EXISTS beta_events (
    id BIGSERIAL PRIMARY KEY,
    server_id BIGINT NOT NULL,
    feature_used TEXT NOT NULL,
    metadata JSONB,
    timestamp DOUBLE PRECISION NOT NULL
);

-- Indices for rapid querying
CREATE INDEX IF NOT EXISTS idx_server_memory_guild ON beta_server_memory(guild_id, type);
CREATE INDEX IF NOT EXISTS idx_feedback_votes ON beta_feedback(votes DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_server ON beta_reports(server_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON beta_events(timestamp DESC);
