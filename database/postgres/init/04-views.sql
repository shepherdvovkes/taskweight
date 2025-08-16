-- TaskWeight Database Views
-- This script creates useful views for common queries

-- View for estimation results with user and task information
CREATE OR REPLACE VIEW estimation_results_detailed AS
SELECT 
    er.id,
    er.card_id,
    er.estimated_hours,
    er.status,
    er.priority,
    er.complexity,
    er.confidence_score,
    er.user_id,
    er.team_id,
    er.project_id,
    er.batch_id,
    er.metadata,
    er.reasoning,
    er.breakdown,
    er.created_at,
    er.updated_at,
    t.title as task_title,
    t.description as task_description,
    t.status as task_status,
    u.username as estimator_username,
    u.email as estimator_email,
    p.name as project_name,
    tc.name as category_name,
    tc.color as category_color
FROM estimation_results er
LEFT JOIN tasks t ON er.card_id = t.title
LEFT JOIN users u ON er.user_id = u.id
LEFT JOIN projects p ON er.project_id = p.id
LEFT JOIN task_categories tc ON t.category_id = tc.id;

-- View for task statistics
CREATE OR REPLACE VIEW task_statistics AS
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.estimated_hours,
    t.actual_hours,
    t.project_id,
    t.assignee_id,
    t.category_id,
    t.created_at,
    t.updated_at,
    p.name as project_name,
    u.username as assignee_username,
    tc.name as category_name,
    tc.color as category_color,
    er.status as estimation_status,
    er.confidence_score,
    er.priority as estimation_priority,
    er.complexity as estimation_complexity,
    COALESCE(te.total_minutes, 0) as tracked_minutes,
    COALESCE(te.total_minutes / 60.0, 0) as tracked_hours
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN task_categories tc ON t.category_id = tc.id
LEFT JOIN estimation_results er ON t.title = er.card_id
LEFT JOIN (
    SELECT task_id, SUM(duration_minutes) as total_minutes
    FROM time_entries
    GROUP BY task_id
) te ON t.id = te.task_id;

-- View for user performance metrics
CREATE OR REPLACE VIEW user_performance_metrics AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    COUNT(DISTINCT er.id) as total_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'completed' THEN er.id END) as completed_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'processing' THEN er.id END) as processing_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'failed' THEN er.id END) as failed_estimations,
    AVG(er.estimated_hours) as average_estimated_hours,
    AVG(ef.accuracy) as average_accuracy,
    AVG(ef.actual_hours) as average_actual_hours,
    COUNT(DISTINCT ef.id) as feedback_count,
    COUNT(DISTINCT CASE WHEN ef.accuracy >= 80 THEN ef.id END) as accurate_estimations,
    COUNT(DISTINCT CASE WHEN ef.actual_hours > er.estimated_hours THEN ef.id END) as overestimated_count,
    COUNT(DISTINCT CASE WHEN ef.actual_hours < er.estimated_hours THEN ef.id END) as underestimated_count
FROM users u
LEFT JOIN estimation_results er ON u.id = er.user_id
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
GROUP BY u.id, u.username, u.email, u.created_at;

-- View for project performance overview
CREATE OR REPLACE VIEW project_performance_overview AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.owner_id,
    p.created_at,
    p.updated_at,
    u.username as owner_username,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'in_progress' THEN t.id END) as in_progress_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'pending' THEN t.id END) as pending_tasks,
    COUNT(DISTINCT er.id) as total_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'completed' THEN er.id END) as completed_estimations,
    SUM(er.estimated_hours) as total_estimated_hours,
    SUM(COALESCE(ef.actual_hours, 0)) as total_actual_hours,
    AVG(ef.accuracy) as average_accuracy,
    AVG(er.confidence_score) as average_confidence,
    COUNT(DISTINCT tc.id) as total_categories
