-- TaskWeight Sample Data
-- This file contains sample data for development and testing

-- Insert sample users
INSERT INTO users (id, username, email, password_hash) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'admin', 'admin@taskweight.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8m'),
    ('550e8400-e29b-41d4-a716-446655440002', 'developer', 'dev@taskweight.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8m'),
    ('550e8400-e29b-41d4-a716-446655440003', 'manager', 'manager@taskweight.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8m')
ON CONFLICT (username) DO NOTHING;

-- Insert sample projects
INSERT INTO projects (id, name, description, owner_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440010', 'TaskWeight Platform', 'Main platform for task estimation', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440011', 'Mobile App', 'iOS and Android mobile application', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440012', 'API Development', 'REST API for external integrations', '550e8400-e29b-41d4-a716-446655440003')
ON CONFLICT DO NOTHING;

-- Insert sample tasks
INSERT INTO tasks (id, title, description, project_id, assignee_id, status, priority, estimated_hours) VALUES
    ('550e8400-e29b-41d4-a716-446655440020', 'Setup Database', 'Initialize PostgreSQL database with proper schema', '550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440001', 'completed', 'high', 4.0),
    ('550e8400-e29b-41d4-a716-446655440021', 'User Authentication', 'Implement JWT-based authentication system', '550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440002', 'in_progress', 'high', 8.0),
    ('550e8400-e29b-41d4-a716-446655440022', 'Trello Integration', 'Connect with Trello API for task sync', '550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440002', 'todo', 'medium', 6.0)
ON CONFLICT DO NOTHING;

-- Insert sample estimation results
INSERT INTO estimation_results (id, card_id, task_description, repo_url, estimated_hours, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440030', 'trello_card_001', 'Implement user authentication system', 'https://github.com/taskweight/auth-service', 8.0, 'estimated'),
    ('550e8400-e29b-41d4-a716-446655440031', 'trello_card_002', 'Setup database schema and migrations', 'https://github.com/taskweight/database', 4.0, 'completed'),
    ('550e8400-e29b-41d4-a716-446655440032', 'trello_card_003', 'Create REST API endpoints', 'https://github.com/taskweight/api', 12.0, 'processing')
ON CONFLICT DO NOTHING;
