-- TaskWeight Webhooks System
-- This file contains webhook management tables and functions

-- Create webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    secret_key VARCHAR(255),
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create webhook_deliveries table for tracking webhook attempts
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    error_message TEXT,
    attempt_count INTEGER DEFAULT 1,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for webhooks
CREATE INDEX IF NOT EXISTS idx_webhooks_integration_id ON webhooks(integration_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_next_retry_at ON webhook_deliveries(next_retry_at);

-- Create triggers for webhooks
CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to register webhook delivery
CREATE OR REPLACE FUNCTION register_webhook_delivery(
    p_webhook_id UUID,
    p_event_type VARCHAR,
    p_payload JSONB
)
RETURNS UUID AS $$
DECLARE
    delivery_id UUID;
BEGIN
    INSERT INTO webhook_deliveries (webhook_id, event_type, payload)
    VALUES (p_webhook_id, p_event_type, p_payload)
    RETURNING id INTO delivery_id;
    
    RETURN delivery_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending webhook deliveries
CREATE OR REPLACE FUNCTION get_pending_webhook_deliveries()
RETURNS TABLE(
    delivery_id UUID,
    webhook_id UUID,
    webhook_url VARCHAR,
    event_type VARCHAR,
    payload JSONB,
    attempt_count INTEGER,
    secret_key VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        wd.id as delivery_id,
        wd.webhook_id,
        w.url as webhook_url,
        wd.event_type,
        wd.payload,
        wd.attempt_count,
        w.secret_key
    FROM webhook_deliveries wd
    JOIN webhooks w ON wd.webhook_id = w.id
    WHERE w.is_active = true 
        AND wd.delivered_at IS NULL
        AND (wd.next_retry_at IS NULL OR wd.next_retry_at <= CURRENT_TIMESTAMP)
        AND wd.attempt_count <= w.retry_count
    ORDER BY wd.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Function to mark webhook delivery as successful
CREATE OR REPLACE FUNCTION mark_webhook_delivered(
    p_delivery_id UUID,
    p_response_status INTEGER,
    p_response_body TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE webhook_deliveries 
    SET 
        response_status = p_response_status,
        response_body = p_response_body,
        delivered_at = CURRENT_TIMESTAMP
    WHERE id = p_delivery_id;
END;
$$ LANGUAGE plpgsql;

-- Function to mark webhook delivery as failed
CREATE OR REPLACE FUNCTION mark_webhook_failed(
    p_delivery_id UUID,
    p_error_message TEXT,
    p_next_retry_at TIMESTAMP WITH TIME ZONE
)
RETURNS VOID AS $$
BEGIN
    UPDATE webhook_deliveries 
    SET 
        error_message = p_error_message,
        next_retry_at = p_next_retry_at,
        attempt_count = attempt_count + 1
    WHERE id = p_delivery_id;
END;
$$ LANGUAGE plpgsql;
