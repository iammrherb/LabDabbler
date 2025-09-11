-- LabDabbler Database Initialization Script
-- This script sets up the initial database structure and optimizations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS labdabbler;

-- Set search path
ALTER DATABASE labdabbler_production SET search_path TO labdabbler, public;

-- Create application tables
CREATE TABLE IF NOT EXISTS labdabbler.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labdabbler.labs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'stopped',
    created_by UUID REFERENCES labdabbler.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labdabbler.lab_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lab_id UUID REFERENCES labdabbler.labs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    logs TEXT,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS labdabbler.repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(500) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'git',
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labdabbler.containers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    image VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    vendor VARCHAR(100),
    version VARCHAR(100),
    architecture VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    last_discovered TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON labdabbler.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON labdabbler.users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON labdabbler.users(is_active);

CREATE INDEX IF NOT EXISTS idx_labs_name ON labdabbler.labs(name);
CREATE INDEX IF NOT EXISTS idx_labs_status ON labdabbler.labs(status);
CREATE INDEX IF NOT EXISTS idx_labs_created_by ON labdabbler.labs(created_by);
CREATE INDEX IF NOT EXISTS idx_labs_created_at ON labdabbler.labs(created_at);
CREATE INDEX IF NOT EXISTS idx_labs_config ON labdabbler.labs USING GIN(config);

CREATE INDEX IF NOT EXISTS idx_lab_executions_lab_id ON labdabbler.lab_executions(lab_id);
CREATE INDEX IF NOT EXISTS idx_lab_executions_status ON labdabbler.lab_executions(status);
CREATE INDEX IF NOT EXISTS idx_lab_executions_started_at ON labdabbler.lab_executions(started_at);

CREATE INDEX IF NOT EXISTS idx_repositories_name ON labdabbler.repositories(name);
CREATE INDEX IF NOT EXISTS idx_repositories_type ON labdabbler.repositories(type);
CREATE INDEX IF NOT EXISTS idx_repositories_sync_status ON labdabbler.repositories(sync_status);

CREATE INDEX IF NOT EXISTS idx_containers_name ON labdabbler.containers(name);
CREATE INDEX IF NOT EXISTS idx_containers_category ON labdabbler.containers(category);
CREATE INDEX IF NOT EXISTS idx_containers_vendor ON labdabbler.containers(vendor);
CREATE INDEX IF NOT EXISTS idx_containers_metadata ON labdabbler.containers USING GIN(metadata);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON labdabbler.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_labs_updated_at BEFORE UPDATE ON labdabbler.labs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON labdabbler.repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create default admin user (password should be changed immediately)
INSERT INTO labdabbler.users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@labdabbler.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBdXzogKI00ycW', true)
ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA labdabbler TO labdabbler_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA labdabbler TO labdabbler_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA labdabbler TO labdabbler_user;

-- Analyze tables for query planner
ANALYZE;