-- TaskWeight Database Functions
-- This script contains additional functions for the database

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

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

-- Function to get user estimation accuracy
CREATE OR REPLACE FUNCTION get_user_estimation_accuracy(p_user_id UUID, p_days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    total_estimations BIGINT,
    accurate_estimations BIGINT,
    overestimated_count BIGINT,
    underestimated_count BIGINT,
    average_accuracy_percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_estimations,
        COUNT(CASE WHEN accuracy >= 80 THEN 1 END)::BIGINT as accurate_estimations,
        COUNT(CASE WHEN actual_hours > estimated_hours THEN 1 END)::BIGINT as overestimated_count,
        COUNT(CASE WHEN actual_hours < estimated_hours THEN 1 END)::BIGINT as underestimated_count,
        AVG(accuracy)::DECIMAL(5,2) as average_accuracy_percentage
    FROM estimation_results er
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE er.user_id = p_user_id 
    AND er.created_at >= CURRENT_DATE - INTERVAL '1 day' * p_days_back
    AND ef.actual_hours IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to get project statistics
CREATE OR REPLACE FUNCTION get_project_statistics(p_project_id VARCHAR(255))
RETURNS TABLE(
    total_tasks BIGINT,
    completed_tasks BIGINT,
    in_progress_tasks BIGINT,
    total_estimated_hours DECIMAL(10,2),
    total_actual_hours DECIMAL(10,2),
    average_accuracy DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_tasks,
        COUNT(CASE WHEN er.status = 'completed' THEN 1 END)::BIGINT as completed_tasks,
        COUNT(CASE WHEN er.status = 'processing' THEN 1 END)::BIGINT as in_progress_tasks,
        SUM(er.estimated_hours)::DECIMAL(10,2) as total_estimated_hours,
        SUM(COALESCE(ef.actual_hours, 0))::DECIMAL(10,2) as total_actual_hours,
        AVG(ef.accuracy)::DECIMAL(5,2) as average_accuracy
    FROM estimation_results er
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE er.project_id = p_project_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get team performance metrics
CREATE OR REPLACE FUNCTION get_team_performance_metrics(p_team_id VARCHAR(255), p_period_days INTEGER DEFAULT 30)
RETURNS TABLE(
    team_id VARCHAR(255),
    total_estimations BIGINT,
    average_accuracy DECIMAL(5,2),
    total_estimated_hours DECIMAL(10,2),
    total_actual_hours DECIMAL(10,2),
    efficiency_ratio DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        er.team_id,
        COUNT(*)::BIGINT as total_estimations,
        AVG(ef.accuracy)::DECIMAL(5,2) as average_accuracy,
        SUM(er.estimated_hours)::DECIMAL(10,2) as total_estimated_hours,
        SUM(COALESCE(ef.actual_hours, 0))::DECIMAL(10,2) as total_actual_hours,
        CASE 
            WHEN SUM(er.estimated_hours) > 0 
            THEN (SUM(COALESCE(ef.actual_hours, 0)) / SUM(er.estimated_hours))::DECIMAL(5,2)
            ELSE 0 
        END as efficiency_ratio
    FROM estimation_results er
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE er.team_id = p_team_id 
    AND er.created_at >= CURRENT_DATE - INTERVAL '1 day' * p_period_days
    GROUP BY er.team_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate estimation confidence score
CREATE OR REPLACE FUNCTION calculate_confidence_score(
    p_task_complexity VARCHAR(20),
    p_user_experience_level VARCHAR(20),
    p_historical_accuracy DECIMAL(5,2)
)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    complexity_score DECIMAL(5,2);
    experience_score DECIMAL(5,2);
    accuracy_score DECIMAL(5,2);
    final_score DECIMAL(5,2);
BEGIN
    -- Complexity score (lower complexity = higher confidence)
    CASE p_task_complexity
        WHEN 'simple' THEN complexity_score := 0.9;
        WHEN 'medium' THEN complexity_score := 0.7;
        WHEN 'complex' THEN complexity_score := 0.5;
        WHEN 'very_complex' THEN complexity_score := 0.3;
        ELSE complexity_score := 0.5;
    END CASE;
    
    -- Experience score
    CASE p_user_experience_level
        WHEN 'beginner' THEN experience_score := 0.4;
        WHEN 'intermediate' THEN experience_score := 0.7;
        WHEN 'expert' THEN experience_score := 0.9;
        ELSE experience_score := 0.6;
    END CASE;
    
    -- Historical accuracy score
    IF p_historical_accuracy IS NULL THEN
        accuracy_score := 0.5;
    ELSE
        accuracy_score := p_historical_accuracy / 100.0;
    END IF;
    
    -- Calculate weighted final score
    final_score := (complexity_score * 0.3 + experience_score * 0.3 + accuracy_score * 0.4) * 100;
    
    -- Ensure score is between 0 and 100
    final_score := GREATEST(0, LEAST(100, final_score));
    
    RETURN final_score;
END;
$$ LANGUAGE plpgsql;

-- Function to get batch processing status
CREATE OR REPLACE FUNCTION get_batch_status(p_batch_id VARCHAR(255))
RETURNS TABLE(
    batch_id VARCHAR(255),
    total_tasks INTEGER,
    processing_tasks INTEGER,
    completed_tasks INTEGER,
    failed_tasks INTEGER,
    status VARCHAR(50),
    progress_percentage DECIMAL(5,2),
    estimated_completion_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        be.batch_id,
        be.total_tasks,
        be.processing_tasks,
        be.completed_tasks,
        be.failed_tasks,
        be.status,
        CASE 
            WHEN be.total_tasks > 0 
            THEN ((be.completed_tasks + be.failed_tasks)::DECIMAL / be.total_tasks * 100)::DECIMAL(5,2)
            ELSE 0 
        END as progress_percentage,
        be.estimated_completion_time
    FROM batch_estimations be
    WHERE be.batch_id = p_batch_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity(
    p_user_id UUID,
    p_activity_type VARCHAR(100),
    p_activity_data JSONB DEFAULT '{}',
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_session_id VARCHAR(255) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    activity_id UUID;
BEGIN
    INSERT INTO user_activity_logs (
        user_id, 
        activity_type, 
        activity_data, 
        ip_address, 
        user_agent, 
        session_id
    ) VALUES (
        p_user_id, 
        p_activity_type, 
        p_activity_data, 
        p_ip_address, 
        p_user_agent, 
        p_session_id
    ) RETURNING id INTO activity_id;
    
    RETURN activity_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create notification
CREATE OR REPLACE FUNCTION create_notification(
    p_user_id UUID,
    p_type VARCHAR(100),
    p_title VARCHAR(255),
    p_message TEXT,
    p_priority VARCHAR(20) DEFAULT 'normal',
    p_data JSONB DEFAULT '{}',
    p_scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    notification_id UUID;
BEGIN
    INSERT INTO notifications (
        user_id,
        type,
        title,
        message,
        priority,
        data,
        scheduled_at
    ) VALUES (
        p_user_id,
        p_type,
        p_title,
        p_message,
        p_priority,
        p_data,
        p_scheduled_at
    ) RETURNING id INTO notification_id;
    
    RETURN notification_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get user notifications
CREATE OR REPLACE FUNCTION get_user_notifications(
    p_user_id UUID,
    p_status VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    id UUID,
    type VARCHAR(100),
    title VARCHAR(255),
    message TEXT,
    priority VARCHAR(20),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.type,
        n.title,
        n.message,
        n.priority,
        n.status,
        n.created_at,
        n.read_at
    FROM notifications n
    WHERE n.user_id = p_user_id
    AND (p_status IS NULL OR n.status = p_status)
    ORDER BY 
        CASE n.priority
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'normal' THEN 3
            WHEN 'low' THEN 4
            ELSE 5
        END,
        n.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function to mark notification as read
CREATE OR REPLACE FUNCTION mark_notification_read(p_notification_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE notifications 
    SET read_at = CURRENT_TIMESTAMP
    WHERE id = p_notification_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to get task dependencies
CREATE OR REPLACE FUNCTION get_task_dependencies(p_task_id UUID)
RETURNS TABLE(
    dependency_id UUID,
    dependent_task_id UUID,
    prerequisite_task_id UUID,
    dependency_type VARCHAR(50),
    prerequisite_title VARCHAR(255),
    prerequisite_status VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        td.id as dependency_id,
        td.dependent_task_id,
        td.prerequisite_task_id,
        td.dependency_type,
        t.title as prerequisite_title,
        er.status as prerequisite_status
    FROM task_dependencies td
    JOIN tasks t ON td.prerequisite_task_id = t.id
    LEFT JOIN estimation_results er ON t.title = er.card_id
WHERE td.dependent_task_id = p_task_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check if task can be started (dependencies met)
CREATE OR REPLACE FUNCTION can_task_start(p_task_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    blocked_tasks INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO blocked_tasks
    FROM task_dependencies td
    JOIN estimation_results er ON td.prerequisite_task_id::text = er.card_id
WHERE td.dependent_task_id = p_task_id
    AND er.status != 'completed';
    
    RETURN blocked_tasks = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to get time tracking summary
CREATE OR REPLACE FUNCTION get_time_tracking_summary(
    p_user_id UUID,
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '7 days',
    p_end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    date DATE,
    total_minutes INTEGER,
    billable_minutes INTEGER,
    task_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(te.start_time) as date,
        SUM(te.duration_minutes)::INTEGER as total_minutes,
        SUM(CASE WHEN te.is_billable THEN te.duration_minutes ELSE 0 END)::INTEGER as billable_minutes,
        COUNT(DISTINCT te.task_id)::INTEGER as task_count
    FROM time_entries te
    WHERE te.user_id = p_user_id
    AND DATE(te.start_time) BETWEEN p_start_date AND p_end_date
    GROUP BY DATE(te.start_time)
    ORDER BY date;
END;
$$ LANGUAGE plpgsql;

-- Function to get estimation trends
CREATE OR REPLACE FUNCTION get_estimation_trends(
    p_user_id UUID,
    p_days_back INTEGER DEFAULT 90
)
RETURNS TABLE(
    week_start DATE,
    total_estimations INTEGER,
    average_accuracy DECIMAL(5,2),
    average_estimated_hours DECIMAL(5,2),
    average_actual_hours DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE_TRUNC('week', er.created_at)::DATE as week_start,
        COUNT(*)::INTEGER as total_estimations,
        AVG(ef.accuracy)::DECIMAL(5,2) as average_accuracy,
        AVG(er.estimated_hours)::DECIMAL(5,2) as average_estimated_hours,
        AVG(ef.actual_hours)::DECIMAL(5,2) as average_actual_hours
    FROM estimation_results er
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE er.user_id = p_user_id
    AND er.created_at >= CURRENT_DATE - INTERVAL '1 day' * p_days_back
    GROUP BY DATE_TRUNC('week', er.created_at)
    ORDER BY week_start;
END;
$$ LANGUAGE plpgsql;

-- Function to search tasks by text
CREATE OR REPLACE FUNCTION search_tasks(search_text TEXT)
RETURNS TABLE(
    id UUID,
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(20),
    project_id VARCHAR(255),
    assignee_id UUID,
    category_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.description,
        t.status,
        t.priority,
        t.project_id,
        t.assignee_id,
        t.category_id,
        t.created_at,
        t.updated_at
    FROM tasks t
    WHERE 
        t.title ILIKE '%' || search_text || '%'
        OR t.description ILIKE '%' || search_text || '%'
        OR t.status ILIKE '%' || search_text || '%'
        OR t.priority ILIKE '%' || search_text || '%';
END;
$$ LANGUAGE plpgsql;

-- Function to record metrics
CREATE OR REPLACE FUNCTION record_metric(
    p_metric_name VARCHAR(100),
    p_metric_value DECIMAL(10,4),
    p_metric_unit VARCHAR(20),
    p_source VARCHAR(100),
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    metric_id UUID;
BEGIN
    INSERT INTO metrics (metric_name, metric_value, metric_unit, source, metadata)
    VALUES (p_metric_name, p_metric_value, p_metric_unit, p_source, p_metadata)
    RETURNING id INTO metric_id;
    
    RETURN metric_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get metrics
CREATE OR REPLACE FUNCTION get_metrics(
    p_metric_name VARCHAR(100) DEFAULT NULL,
    p_source VARCHAR(100) DEFAULT NULL,
    p_hours_back INTEGER DEFAULT 24
)
RETURNS TABLE(
    id UUID,
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,4),
    metric_unit VARCHAR(20),
    source VARCHAR(100),
    metadata JSONB,
    timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.metric_name,
        m.metric_value,
        m.metric_unit,
        m.source,
        m.metadata,
        m.timestamp
    FROM metrics m
    WHERE 
        (p_metric_name IS NULL OR m.metric_name = p_metric_name)
        AND (p_source IS NULL OR m.source = p_source)
        AND m.timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * p_hours_back
    ORDER BY m.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending notifications
CREATE OR REPLACE FUNCTION get_pending_notifications(p_user_id UUID)
RETURNS TABLE(
    id UUID,
    user_id UUID,
    type VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    priority VARCHAR(20),
    status VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP,
    read_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id,
        n.user_id,
        n.type,
        n.title,
        n.message,
        n.priority,
        n.status,
        n.metadata,
        n.created_at,
        n.read_at
    FROM notifications n
    WHERE n.user_id = p_user_id
        AND n.status = 'pending'
        AND n.read_at IS NULL
    ORDER BY n.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get user stats
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id UUID)
RETURNS TABLE(
    user_id UUID,
    username VARCHAR(100),
    email VARCHAR(255),
    total_tasks BIGINT,
    completed_tasks BIGINT,
    total_estimated_hours DECIMAL(10,2),
    total_actual_hours DECIMAL(10,2),
    average_accuracy DECIMAL(5,2),
    last_activity TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.username,
        u.email,
        COUNT(DISTINCT t.id)::BIGINT as total_tasks,
        COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END)::BIGINT as completed_tasks,
        COALESCE(SUM(t.estimated_hours), 0)::DECIMAL(10,2) as total_estimated_hours,
        COALESCE(SUM(t.actual_hours), 0)::DECIMAL(10,2) as total_actual_hours,
        AVG(ef.accuracy)::DECIMAL(5,2) as average_accuracy,
        MAX(t.updated_at) as last_activity
    FROM users u
    LEFT JOIN tasks t ON u.id = t.assignee_id
    LEFT JOIN estimation_results er ON t.title = er.card_id
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE u.id = p_user_id
    GROUP BY u.id, u.username, u.email;
END;
$$ LANGUAGE plpgsql;

-- Function to get project timeline
CREATE OR REPLACE FUNCTION get_project_timeline(p_project_id VARCHAR(255))
RETURNS TABLE(
    project_id VARCHAR(255),
    project_name VARCHAR(255),
    total_tasks BIGINT,
    completed_tasks BIGINT,
    in_progress_tasks BIGINT,
    pending_tasks BIGINT,
    total_estimated_hours DECIMAL(10,2),
    total_actual_hours DECIMAL(10,2),
    start_date DATE,
    estimated_completion DATE,
    progress_percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id as project_id,
        p.name as project_name,
        COUNT(t.id)::BIGINT as total_tasks,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::BIGINT as completed_tasks,
        COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END)::BIGINT as in_progress_tasks,
        COUNT(CASE WHEN t.status = 'pending' THEN 1 END)::BIGINT as pending_tasks,
        COALESCE(SUM(t.estimated_hours), 0)::DECIMAL(10,2) as total_estimated_hours,
        COALESCE(SUM(t.actual_hours), 0)::DECIMAL(10,2) as total_actual_hours,
        MIN(t.created_at)::DATE as start_date,
        MAX(t.due_date) as estimated_completion,
        CASE 
            WHEN COUNT(t.id) > 0 
            THEN (COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::DECIMAL / COUNT(t.id) * 100)::DECIMAL(5,2)
            ELSE 0 
        END as progress_percentage
    FROM projects p
    LEFT JOIN tasks t ON p.id = t.project_id
    WHERE p.id = p_project_id
    GROUP BY p.id, p.name;
END;
$$ LANGUAGE plpgsql;

-- Function to get estimation accuracy
CREATE OR REPLACE FUNCTION get_estimation_accuracy(p_user_id UUID DEFAULT NULL, p_days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    user_id UUID,
    username VARCHAR(100),
    total_estimations BIGINT,
    accurate_estimations BIGINT,
    overestimated_count BIGINT,
    underestimated_count BIGINT,
    average_accuracy DECIMAL(5,2),
    average_estimated_hours DECIMAL(5,2),
    average_actual_hours DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.username,
        COUNT(er.id)::BIGINT as total_estimations,
        COUNT(CASE WHEN ef.accuracy >= 80 THEN 1 END)::BIGINT as accurate_estimations,
        COUNT(CASE WHEN ef.actual_hours > er.estimated_hours THEN 1 END)::BIGINT as overestimated_count,
        COUNT(CASE WHEN ef.actual_hours < er.estimated_hours THEN 1 END)::BIGINT as underestimated_count,
        AVG(ef.accuracy)::DECIMAL(5,2) as average_accuracy,
        AVG(er.estimated_hours)::DECIMAL(5,2) as average_estimated_hours,
        AVG(ef.actual_hours)::DECIMAL(5,2) as average_actual_hours
    FROM users u
    LEFT JOIN estimation_results er ON u.id = er.user_id
    LEFT JOIN estimation_feedback ef ON er.id = ef.estimation_id
    WHERE 
        (p_user_id IS NULL OR u.id = p_user_id)
        AND er.created_at >= CURRENT_DATE - INTERVAL '1 day' * p_days_back
        AND ef.actual_hours IS NOT NULL
    GROUP BY u.id, u.username;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO taskweight_user;
