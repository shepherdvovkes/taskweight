-- TaskWeight Metrics and Analytics System
-- This file contains metrics collection and analytics tables

-- Create metrics table for collecting system metrics
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) DEFAULT 'system'
);

-- Create performance_metrics table for task performance tracking
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL, -- 'estimation_accuracy', 'completion_time', 'quality_score'
    metric_value DECIMAL(10,4) NOT NULL,
    baseline_value DECIMAL(10,4),
    improvement_percentage DECIMAL(5,2),
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create user_activity_logs table for tracking user behavior
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(100) NOT NULL, -- 'login', 'task_create', 'estimation_request', 'integration_sync'
    activity_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create estimation_accuracy_history table for tracking estimation improvements
CREATE TABLE IF NOT EXISTS estimation_accuracy_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_estimations INTEGER DEFAULT 0,
    accurate_estimations INTEGER DEFAULT 0,
    overestimated_count INTEGER DEFAULT 0,
    underestimated_count INTEGER DEFAULT 0,
    average_accuracy_percentage DECIMAL(5,2),
    improvement_trend DECIMAL(5,2), -- compared to previous period
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for metrics
CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_source ON metrics(source);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_task_id ON performance_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_estimation_accuracy_history_user_id ON estimation_accuracy_history(user_id);
CREATE INDEX IF NOT EXISTS idx_estimation_accuracy_history_period ON estimation_accuracy_history(period_start, period_end);

-- Function to record a metric
CREATE OR REPLACE FUNCTION record_metric(
    p_metric_name VARCHAR,
    p_metric_value DECIMAL,
    p_metric_unit VARCHAR DEFAULT NULL,
    p_tags JSONB DEFAULT '{}',
    p_source VARCHAR DEFAULT 'system'
)
RETURNS UUID AS $$
DECLARE
    metric_id UUID;
BEGIN
    INSERT INTO metrics (metric_name, metric_value, metric_unit, tags, source)
    VALUES (p_metric_name, p_metric_value, p_metric_unit, p_tags, p_source)
    RETURNING id INTO metric_id;
    
    RETURN metric_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get metrics for a time period
CREATE OR REPLACE FUNCTION get_metrics(
    p_metric_name VARCHAR,
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE,
    p_aggregation VARCHAR DEFAULT 'avg' -- 'avg', 'sum', 'min', 'max', 'count'
)
RETURNS TABLE(
    metric_name VARCHAR,
    metric_value DECIMAL,
    metric_unit VARCHAR,
    aggregation_type VARCHAR,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.metric_name,
        CASE p_aggregation
            WHEN 'avg' THEN AVG(m.metric_value)
            WHEN 'sum' THEN SUM(m.metric_value)
            WHEN 'min' THEN MIN(m.metric_value)
            WHEN 'max' THEN MAX(m.metric_value)
            WHEN 'count' THEN COUNT(m.metric_value)::DECIMAL
            ELSE AVG(m.metric_value)
        END as metric_value,
        m.metric_unit,
        p_aggregation as aggregation_type,
        p_start_time as period_start,
        p_end_time as period_end
    FROM metrics m
    WHERE m.metric_name = p_metric_name
        AND m.timestamp >= p_start_time
        AND m.timestamp <= p_end_time
    GROUP BY m.metric_name, m.metric_unit;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate user performance score
CREATE OR REPLACE FUNCTION calculate_user_performance_score(
    p_user_id UUID,
    p_period_days INTEGER DEFAULT 30
)
RETURNS TABLE(
    user_id UUID,
    total_tasks INTEGER,
    completed_tasks INTEGER,
    average_accuracy DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    trend VARCHAR(20)
) AS $$
DECLARE
    period_start DATE;
    period_end DATE;
    current_period_accuracy DECIMAL(5,2);
    previous_period_accuracy DECIMAL(5,2);
BEGIN
    period_end := CURRENT_DATE;
    period_start := period_end - p_period_days;
    
    -- Get current period accuracy
    SELECT COALESCE(AVG(eah.average_accuracy_percentage), 0)
    INTO current_period_accuracy
    FROM estimation_accuracy_history eah
    WHERE eah.user_id = p_user_id
        AND eah.period_start >= period_start
        AND eah.period_end <= period_end;
    
    -- Get previous period accuracy
    SELECT COALESCE(AVG(eah.average_accuracy_percentage), 0)
    INTO previous_period_accuracy
    FROM estimation_accuracy_history eah
    WHERE eah.user_id = p_user_id
        AND eah.period_start >= period_start - p_period_days
        AND eah.period_end <= period_start;
    
    RETURN QUERY
    SELECT 
        p_user_id as user_id,
        COUNT(t.id)::INTEGER as total_tasks,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::INTEGER as completed_tasks,
        current_period_accuracy,
        CASE 
            WHEN current_period_accuracy >= 90 THEN 5.0
            WHEN current_period_accuracy >= 80 THEN 4.0
            WHEN current_period_accuracy >= 70 THEN 3.0
            WHEN current_period_accuracy >= 60 THEN 2.0
            ELSE 1.0
        END as performance_score,
        CASE 
            WHEN current_period_accuracy > previous_period_accuracy THEN 'improving'
            WHEN current_period_accuracy < previous_period_accuracy THEN 'declining'
            ELSE 'stable'
        END as trend
    FROM tasks t
    WHERE t.assignee_id = p_user_id
        AND t.created_at >= period_start;
END;
$$ LANGUAGE plpgsql;

-- Function to get system health metrics
CREATE OR REPLACE FUNCTION get_system_health_metrics()
RETURNS TABLE(
    metric_name VARCHAR,
    current_value DECIMAL,
    unit VARCHAR,
    status VARCHAR,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.metric_name,
        m.metric_value as current_value,
        m.metric_unit as unit,
        CASE 
            WHEN m.metric_name LIKE '%error%' AND m.metric_value > 0 THEN 'critical'
            WHEN m.metric_name LIKE '%response_time%' AND m.metric_value > 1000 THEN 'warning'
            WHEN m.metric_name LIKE '%uptime%' AND m.metric_value < 99 THEN 'warning'
            ELSE 'healthy'
        END as status,
        m.timestamp as last_updated
    FROM metrics m
    WHERE m.timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        AND m.metric_name IN ('error_rate', 'response_time_ms', 'uptime_percentage', 'active_users')
    ORDER BY m.timestamp DESC;
END;
$$ LANGUAGE plpgsql;


