-- TaskWeight Database Views
-- This file contains database views for convenient data access

-- View for task details with project and assignee information
CREATE OR REPLACE VIEW task_details AS
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.estimated_hours,
    t.actual_hours,
    t.created_at,
    t.updated_at,
    p.name as project_name,
    p.description as project_description,
    u.username as assignee_username,
    u.email as assignee_email
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN users u ON t.assignee_id = u.id;

-- View for project statistics
CREATE OR REPLACE VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    p.description,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'todo' THEN 1 END) as todo_tasks,
    SUM(t.estimated_hours) as total_estimated_hours,
    SUM(t.actual_hours) as total_actual_hours,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
GROUP BY p.id, p.name, p.description, p.created_at, p.updated_at;

-- View for user workload
CREATE OR REPLACE VIEW user_workload AS
SELECT 
    u.id,
    u.username,
    u.email,
    COUNT(t.id) as assigned_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as active_tasks,
    SUM(t.estimated_hours) as total_estimated_hours,
    SUM(t.actual_hours) as total_actual_hours,
    u.created_at
FROM users u
LEFT JOIN tasks t ON u.id = t.assignee_id
GROUP BY u.id, u.username, u.email, u.created_at;

-- View for estimation analytics
CREATE OR REPLACE VIEW estimation_analytics AS
SELECT 
    status,
    COUNT(*) as total_estimations,
    AVG(estimated_hours) as avg_estimated_hours,
    AVG(actual_hours) as avg_actual_hours,
    MIN(created_at) as first_estimation,
    MAX(created_at) as last_estimation
FROM estimation_results
GROUP BY status;
