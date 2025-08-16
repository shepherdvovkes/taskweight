-- TaskWeight Database Migrations
-- This script adds missing tables and fields to match the complete schema

-- Add missing fields to estimation_results table
ALTER TABLE estimation_results 
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS complexity VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS project_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS batch_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS reasoning TEXT,
ADD COLUMN IF NOT EXISTS breakdown JSONB DEFAULT '{}';

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_estimation_results_user_id ON estimation_results(user_id);
CREATE INDEX IF NOT EXISTS idx_estimation_results_team_id ON estimation_results(team_id);
CREATE INDEX IF NOT EXISTS idx_estimation_results_project_id ON estimation_results(project_id);
CREATE INDEX IF NOT EXISTS idx_estimation_results_batch_id ON estimation_results(batch_id);
CREATE INDEX IF NOT EXISTS idx_estimation_results_priority ON estimation_results(priority);
CREATE INDEX IF NOT EXISTS idx_estimation_results_complexity ON estimation_results(complexity);

-- Create estimation_feedback table
CREATE TABLE IF NOT EXISTS estimation_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimation_id UUID REFERENCES estimation_results(id) ON DELETE CASCADE,
    feedback TEXT NOT NULL,
    actual_hours DECIMAL(5,2),
    accuracy INTEGER CHECK (accuracy >= 0 AND accuracy <= 100),
    difficulty INTEGER CHECK (difficulty >= 1 AND difficulty <= 5),
    blockers JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for estimation_feedback
CREATE INDEX IF NOT EXISTS idx_estimation_feedback_estimation_id ON estimation_feedback(estimation_id);
CREATE INDEX IF NOT EXISTS idx_estimation_feedback_created_at ON estimation_feedback(created_at);

-- Create batch_estimations table
CREATE TABLE IF NOT EXISTS batch_estimations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(255) UNIQUE NOT NULL,
    total_tasks INTEGER NOT NULL,
    processing_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'processing',
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    team_id VARCHAR(255),
    project_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estimated_completion_time TIMESTAMP WITH TIME ZONE
);

-- Create indexes for batch_estimations
CREATE INDEX IF NOT EXISTS idx_batch_estimations_batch_id ON batch_estimations(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_estimations_user_id ON batch_estimations(user_id);
CREATE INDEX IF NOT EXISTS idx_batch_estimations_status ON batch_estimations(status);

-- Create webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    events JSONB DEFAULT '[]',
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    secret_key VARCHAR(255),
    retry_count INTEGER DEFAULT 0,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for webhooks
CREATE INDEX IF NOT EXISTS idx_webhooks_integration_id ON webhooks(integration_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active);

-- Create trigger for webhooks
CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(255)
);

-- Create indexes for metrics
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_source ON metrics(source);

-- Create task_categories table
CREATE TABLE IF NOT EXISTS task_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#000000',
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for task_categories
CREATE INDEX IF NOT EXISTS idx_task_categories_project_id ON task_categories(project_id);

-- Create trigger for task_categories
CREATE TRIGGER update_task_categories_updated_at BEFORE UPDATE ON task_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add category_id to tasks table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES task_categories(id) ON DELETE SET NULL;

-- Create index for category_id
CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks(category_id);

-- Create webhook_deliveries table
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    error_message TEXT,
    attempt_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for webhook_deliveries
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(response_status);

-- Create performance_metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id VARCHAR(255) NOT NULL, -- String identifier for the card/task
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    baseline_value DECIMAL(10,4),
    improvement_percentage DECIMAL(5,2),
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create indexes for performance_metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_card_id ON performance_metrics(card_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);

-- Create user_activity_logs table
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(100) NOT NULL,
    activity_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user_activity_logs
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- Create estimation_accuracy_history table
CREATE TABLE IF NOT EXISTS estimation_accuracy_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_estimations INTEGER DEFAULT 0,
    accurate_estimations INTEGER DEFAULT 0,
    overestimated_count INTEGER DEFAULT 0,
    underestimated_count INTEGER DEFAULT 0,
    average_accuracy_percentage DECIMAL(5,2) DEFAULT 0,
    improvement_trend DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for estimation_accuracy_history
