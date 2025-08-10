-- TaskWeight Database Migrations
-- This file contains database migrations for future updates

-- Migration 001: Add task categories
-- Date: 2024-01-01
-- Description: Add support for task categorization

CREATE TABLE IF NOT EXISTS task_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#007bff',
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add category_id to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES task_categories(id) ON DELETE SET NULL;

-- Create indexes for task_categories
CREATE INDEX IF NOT EXISTS idx_task_categories_project_id ON task_categories(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks(category_id);

-- Create trigger for task_categories
CREATE TRIGGER update_task_categories_updated_at BEFORE UPDATE ON task_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration 002: Add webhooks system
-- Date: 2024-01-15
-- Description: Add webhook management for external integrations

-- Note: This migration is now handled by 06-webhooks.sql

-- Migration 003: Add metrics and analytics system
-- Date: 2024-01-20
-- Description: Add comprehensive metrics collection and analytics

-- Note: This migration is now handled by 07-metrics.sql

-- Migration 004: Add notification system
-- Date: 2024-01-25
-- Description: Add comprehensive notification management

-- Note: This migration is now handled by 08-notifications.sql

-- Migration 005: Add task dependencies
-- Date: 2024-02-01
-- Description: Add support for task dependencies and blocking

CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dependent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    prerequisite_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'blocks', -- 'blocks', 'requires', 'suggests'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dependent_task_id, prerequisite_task_id)
);

-- Create indexes for task_dependencies
CREATE INDEX IF NOT EXISTS idx_task_dependencies_dependent ON task_dependencies(dependent_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_prerequisite ON task_dependencies(prerequisite_task_id);

-- Migration 006: Add time tracking
-- Date: 2024-02-05
-- Description: Add detailed time tracking for tasks

CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    description TEXT,
    is_billable BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for time_entries
CREATE INDEX IF NOT EXISTS idx_time_entries_task_id ON time_entries(task_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_user_id ON time_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_start_time ON time_entries(start_time);

-- Create trigger for time_entries
CREATE TRIGGER update_time_entries_updated_at BEFORE UPDATE ON time_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate task duration from time entries
CREATE OR REPLACE FUNCTION calculate_task_duration(p_task_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total_minutes INTEGER;
BEGIN
    SELECT COALESCE(SUM(duration_minutes), 0)
    INTO total_minutes
    FROM time_entries
    WHERE task_id = p_task_id;
    
    RETURN total_minutes;
END;
$$ LANGUAGE plpgsql;
