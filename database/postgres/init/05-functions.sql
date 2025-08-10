-- TaskWeight Database Functions
-- This file contains useful functions for database operations

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_stats(user_uuid UUID)
RETURNS TABLE(
    total_projects BIGINT,
    total_tasks BIGINT,
    completed_tasks BIGINT,
    total_estimated_hours DECIMAL,
    total_actual_hours DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT p.id)::BIGINT as total_projects,
        COUNT(t.id)::BIGINT as total_tasks,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::BIGINT as completed_tasks,
        COALESCE(SUM(t.estimated_hours), 0) as total_estimated_hours,
        COALESCE(SUM(t.actual_hours), 0) as total_actual_hours
    FROM users u
    LEFT JOIN projects p ON u.id = p.owner_id
    LEFT JOIN tasks t ON p.id = t.project_id
    WHERE u.id = user_uuid
    GROUP BY u.id;
END;
$$ LANGUAGE plpgsql;

-- Function to search tasks by text
CREATE OR REPLACE FUNCTION search_tasks(search_term TEXT)
RETURNS TABLE(
    id UUID,
    title VARCHAR,
    description TEXT,
    status VARCHAR,
    priority VARCHAR,
    project_name VARCHAR,
    assignee_username VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.description,
        t.status,
        t.priority,
        p.name as project_name,
        u.username as assignee_username
    FROM tasks t
    LEFT JOIN projects p ON t.project_id = p.id
    LEFT JOIN users u ON t.assignee_id = u.id
    WHERE 
        t.title ILIKE '%' || search_term || '%' OR
        t.description ILIKE '%' || search_term || '%' OR
        p.name ILIKE '%' || search_term || '%'
    ORDER BY t.updated_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get project timeline
CREATE OR REPLACE FUNCTION get_project_timeline(project_uuid UUID)
RETURNS TABLE(
    task_id UUID,
    task_title VARCHAR,
    status VARCHAR,
    estimated_hours DECIMAL,
    actual_hours DECIMAL,
    assignee_username VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id as task_id,
        t.title as task_title,
        t.status,
        t.estimated_hours,
        t.actual_hours,
        u.username as assignee_username,
        t.created_at,
        t.updated_at
    FROM tasks t
    LEFT JOIN users u ON t.assignee_id = u.id
    WHERE t.project_id = project_uuid
    ORDER BY t.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate estimation accuracy
CREATE OR REPLACE FUNCTION get_estimation_accuracy()
RETURNS TABLE(
    total_estimations BIGINT,
    accurate_estimations BIGINT,
    overestimated BIGINT,
    underestimated BIGINT,
    accuracy_percentage DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH accuracy_stats AS (
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN ABS(estimated_hours - actual_hours) <= 1 THEN 1 END) as accurate,
            COUNT(CASE WHEN estimated_hours > actual_hours + 1 THEN 1 END) as overestimated,
            COUNT(CASE WHEN estimated_hours < actual_hours - 1 THEN 1 END) as underestimated
        FROM estimation_results
        WHERE status = 'completed' AND actual_hours IS NOT NULL
    )
    SELECT 
        total,
        accurate,
        overestimated,
        underestimated,
        ROUND((accurate::DECIMAL / total * 100), 2) as accuracy_percentage
    FROM accuracy_stats;
END;
$$ LANGUAGE plpgsql;
