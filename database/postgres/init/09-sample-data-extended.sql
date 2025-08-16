-- TaskWeight Extended Sample Data
-- This script adds comprehensive sample data for testing

-- Insert additional users
INSERT INTO users (id, username, email, password_hash, role, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'alice_dev', 'alice@example.com', 'hash_alice', 'developer', CURRENT_TIMESTAMP),
('550e8400-e29b-41d4-a716-446655440002', 'bob_qa', 'bob@example.com', 'hash_bob', 'qa', CURRENT_TIMESTAMP),
('550e8400-e29b-41d4-a716-446655440003', 'charlie_pm', 'charlie@example.com', 'hash_charlie', 'project_manager', CURRENT_TIMESTAMP),
('550e8400-e29b-41d4-a716-446655440004', 'diana_designer', 'diana@example.com', 'hash_diana', 'designer', CURRENT_TIMESTAMP),
('550e8400-e29b-41d4-a716-446655440005', 'eve_architect', 'eve@example.com', 'hash_eve', 'architect', CURRENT_TIMESTAMP);

-- Insert additional projects
INSERT INTO projects (id, name, description, owner_id, created_at) VALUES
('660e8400-e29b-41d4-a716-446655440001', 'Mobile App Redesign', 'Redesign of mobile application UI/UX', '550e8400-e29b-41d4-a716-446655440004', CURRENT_TIMESTAMP),
('660e8400-e29b-41d4-a716-446655440002', 'API Gateway', 'Microservices API gateway implementation', '550e8400-e29b-41d4-a716-446655440005', CURRENT_TIMESTAMP),
('660e8400-e29b-41d4-a716-446655440003', 'Data Migration', 'Legacy system data migration', '550e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP);

-- Insert task categories
INSERT INTO task_categories (id, name, description, color, project_id, created_at) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'Frontend', 'Frontend development tasks', '#007bff', '660e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP),
('770e8400-e29b-41d4-a716-446655440002', 'Backend', 'Backend development tasks', '#28a745', '660e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP),
('770e8400-e29b-41d4-a716-446655440003', 'Testing', 'QA and testing tasks', '#ffc107', '660e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP),
('770e8400-e29b-41d4-a716-446655440004', 'Infrastructure', 'DevOps and infrastructure tasks', '#6f42c1', '660e8400-e29b-41d4-a716-446655440002', CURRENT_TIMESTAMP),
('770e8400-e29b-41d4-a716-446655440005', 'Documentation', 'Documentation and specs', '#17a2b8', '660e8400-e29b-41d4-a716-446655440003', CURRENT_TIMESTAMP);

-- Insert additional tasks
INSERT INTO tasks (id, title, description, status, priority, estimated_hours, actual_hours, project_id, assignee_id, category_id, created_at) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'Design Login Screen', 'Create modern login screen design', 'in_progress', 'high', 8.0, 6.5, '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440004', '770e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP),
('880e8400-e29b-41d4-a716-446655440002', 'Implement Authentication', 'Backend authentication system', 'pending', 'high', 16.0, NULL, '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', CURRENT_TIMESTAMP),
('880e8400-e29b-41d4-a716-446655440003', 'API Testing', 'Comprehensive API testing', 'pending', 'medium', 12.0, NULL, '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', CURRENT_TIMESTAMP),
('880e8400-e29b-41d4-a716-446655440004', 'Load Balancer Setup', 'Configure load balancer', 'completed', 'medium', 6.0, 5.5, '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440005', '770e8400-e29b-41d4-a716-446655440004', CURRENT_TIMESTAMP),
('880e8400-e29b-41d4-a716-446655440005', 'Data Schema Design', 'Design new data schema', 'in_progress', 'high', 20.0, 15.0, '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440005', CURRENT_TIMESTAMP);

-- Insert estimation results
INSERT INTO estimation_results (id, card_id, estimated_hours, status, priority, complexity, confidence_score, user_id, team_id, project_id, batch_id, metadata, reasoning, breakdown, created_at) VALUES
('990e8400-e29b-41d4-a716-446655440001', 'Design Login Screen', 8.0, 'estimated', 'high', 'medium', 85.5, '550e8400-e29b-41d4-a716-446655440004', 'team_design', '660e8400-e29b-41d4-a716-446655440001', 'batch_001', '{"design_tools": ["figma", "sketch"]}', 'Based on similar UI components', '{"research": 2, "design": 4, "review": 2}'),
('990e8400-e29b-41d4-a716-446655440002', 'Implement Authentication', 16.0, 'estimated', 'high', 'complex', 72.3, '550e8400-e29b-41d4-a716-446655440001', 'team_backend', '660e8400-e29b-41d4-a716-446655440001', 'batch_001', '{"framework": "django", "security": "oauth2"}', 'Complex authentication with OAuth2', '{"setup": 4, "implementation": 8, "testing": 4}'),
('990e8400-e29b-41d4-a716-446655440003', 'API Testing', 12.0, 'estimated', 'medium', 'medium', 78.9, '550e8400-e29b-41d4-a716-446655440002', 'team_qa', '660e8400-e29b-41d4-a716-446655440001', 'batch_001', '{"testing_tools": ["postman", "jest"]}', 'Standard API testing process', '{"planning": 2, "execution": 8, "reporting": 2}'),
('990e8400-e29b-41d4-a716-446655440004', 'Load Balancer Setup', 6.0, 'completed', 'medium', 'simple', 92.1, '550e8400-e29b-41d4-a716-446655440005', 'team_devops', '660e8400-e29b-41d4-a716-446655440002', 'batch_002', '{"infrastructure": "aws", "tool": "nginx"}', 'Standard load balancer setup', '{"configuration": 3, "testing": 2, "deployment": 1}'),
('990e8400-e29b-41d4-a716-446655440005', 'Data Schema Design', 20.0, 'estimated', 'high', 'very_complex', 65.7, '550e8400-e29b-41d4-a716-446655440001', 'team_data', '660e8400-e29b-41d4-a716-446655440003', 'batch_003', '{"database": "postgresql", "migration": "legacy"}', 'Complex legacy data migration', '{"analysis": 6, "design": 8, "validation": 6}');

-- Insert estimation feedback
INSERT INTO estimation_feedback (id, estimation_id, feedback, actual_hours, accuracy, difficulty, blockers, notes, created_at) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', 'Design was more complex than expected', 6.5, 81.25, 3, '["client_feedback_delays"]', 'Client requested multiple revisions', CURRENT_TIMESTAMP),
('aa0e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440004', 'Setup went smoothly', 5.5, 91.67, 2, '[]', 'No blockers encountered', CURRENT_TIMESTAMP);

-- Insert batch estimations
INSERT INTO batch_estimations (id, batch_id, total_tasks, processing_tasks, completed_tasks, failed_tasks, status, user_id, team_id, project_id, created_at, estimated_completion_time) VALUES
('bb0e8400-e29b-41d4-a716-446655440001', 'batch_001', 3, 0, 3, 0, 'completed', '550e8400-e29b-41d4-a716-446655440003', 'team_mobile', '660e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '2 hours'),
('bb0e8400-e29b-41d4-a716-446655440002', 'batch_002', 1, 0, 1, 0, 'completed', '550e8400-e29b-41d4-a716-446655440005', 'team_devops', '660e8400-e29b-41d4-a716-446655440002', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 hour'),
('bb0e8400-e29b-41d4-a716-446655440003', 'batch_003', 1, 1, 0, 0, 'processing', '550e8400-e29b-41d4-a716-446655440001', 'team_data', '660e8400-e29b-41d4-a716-446655440003', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '4 hours');

-- Insert time entries
INSERT INTO time_entries (id, task_id, user_id, start_time, end_time, duration_minutes, description, is_billable, created_at) VALUES
('cc0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440004', CURRENT_TIMESTAMP - INTERVAL '6 hours', CURRENT_TIMESTAMP - INTERVAL '4 hours', 120, 'Initial design research', true, CURRENT_TIMESTAMP),
('cc0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440004', CURRENT_TIMESTAMP - INTERVAL '3 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour', 120, 'Design implementation', true, CURRENT_TIMESTAMP),
('cc0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440005', CURRENT_TIMESTAMP - INTERVAL '5 hours', CURRENT_TIMESTAMP - INTERVAL '3 hours', 120, 'Load balancer configuration', true, CURRENT_TIMESTAMP),
('cc0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP - INTERVAL '8 hours', CURRENT_TIMESTAMP - INTERVAL '5 hours', 180, 'Data schema analysis', true, CURRENT_TIMESTAMP);

-- Insert task dependencies
INSERT INTO task_dependencies (id, dependent_task_id, prerequisite_task_id, dependency_type, created_at) VALUES
('dd0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', 'finish_to_start', CURRENT_TIMESTAMP),
('dd0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440002', 'finish_to_start', CURRENT_TIMESTAMP);

-- Insert notification templates
INSERT INTO notification_templates (id, name, type, subject, body_template, variables, is_active, created_at) VALUES
('ee0e8400-e29b-41d4-a716-446655440001', 'Task Assignment', 'task_assigned', 'New Task Assigned: {{task_title}}', 'You have been assigned a new task: {{task_title}}\n\nProject: {{project_name}}\nPriority: {{priority}}\nEstimated Hours: {{estimated_hours}}\n\nPlease review and start working on it.', '{"task_title": "string", "project_name": "string", "priority": "string", "estimated_hours": "number"}', true, CURRENT_TIMESTAMP),
('ee0e8400-e29b-41d4-a716-446655440002', 'Estimation Complete', 'estimation_complete', 'Estimation Complete for: {{task_title}}', 'The estimation for task "{{task_title}}" has been completed.\n\nEstimated Hours: {{estimated_hours}}\nConfidence Score: {{confidence_score}}%\n\nPlease review the estimation.', '{"task_title": "string", "estimated_hours": "number", "confidence_score": "number"}', true, CURRENT_TIMESTAMP),
('ee0e8400-e29b-41d4-a716-446655440003', 'Batch Complete', 'batch_complete', 'Batch Processing Complete: {{batch_id}}', 'Batch {{batch_id}} has been completed successfully.\n\nTotal Tasks: {{total_tasks}}\nCompleted: {{completed_tasks}}\nFailed: {{failed_tasks}}\n\nAll estimations are ready for review.', '{"batch_id": "string", "total_tasks": "number", "completed_tasks": "number", "failed_tasks": "number"}', true, CURRENT_TIMESTAMP);

-- Insert notifications
INSERT INTO notifications (id, user_id, template_id, type, title, message, data, priority, status, created_at) VALUES
('ff0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'ee0e8400-e29b-41d4-a716-446655440001', 'task_assigned', 'New Task: Implement Authentication', 'You have been assigned a new task: Implement Authentication\n\nProject: Mobile App Redesign\nPriority: high\nEstimated Hours: 16.0\n\nPlease review and start working on it.', '{"task_title": "Implement Authentication", "project_name": "Mobile App Redesign", "priority": "high", "estimated_hours": 16.0}', 'high', 'pending', CURRENT_TIMESTAMP),
('ff0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'ee0e8400-e29b-41d4-a716-446655440002', 'estimation_complete', 'Estimation Complete: API Testing', 'The estimation for task "API Testing" has been completed.\n\nEstimated Hours: 12.0\nConfidence Score: 78.9%\n\nPlease review the estimation.', '{"task_title": "API Testing", "estimated_hours": 12.0, "confidence_score": 78.9}', 'normal', 'pending', CURRENT_TIMESTAMP);

-- Insert notification preferences
INSERT INTO notification_preferences (id, user_id, email_enabled, push_enabled, in_app_enabled, webhook_enabled, quiet_hours_start, quiet_hours_end, timezone, categories, created_at) VALUES
('110e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', true, false, true, false, '22:00:00', '08:00:00', 'UTC', '{"task_assigned": true, "estimation_complete": true}', CURRENT_TIMESTAMP),
('110e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', true, true, true, false, '23:00:00', '07:00:00', 'UTC', '{"task_assigned": true, "estimation_complete": true}', CURRENT_TIMESTAMP),
('110e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', true, false, true, true, '21:00:00', '09:00:00', 'UTC', '{"batch_complete": true, "project_updates": true}', CURRENT_TIMESTAMP);

-- Insert metrics
INSERT INTO metrics (id, metric_name, metric_value, metric_unit, tags, timestamp, source) VALUES
('120e8400-e29b-41d4-a716-446655440001', 'estimation_accuracy', 85.5, 'percentage', '{"team": "team_design", "project": "mobile_app"}', CURRENT_TIMESTAMP, 'estimation_system'),
('120e8400-e29b-41d4-a716-446655440002', 'estimation_accuracy', 72.3, 'percentage', '{"team": "team_backend", "project": "mobile_app"}', CURRENT_TIMESTAMP, 'estimation_system'),
('120e8400-e29b-41d4-a716-446655440003', 'estimation_accuracy', 78.9, 'percentage', '{"team": "team_qa", "project": "mobile_app"}', CURRENT_TIMESTAMP, 'estimation_system'),
('120e8400-e29b-41d4-a716-446655440004', 'estimation_accuracy', 92.1, 'percentage', '{"team": "team_devops", "project": "api_gateway"}', CURRENT_TIMESTAMP, 'estimation_system'),
('120e8400-e29b-41d4-a716-446655440005', 'estimation_accuracy', 65.7, 'percentage', '{"team": "team_data", "project": "data_migration"}', CURRENT_TIMESTAMP, 'estimation_system'),
('120e8400-e29b-41d4-a716-446655440006', 'average_estimation_time', 45.2, 'minutes', '{"period": "daily"}', CURRENT_TIMESTAMP, 'performance_monitor'),
('120e8400-e29b-41d4-a716-446655440007', 'total_estimations', 15, 'count', '{"period": "daily"}', CURRENT_TIMESTAMP, 'performance_monitor'),
('120e8400-e29b-41d4-a716-446655440008', 'active_users', 8, 'count', '{"period": "daily"}', CURRENT_TIMESTAMP, 'user_activity');

-- Insert user activity logs
INSERT INTO user_activity_logs (id, user_id, activity_type, activity_data, ip_address, user_agent, session_id, created_at) VALUES
('130e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'login', '{"ip": "192.168.1.100", "browser": "chrome"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'session_001', CURRENT_TIMESTAMP),
('130e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'task_view', '{"task_id": "880e8400-e29b-41d4-a716-446655440002", "project_id": "660e8400-e29b-41d4-a716-446655440001"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'session_001', CURRENT_TIMESTAMP),
('130e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'login', '{"ip": "192.168.1.101", "browser": "firefox"}', '192.168.1.101', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0', 'session_002', CURRENT_TIMESTAMP),
('130e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440003', 'estimation_create', '{"estimation_id": "990e8400-e29b-41d4-a716-446655440001", "task_id": "880e8400-e29b-41d4-a716-446655440001"}', '192.168.1.102', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'session_003', CURRENT_TIMESTAMP);

-- Insert performance metrics
INSERT INTO performance_metrics (id, task_id, metric_type, metric_value, baseline_value, improvement_percentage, measured_at, notes) VALUES
('140e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'design_iterations', 3, 2, -50.0, CURRENT_TIMESTAMP, 'More iterations than expected due to client feedback'),
('140e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440004', 'deployment_time', 15.5, 20.0, 22.5, CURRENT_TIMESTAMP, 'Faster deployment due to improved automation'),
('140e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440005', 'code_complexity', 8.5, 6.0, -41.7, CURRENT_TIMESTAMP, 'Higher complexity due to legacy system constraints');

-- Insert estimation accuracy history
INSERT INTO estimation_accuracy_history (id, user_id, period_start, period_end, total_estimations, accurate_estimations, overestimated_count, underestimated_count, average_accuracy_percentage, improvement_trend, created_at) VALUES
('150e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, 25, 18, 4, 3, 72.0, 5.2, CURRENT_TIMESTAMP),
('150e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, 18, 15, 2, 1, 83.3, 2.1, CURRENT_TIMESTAMP),
('150e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440004', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, 12, 11, 1, 0, 91.7, 1.8, CURRENT_TIMESTAMP);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskweight_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taskweight_user;