FROM projects p
LEFT JOIN users u ON p.owner_id = u.id
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN estimation_results er ON t.title = er.card_id
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
LEFT JOIN task_categories tc ON p.id = tc.project_id
GROUP BY p.id, p.name, p.description, p.owner_id, p.created_at, p.updated_at, u.username;

-- View for team performance summary
CREATE OR REPLACE VIEW team_performance_summary AS
SELECT 
    er.team_id,
    COUNT(DISTINCT er.user_id) as team_members,
    COUNT(DISTINCT er.id) as total_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'completed' THEN er.id END) as completed_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'processing' THEN er.id END) as processing_estimations,
    COUNT(DISTINCT CASE WHEN er.status = 'failed' THEN er.id END) as failed_estimations,
    AVG(er.estimated_hours) as average_estimated_hours,
    AVG(ef.accuracy) as average_accuracy,
    AVG(er.confidence_score) as average_confidence,
    SUM(er.estimated_hours) as total_estimated_hours,
    SUM(COALESCE(ef.actual_hours, 0)) as total_actual_hours,
    CASE 
        WHEN SUM(er.estimated_hours) > 0 
        THEN (SUM(COALESCE(ef.actual_hours, 0)) / SUM(er.estimated_hours))::DECIMAL(5,2)
        ELSE 0 
    END as efficiency_ratio,
    MAX(er.created_at) as last_activity
FROM estimation_results er
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
WHERE er.team_id IS NOT NULL
GROUP BY er.team_id;

-- View for estimation accuracy trends
CREATE OR REPLACE VIEW estimation_accuracy_trends AS
SELECT 
    DATE_TRUNC('week', er.created_at)::DATE as week_start,
    COUNT(*) as total_estimations,
    COUNT(CASE WHEN ef.accuracy >= 80 THEN 1 END) as accurate_estimations,
    COUNT(CASE WHEN ef.accuracy >= 60 AND ef.accuracy < 80 THEN 1 END) as good_estimations,
    COUNT(CASE WHEN ef.accuracy >= 40 AND ef.accuracy < 60 THEN 1 END) as fair_estimations,
    COUNT(CASE WHEN ef.accuracy < 40 THEN 1 END) as poor_estimations,
    AVG(ef.accuracy) as average_accuracy,
    AVG(er.confidence_score) as average_confidence,
    AVG(er.estimated_hours) as average_estimated_hours,
    AVG(ef.actual_hours) as average_actual_hours
FROM estimation_results er
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
WHERE ef.actual_hours IS NOT NULL
GROUP BY DATE_TRUNC('week', er.created_at)
ORDER BY week_start;

-- View for time tracking summary
CREATE OR REPLACE VIEW time_tracking_summary AS
SELECT 
    te.user_id,
    u.username,
    DATE(te.start_time) as date,
    COUNT(DISTINCT te.task_id) as tasks_worked_on,
    SUM(te.duration_minutes) as total_minutes,
    SUM(te.duration_minutes) / 60.0 as total_hours,
    SUM(CASE WHEN te.is_billable THEN te.duration_minutes ELSE 0 END) as billable_minutes,
    SUM(CASE WHEN te.is_billable THEN te.duration_minutes ELSE 0 END) / 60.0 as billable_hours,
    AVG(te.duration_minutes) as average_session_minutes
FROM time_entries te
JOIN users u ON te.user_id = u.id
GROUP BY te.user_id, u.username, DATE(te.start_time)
ORDER BY te.user_id, date;

-- View for notification summary
CREATE OR REPLACE VIEW notification_summary AS
SELECT 
    n.user_id,
    u.username,
    n.type,
    n.priority,
    n.status,
    COUNT(*) as count,
    MAX(n.created_at) as latest_notification,
    COUNT(CASE WHEN n.read_at IS NULL THEN 1 END) as unread_count
FROM notifications n
JOIN users u ON n.user_id = u.id
GROUP BY n.user_id, u.username, n.type, n.priority, n.status;