CREATE INDEX IF NOT EXISTS idx_estimation_accuracy_history_user_id ON estimation_accuracy_history(user_id);
CREATE INDEX IF NOT EXISTS idx_estimation_accuracy_history_period ON estimation_accuracy_history(period_start, period_end);

-- Create notification_templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    subject VARCHAR(255),
    body_template TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notification_templates
CREATE INDEX IF NOT EXISTS idx_notification_templates_name ON notification_templates(name);
CREATE INDEX IF NOT EXISTS idx_notification_templates_type ON notification_templates(type);
CREATE INDEX IF NOT EXISTS idx_notification_templates_is_active ON notification_templates(is_active);

-- Create trigger for notification_templates
CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES notification_templates(id) ON DELETE SET NULL,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_template_id ON notifications(template_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON notifications(scheduled_at);

-- Create trigger for notifications
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT false,
    in_app_enabled BOOLEAN DEFAULT true,
    webhook_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    categories JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notification_preferences
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);

-- Create trigger for notification_preferences
CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create notification_logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
    attempt_number INTEGER DEFAULT 1,
    delivery_method VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_data JSONB DEFAULT '{}',
    error_message TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notification_logs
CREATE INDEX IF NOT EXISTS idx_notification_logs_notification_id ON notification_logs(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);

-- Create task_dependencies table
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dependent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    prerequisite_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'finish_to_start',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for task_dependencies
CREATE INDEX IF NOT EXISTS idx_task_dependencies_dependent ON task_dependencies(dependent_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_prerequisite ON task_dependencies(prerequisite_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_type ON task_dependencies(dependency_type);

-- Create time_entries table
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
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

-- Add constraints and checks
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'chk_priority' AND table_name = 'estimation_results') THEN
        ALTER TABLE estimation_results ADD CONSTRAINT chk_priority CHECK (priority IN ('low', 'medium', 'high', 'critical'));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'chk_complexity' AND table_name = 'estimation_results') THEN
        ALTER TABLE estimation_results ADD CONSTRAINT chk_complexity CHECK (complexity IN ('simple', 'medium', 'complex', 'very_complex'));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'chk_status' AND table_name = 'estimation_results') THEN
        ALTER TABLE estimation_results ADD CONSTRAINT chk_status CHECK (status IN ('processing', 'estimated', 'completed', 'failed'));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_estimation_results_user' AND table_name = 'estimation_results') THEN
        ALTER TABLE estimation_results ADD CONSTRAINT fk_estimation_results_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create composite indexes for better performance
CREATE INDEX IF NOT EXISTS idx_estimation_results_user_status ON estimation_results(user_id, status);
CREATE INDEX IF NOT EXISTS idx_estimation_results_project_status ON estimation_results(project_id, status);
CREATE INDEX IF NOT EXISTS idx_estimation_results_team_status ON estimation_results(team_id, status);

-- Add comments for documentation
COMMENT ON TABLE estimation_results IS 'Results of AI task estimations';
COMMENT ON TABLE estimation_feedback IS 'User feedback on estimations';
COMMENT ON TABLE batch_estimations IS 'Batch processing of multiple estimations';
COMMENT ON TABLE webhooks IS 'Webhook configurations for external integrations';
COMMENT ON TABLE metrics IS 'System metrics and performance data';
COMMENT ON TABLE task_categories IS 'Categories for organizing tasks';
COMMENT ON TABLE webhook_deliveries IS 'Webhook delivery tracking';
COMMENT ON TABLE performance_metrics IS 'Task performance measurements';
COMMENT ON TABLE user_activity_logs IS 'User activity tracking';
COMMENT ON TABLE estimation_accuracy_history IS 'Historical accuracy data';
COMMENT ON TABLE notification_templates IS 'Notification message templates';
COMMENT ON TABLE notifications IS 'User notifications';
COMMENT ON TABLE notification_preferences IS 'User notification settings';
COMMENT ON TABLE notification_logs IS 'Notification delivery logs';
COMMENT ON TABLE task_dependencies IS 'Task dependency relationships';
COMMENT ON TABLE time_entries IS 'Time tracking entries';

-- Grant permissions to taskweight_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskweight_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taskweight_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO taskweight_user;
