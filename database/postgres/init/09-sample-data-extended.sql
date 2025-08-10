-- TaskWeight Extended Sample Data
-- This file contains additional sample data for new tables

-- Insert sample task categories
INSERT INTO task_categories (id, name, description, color, project_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440040', 'Frontend', 'Frontend development tasks', '#28a745', '550e8400-e29b-41d4-a716-446655440010'),
    ('550e8400-e29b-41d4-a716-446655440041', 'Backend', 'Backend development tasks', '#007bff', '550e8400-e29b-41d4-a716-446655440010'),
    ('550e8400-e29b-41d4-a716-446655440042', 'Database', 'Database related tasks', '#ffc107', '550e8400-e29b-41d4-a716-446655440010'),
    ('550e8400-e29b-41d4-a716-446655440043', 'Testing', 'Testing and QA tasks', '#dc3545', '550e8400-e29b-41d4-a716-446655440011'),
    ('550e8400-e29b-41d4-a716-446655440044', 'Documentation', 'Documentation tasks', '#6c757d', '550e8400-e29b-41d4-a716-446655440012')
ON CONFLICT DO NOTHING;

-- Update existing tasks with categories
UPDATE tasks SET category_id = '550e8400-e29b-41d4-a716-446655440042' WHERE title = 'Setup Database';
UPDATE tasks SET category_id = '550e8400-e29b-41d4-a716-446655440041' WHERE title = 'User Authentication';
UPDATE tasks SET category_id = '550e8400-e29b-41d4-a716-446655440041' WHERE title = 'Trello Integration';

-- Insert sample webhooks
INSERT INTO webhooks (id, name, url, events, integration_id, secret_key) VALUES
    ('550e8400-e29b-41d4-a716-446655440050', 'Trello Card Updates', 'https://api.taskweight.com/webhooks/trello', ARRAY['card_created', 'card_updated', 'card_moved'], '550e8400-e29b-41d4-a716-446655440030', 'webhook_secret_123'),
    ('550e8400-e29b-41d4-a716-446655440051', 'Jira Issue Updates', 'https://api.taskweight.com/webhooks/jira', ARRAY['issue_created', 'issue_updated', 'issue_transitioned'], '550e8400-e29b-41d4-a716-446655440031', 'webhook_secret_456')
ON CONFLICT DO NOTHING;

-- Insert sample metrics
INSERT INTO metrics (metric_name, metric_value, metric_unit, tags, source) VALUES
    ('active_users', 15, 'users', '{"period": "daily"}', 'system'),
    ('estimation_requests', 47, 'requests', '{"period": "daily"}', 'api'),
    ('average_response_time', 245, 'ms', '{"endpoint": "estimation"}', 'api'),
    ('error_rate', 0.02, 'percentage', '{"service": "estimation"}', 'system'),
    ('uptime_percentage', 99.8, 'percentage', '{"service": "main"}', 'monitoring')
ON CONFLICT DO NOTHING;

-- Insert sample performance metrics
INSERT INTO performance_metrics (id, task_id, metric_type, metric_value, baseline_value, improvement_percentage) VALUES
    ('550e8400-e29b-41d4-a716-446655440060', '550e8400-e29b-41d4-a716-446655440020', 'estimation_accuracy', 95.5, 85.0, 12.4),
    ('550e8400-e29b-41d4-a716-446655440061', '550e8400-e29b-41d4-a716-446655440021', 'completion_time', 7.5, 8.0, 6.3),
    ('550e8400-e29b-41d4-a716-446655440062', '550e8400-e29b-41d4-a716-446655440022', 'quality_score', 88.0, 82.0, 7.3)
ON CONFLICT DO NOTHING;

-- Insert sample user activity logs
INSERT INTO user_activity_logs (id, user_id, activity_type, activity_data, ip_address, session_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440070', '550e8400-e29b-41d4-a716-446655440001', 'login', '{"method": "password", "success": true}', '192.168.1.100', 'session_001'),
    ('550e8400-e29b-41d4-a716-446655440071', '550e8400-e29b-41d4-a716-446655440002', 'estimation_request', '{"task_type": "development", "complexity": "medium"}', '192.168.1.101', 'session_002'),
    ('550e8400-e29b-41d4-a716-446655440072', '550e8400-e29b-41d4-a716-446655440003', 'integration_sync', '{"service": "trello", "cards_synced": 15}', '192.168.1.102', 'session_003')
ON CONFLICT DO NOTHING;

-- Insert sample estimation accuracy history
INSERT INTO estimation_accuracy_history (id, user_id, period_start, period_end, total_estimations, accurate_estimations, overestimated_count, underestimated_count, average_accuracy_percentage, improvement_trend) VALUES
    ('550e8400-e29b-41d4-a716-446655440080', '550e8400-e29b-41d4-a716-446655440001', '2024-01-01', '2024-01-31', 25, 20, 3, 2, 80.0, 5.2),
    ('550e8400-e29b-41d4-a716-446655440081', '550e8400-e29b-41d4-a716-446655440002', '2024-01-01', '2024-01-31', 30, 26, 2, 2, 86.7, 8.1),
    ('550e8400-e29b-41d4-a716-446655440082', '550e8400-e29b-41d4-a716-446655440003', '2024-01-01', '2024-01-31', 20, 17, 2, 1, 85.0, 3.5)
ON CONFLICT DO NOTHING;

-- Insert sample notification templates
INSERT INTO notification_templates (id, name, type, subject, body_template, variables) VALUES
    ('550e8400-e29b-41d4-a716-446655440090', 'task_assigned', 'email', 'New Task Assigned', 'You have been assigned a new task: {{0}}. Project: {{1}}. Estimated time: {{2}} hours.', '["task_title", "project_name", "estimated_hours"]'),
    ('550e8400-e29b-41d4-a716-446655440091', 'estimation_complete', 'in_app', 'Estimation Complete', 'Your estimation request for "{{0}}" has been completed. Result: {{1}} hours.', '["task_description", "estimated_hours"]'),
    ('550e8400-e29b-41d4-a716-446655440092', 'integration_sync', 'webhook', 'Integration Sync', 'Integration with {{0}} has been synchronized. {{1}} items processed.', '["service_name", "items_count"]')
ON CONFLICT DO NOTHING;

-- Insert sample notifications
INSERT INTO notifications (id, user_id, template_id, type, title, message, data, priority, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440090', 'email', 'New Task Assigned', 'You have been assigned a new task: User Authentication. Project: TaskWeight Platform. Estimated time: 8.0 hours.', '["User Authentication", "TaskWeight Platform", "8.0"]', 'normal', 'sent'),
    ('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440091', 'in_app', 'Estimation Complete', 'Your estimation request for "Implement user authentication system" has been completed. Result: 8.0 hours.', '["Implement user authentication system", "8.0"]', 'normal', 'delivered')
ON CONFLICT DO NOTHING;

-- Insert sample notification preferences
INSERT INTO notification_preferences (id, user_id, email_enabled, push_enabled, in_app_enabled, webhook_enabled, quiet_hours_start, quiet_hours_end, timezone, categories) VALUES
    ('550e8400-e29b-41d4-a716-446655440110', '550e8400-e29b-41d4-a716-446655440001', true, false, true, true, '22:00:00', '08:00:00', 'UTC', '{"task_updates": true, "system_alerts": true, "weekly_reports": false}'),
    ('550e8400-e29b-41d4-a716-446655440111', '550e8400-e29b-41d4-a716-446655440002', true, true, true, false, '23:00:00', '07:00:00', 'Europe/London', '{"task_updates": true, "estimation_results": true, "integration_sync": true}'),
    ('550e8400-e29b-41d4-a716-446655440112', '550e8400-e29b-41d4-a716-446655440003', false, false, true, true, '21:00:00', '09:00:00', 'America/New_York', '{"project_updates": true, "team_notifications": true}')
ON CONFLICT DO NOTHING;

-- Insert sample task dependencies
INSERT INTO task_dependencies (id, dependent_task_id, prerequisite_task_id, dependency_type) VALUES
    ('550e8400-e29b-41d4-a716-446655440120', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440020', 'requires'),
    ('550e8400-e29b-41d4-a716-446655440121', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440021', 'blocks')
ON CONFLICT DO NOTHING;

-- Insert sample time entries
INSERT INTO time_entries (id, task_id, user_id, start_time, end_time, duration_minutes, description, is_billable) VALUES
    ('550e8400-e29b-41d4-a716-446655440130', '550e8400-e29b-41d4-a716-446655440020', '550e8400-e29b-41d4-a716-446655440001', '2024-01-15 09:00:00+00', '2024-01-15 13:00:00+00', 240, 'Database setup and initial configuration', true),
    ('550e8400-e29b-41d4-a716-446655440131', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440002', '2024-01-16 10:00:00+00', '2024-01-16 18:00:00+00', 480, 'JWT implementation and user management', true),
    ('550e8400-e29b-41d4-a716-446655440132', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440002', '2024-01-17 09:00:00+00', '2024-01-17 17:00:00+00', 480, 'Testing and bug fixes', true)
ON CONFLICT DO NOTHING;

-- Update actual_hours in tasks based on time entries
UPDATE tasks SET actual_hours = 4.0 WHERE id = '550e8400-e29b-41d4-a716-446655440020';
UPDATE tasks SET actual_hours = 16.0 WHERE id = '550e8400-e29b-41d4-a716-446655440021';


