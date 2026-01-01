-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema with 4 tables: projects, srs_versions, chat_history, memory_facts
-- Created: 2024-01-01

BEGIN;

-- ============================================
-- Table: projects
-- Purpose: Store basic project information
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Table: srs_versions
-- Purpose: Store SRS document versions (snapshots)
-- ============================================
CREATE TABLE IF NOT EXISTS srs_versions (
    version_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    srs_data JSONB NOT NULL,
    srs_markdown TEXT,
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    UNIQUE(project_id, version_number)
);

-- ============================================
-- Table: chat_history
-- Purpose: Store conversation history between user and agent
-- ============================================
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    tool_calls JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Table: memory_facts
-- Purpose: Store long-term memory facts and preferences
-- ============================================
CREATE TABLE IF NOT EXISTS memory_facts (
    fact_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    fact_key VARCHAR(255) NOT NULL,
    fact_value TEXT NOT NULL,
    fact_type VARCHAR(50) CHECK (fact_type IN ('preference', 'requirement', 'constraint')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, fact_key)
);

-- ============================================
-- Indexes for Performance Optimization
-- ============================================

-- Index for srs_versions: Query latest version by project
CREATE INDEX IF NOT EXISTS idx_srs_versions_project_created 
ON srs_versions(project_id, created_at DESC);

-- Index for chat_history: Query by session
CREATE INDEX IF NOT EXISTS idx_chat_history_session 
ON chat_history(project_id, session_id, timestamp);

-- Index for memory_facts: Query facts by project
CREATE INDEX IF NOT EXISTS idx_memory_facts_project 
ON memory_facts(project_id, fact_key);

-- Index for JSONB queries on srs_data (PostgreSQL GIN index)
CREATE INDEX IF NOT EXISTS idx_srs_data_gin 
ON srs_versions USING GIN (srs_data);

-- Index for full-text search on srs_markdown (optional)
CREATE INDEX IF NOT EXISTS idx_srs_markdown_fts 
ON srs_versions USING GIN (to_tsvector('english', COALESCE(srs_markdown, '')));

-- ============================================
-- Triggers for updated_at timestamps
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for projects table
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for memory_facts table
CREATE TRIGGER update_memory_facts_updated_at
    BEFORE UPDATE ON memory_facts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