-- View for webhook delivery status
CREATE OR REPLACE VIEW webhook_delivery_status AS
SELECT 
    w.id as webhook_id,
    w.name as webhook_name,
    w.url,
    w.is_active,
    wd.event_type,
    wd.response_status,
    wd.attempt_count,
    wd.delivered_at,
    wd.error_message,
    wd.created_at as delivery_created,
    CASE 
        WHEN wd.response_status >= 200 AND wd.response_status < 300 THEN 'success'
        WHEN wd.response_status >= 400 THEN 'error'
        WHEN wd.response_status IS NULL THEN 'pending'
        ELSE 'unknown'
    END as delivery_status
FROM webhooks w
LEFT JOIN webhook_deliveries wd ON w.id = wd.webhook_id
WHERE w.is_active = true;

-- View for task dependencies overview
CREATE OR REPLACE VIEW task_dependencies_overview AS
SELECT 
    td.id as dependency_id,
    td.dependency_type,
    dependent.id as dependent_task_id,
    dependent.title as dependent_task_title,
    dependent.status as dependent_task_status,
    prerequisite.id as prerequisite_task_id,
    prerequisite.title as prerequisite_task_title,
    prerequisite.status as prerequisite_task_status,
    p.name as project_name,
    td.created_at
FROM task_dependencies td
JOIN tasks dependent ON td.dependent_task_id = dependent.id
JOIN tasks prerequisite ON td.prerequisite_task_id = prerequisite.id
JOIN projects p ON dependent.project_id = p.id
ORDER BY dependent.id, td.created_at;

-- View for batch processing status
CREATE OR REPLACE VIEW batch_processing_status AS
SELECT 
    be.batch_id,
    be.total_tasks,
    be.processing_tasks,
    be.completed_tasks,
    be.failed_tasks,
    be.status,
    be.user_id,
    u.username,
    be.team_id,
    be.project_id,
    be.created_at,
    be.estimated_completion_time,
    CASE 
        WHEN be.total_tasks > 0 
        THEN ((be.completed_tasks + be.failed_tasks)::DECIMAL / be.total_tasks * 100)::DECIMAL(5,2)
        ELSE 0 
    END as progress_percentage,
    CASE 
        WHEN be.status = 'completed' THEN 'Completed'
        WHEN be.status = 'failed' THEN 'Failed'
        WHEN be.status = 'processing' AND be.processing_tasks > 0 THEN 'In Progress'
        WHEN be.status = 'processing' AND be.processing_tasks = 0 THEN 'Queued'
        ELSE 'Unknown'
    END as status_description
FROM batch_estimations be
LEFT JOIN users u ON be.user_id = u.id;

-- View for system metrics overview
CREATE OR REPLACE VIEW system_metrics_overview AS
SELECT 
    metric_name,
    metric_unit,
    source,
    AVG(metric_value) as average_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as data_points,
    MAX(timestamp) as latest_measurement,
    MIN(timestamp) as first_measurement
FROM metrics
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY metric_name, metric_unit, source
ORDER BY metric_name, source;

-- View for task details
CREATE OR REPLACE VIEW task_details AS
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.estimated_hours,
    t.actual_hours,
    t.due_date,
    t.project_id,
    t.assignee_id,
    t.category_id,
    t.created_at,
    t.updated_at,
    p.name as project_name,
    u.username as assignee_username,
    u.email as assignee_email,
    tc.name as category_name,
    tc.color as category_color,
    er.status as estimation_status,
    er.confidence_score,
    er.complexity,
    er.reasoning,
    COALESCE(te.total_minutes, 0) as tracked_minutes,
    COALESCE(te.total_minutes / 60.0, 0) as tracked_hours
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN task_categories tc ON t.category_id = tc.id
LEFT JOIN estimation_results er ON t.title = er.card_id
LEFT JOIN (
    SELECT task_id, SUM(duration_minutes) as total_minutes
    FROM time_entries
    GROUP BY task_id
) te ON t.id = te.task_id;

