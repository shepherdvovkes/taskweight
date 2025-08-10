-- TaskWeight Notifications System
-- This file contains notification management tables and functions

-- Create notification_templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'email', 'push', 'in_app', 'webhook'
    subject VARCHAR(255),
    body_template TEXT NOT NULL,
    variables JSONB DEFAULT '{}', -- template variables
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES notification_templates(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL, -- 'email', 'push', 'in_app', 'webhook'
    title VARCHAR(255),
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}', -- additional data
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed', 'read'
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

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT false,
    in_app_enabled BOOLEAN DEFAULT true,
    webhook_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    categories JSONB DEFAULT '{}', -- notification categories and their settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_logs table for tracking delivery attempts
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'retry'
    response_data JSONB,
    error_message TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled_at ON notifications(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS idx_notification_templates_type ON notification_templates(type);
CREATE INDEX IF NOT EXISTS idx_notification_templates_is_active ON notification_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_notification_id ON notification_logs(notification_id);

-- Create triggers for notifications
CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_preferences_updated_at BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create a notification
CREATE OR REPLACE FUNCTION create_notification(
    p_user_id UUID,
    p_template_name VARCHAR,
    p_type VARCHAR DEFAULT 'in_app',
    p_data JSONB DEFAULT '{}',
    p_priority VARCHAR DEFAULT 'normal',
    p_scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    template_record notification_templates%ROWTYPE;
    notification_id UUID;
    title_text VARCHAR(255);
    message_text TEXT;
BEGIN
    -- Get template
    SELECT * INTO template_record
    FROM notification_templates
    WHERE name = p_template_name AND is_active = true;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Template % not found or inactive', p_template_name;
    END IF;
    
    -- Process template variables
    title_text := COALESCE(template_record.subject, '');
    message_text := template_record.body_template;
    
    -- Replace variables in message (simple variable replacement)
    -- In production, you might want to use a more sophisticated templating engine
    FOR i IN 0..jsonb_array_length(p_data) - 1 LOOP
        message_text := REPLACE(message_text, '{{' || i || '}}', p_data->>i);
    END LOOP;
    
    -- Create notification
    INSERT INTO notifications (
        user_id, template_id, type, title, message, data, 
        priority, scheduled_at
    ) VALUES (
        p_user_id, template_record.id, p_type, title_text, message_text, 
        p_data, p_priority, p_scheduled_at
    ) RETURNING id INTO notification_id;
    
    RETURN notification_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending notifications for a user
CREATE OR REPLACE FUNCTION get_pending_notifications(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE(
    id UUID,
    title VARCHAR,
    message TEXT,
    type VARCHAR,
    priority VARCHAR,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.title,
        n.message,
        n.type,
        n.priority,
        n.data,
        n.created_at
    FROM notifications n
    WHERE n.user_id = p_user_id
        AND n.status = 'pending'
        AND (n.scheduled_at IS NULL OR n.scheduled_at <= CURRENT_TIMESTAMP)
    ORDER BY 
        CASE n.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            WHEN 'normal' THEN 3
            WHEN 'low' THEN 4
        END,
        n.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to mark notification as sent
CREATE OR REPLACE FUNCTION mark_notification_sent(
    p_notification_id UUID,
    p_delivery_method VARCHAR,
    p_response_data JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE notifications 
    SET 
        status = 'sent',
        sent_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_notification_id;
    
    -- Log the delivery attempt
    INSERT INTO notification_logs (
        notification_id, attempt_number, delivery_method, 
        status, response_data
    ) VALUES (
        p_notification_id, 1, p_delivery_method, 'success', p_response_data
    );
END;
$$ LANGUAGE plpgsql;

-- Function to mark notification as failed
CREATE OR REPLACE FUNCTION mark_notification_failed(
    p_notification_id UUID,
    p_delivery_method VARCHAR,
    p_error_message TEXT,
    p_response_data JSONB DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    current_retry_count INTEGER;
    max_retries INTEGER;
    new_status VARCHAR(20);
BEGIN
    SELECT retry_count, max_retries INTO current_retry_count, max_retries
    FROM notifications WHERE id = p_notification_id;
    
    IF current_retry_count >= max_retries THEN
        new_status := 'failed';
    ELSE
        new_status := 'pending';
    END IF;
    
    UPDATE notifications 
    SET 
        status = new_status,
        retry_count = current_retry_count + 1,
        error_message = p_error_message,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_notification_id;
    
    -- Log the failed attempt
    INSERT INTO notification_logs (
        notification_id, attempt_number, delivery_method, 
        status, error_message, response_data
    ) VALUES (
        p_notification_id, current_retry_count + 1, p_delivery_method, 
        'failed', p_error_message, p_response_data
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get notification statistics for a user
CREATE OR REPLACE FUNCTION get_notification_stats(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE(
    total_notifications BIGINT,
    sent_notifications BIGINT,
    failed_notifications BIGINT,
    read_notifications BIGINT,
    delivery_success_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_notifications,
        COUNT(CASE WHEN status = 'sent' OR status = 'delivered' THEN 1 END)::BIGINT as sent_notifications,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::BIGINT as failed_notifications,
        COUNT(CASE WHEN status = 'read' THEN 1 END)::BIGINT as read_notifications,
        ROUND(
            (COUNT(CASE WHEN status = 'sent' OR status = 'delivered' THEN 1 END)::DECIMAL / 
             COUNT(*)::DECIMAL * 100), 2
        ) as delivery_success_rate
    FROM notifications
    WHERE user_id = p_user_id
        AND created_at >= CURRENT_DATE - p_days;
END;
$$ LANGUAGE plpgsql;