-- View for project stats
CREATE OR REPLACE VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.status,
    p.created_at,
    p.updated_at,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'pending' THEN 1 END) as pending_tasks,
    COUNT(CASE WHEN t.status = 'blocked' THEN 1 END) as blocked_tasks,
    COALESCE(SUM(t.estimated_hours), 0) as total_estimated_hours,
    COALESCE(SUM(t.actual_hours), 0) as total_actual_hours,
    AVG(er.confidence_score) as average_confidence,
    AVG(ef.accuracy) as average_accuracy,
    MIN(t.created_at) as first_task_date,
    MAX(t.updated_at) as last_task_update,
    CASE 
        WHEN COUNT(t.id) > 0 
        THEN (COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::DECIMAL / COUNT(t.id) * 100)::DECIMAL(5,2)
        ELSE 0 
    END as completion_percentage
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN estimation_results er ON t.title = er.card_id
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
GROUP BY p.id, p.name, p.description, p.status, p.created_at, p.updated_at;

-- View for user workload
CREATE OR REPLACE VIEW user_workload AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    u.updated_at,
    COUNT(DISTINCT t.id) as total_assigned_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'in_progress' THEN t.id END) as in_progress_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'pending' THEN t.id END) as pending_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'blocked' THEN t.id END) as blocked_tasks,
    COALESCE(SUM(t.estimated_hours), 0) as total_estimated_hours,
    COALESCE(SUM(t.actual_hours), 0) as total_actual_hours,
    COALESCE(SUM(te.duration_minutes) / 60.0, 0) as total_tracked_hours,
    AVG(er.confidence_score) as average_confidence,
    AVG(ef.accuracy) as average_accuracy,
    COUNT(DISTINCT er.id) as total_estimations,
    MAX(t.updated_at) as last_task_update,
    MAX(te.start_time) as last_time_entry
FROM users u
LEFT JOIN tasks t ON u.id = t.assignee_id
LEFT JOIN estimation_results er ON u.id = er.user_id
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
LEFT JOIN time_entries te ON u.id = te.user_id
GROUP BY u.id, u.username, u.email, u.created_at, u.updated_at;

-- View for estimation analytics
CREATE OR REPLACE VIEW estimation_analytics AS
SELECT 
    DATE_TRUNC('day', er.created_at)::DATE as estimation_date,
    er.user_id,
    u.username,
    er.team_id,
    er.project_id,
    p.name as project_name,
    COUNT(er.id) as total_estimations,
    COUNT(CASE WHEN er.status = 'completed' THEN 1 END) as completed_estimations,
    COUNT(CASE WHEN er.status = 'processing' THEN 1 END) as processing_estimations,
    COUNT(CASE WHEN er.status = 'failed' THEN 1 END) as failed_estimations,
    AVG(er.estimated_hours) as average_estimated_hours,
    AVG(er.confidence_score) as average_confidence,
    AVG(er.complexity) as average_complexity,
    AVG(ef.accuracy) as average_accuracy,
    AVG(ef.actual_hours) as average_actual_hours,
    COUNT(CASE WHEN ef.accuracy >= 80 THEN 1 END) as accurate_estimations,
    COUNT(CASE WHEN ef.actual_hours > er.estimated_hours THEN 1 END) as overestimated_count,
    COUNT(CASE WHEN ef.actual_hours < er.estimated_hours THEN 1 END) as underestimated_count,
    SUM(er.estimated_hours) as total_estimated_hours,
    SUM(COALESCE(ef.actual_hours, 0)) as total_actual_hours
FROM estimation_results er
LEFT JOIN users u ON er.user_id = u.id
LEFT JOIN projects p ON er.project_id = p.id
LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
GROUP BY 
    DATE_TRUNC('day', er.created_at)::DATE,
    er.user_id,
    u.username,
    er.team_id,
    er.project_id,
    p.name
ORDER BY estimation_date DESC, u.username;

-- Grant permissions on views
GRANT SELECT ON ALL TABLES IN SCHEMA public TO taskweight_user;
