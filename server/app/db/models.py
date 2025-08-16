from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", back_populates="assignee")
    estimations = relationship("EstimationResult", back_populates="user")
    time_entries = relationship("TimeEntry", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False)
    activity_logs = relationship("UserActivityLog", back_populates="user")
    accuracy_history = relationship("EstimationAccuracyHistory", back_populates="user")


class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    categories = relationship("TaskCategory", back_populates="project")


class TaskCategory(Base):
    __tablename__ = 'task_categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#000000')
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="categories")
    tasks = relationship("Task", back_populates="category")


class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    estimated_hours = Column(Numeric(5, 2))
    actual_hours = Column(Numeric(5, 2))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    category_id = Column(UUID(as_uuid=True), ForeignKey('task_categories.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")
    category = relationship("TaskCategory", back_populates="tasks")
    estimation_results = relationship("EstimationResult", back_populates="task")
    time_entries = relationship("TimeEntry", back_populates="task")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.dependent_task_id", back_populates="dependent_task")
    prerequisites = relationship("TaskDependency", foreign_keys="TaskDependency.prerequisite_task_id", back_populates="prerequisite_task")
    performance_metrics = relationship("PerformanceMetric", back_populates="task")


class Integration(Base):
    __tablename__ = 'integrations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    config = Column(JSONB)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    webhooks = relationship("Webhook", back_populates="integration")


class EstimationResult(Base):
    __tablename__ = 'estimation_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    estimated_hours = Column(Numeric(5, 2), nullable=False)
    status = Column(String(50), nullable=False)
    priority = Column(String(20))
    complexity = Column(String(20))
    confidence_score = Column(Numeric(5, 2))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    team_id = Column(String(255))
    project_id = Column(String(255))
    batch_id = Column(String(255))
    task_metadata = Column(JSONB, default={})
    reasoning = Column(Text)
    breakdown = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='chk_priority'),
        CheckConstraint("complexity IN ('simple', 'medium', 'complex', 'very_complex')", name='chk_complexity'),
        CheckConstraint("status IN ('processing', 'estimated', 'completed', 'failed')", name='chk_status'),
    )
    
    # Relationships
    task = relationship("Task", back_populates="estimation_results")
    user = relationship("User", back_populates="estimations")
    feedback = relationship("EstimationFeedback", back_populates="estimation")


class EstimationFeedback(Base):
    __tablename__ = 'estimation_feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estimation_id = Column(UUID(as_uuid=True), ForeignKey('estimation_results.id', ondelete='CASCADE'), nullable=False)
    feedback = Column(Text, nullable=False)
    actual_hours = Column(Numeric(5, 2))
    accuracy = Column(Integer)
    difficulty = Column(Integer)
    blockers = Column(JSONB, default=[])
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("accuracy >= 0 AND accuracy <= 100", name='chk_accuracy'),
        CheckConstraint("difficulty >= 1 AND difficulty <= 5", name='chk_difficulty'),
    )
    
    # Relationships
    estimation = relationship("EstimationResult", back_populates="feedback")


class BatchEstimation(Base):
    __tablename__ = 'batch_estimations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(255), unique=True, nullable=False)
    total_tasks = Column(Integer, nullable=False)
    processing_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    status = Column(String(50), default='processing')
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    team_id = Column(String(255))
    project_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    estimated_completion_time = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")


class Webhook(Base):
    __tablename__ = 'webhooks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, default=[])
    integration_id = Column(UUID(as_uuid=True), ForeignKey('integrations.id', ondelete='CASCADE'))
    is_active = Column(Boolean, default=True)
    secret_key = Column(String(255))
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    integration = relationship("Integration", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook")


class WebhookDelivery(Base):
    __tablename__ = 'webhook_deliveries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    response_status = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    attempt_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")


class Metric(Base):
    __tablename__ = 'metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Numeric(10, 4), nullable=False)
    metric_unit = Column(String(50))
    tags = Column(JSONB, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String(255))


class TimeEntry(Base):
    __tablename__ = 'time_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    description = Column(Text)
    is_billable = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="time_entries")
    user = relationship("User", back_populates="time_entries")


class TaskDependency(Base):
    __tablename__ = 'task_dependencies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dependent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    prerequisite_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    dependency_type = Column(String(50), default='finish_to_start')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    dependent_task = relationship("Task", foreign_keys=[dependent_task_id], back_populates="dependencies")
    prerequisite_task = relationship("Task", foreign_keys=[prerequisite_task_id], back_populates="prerequisites")


class PerformanceMetric(Base):
    __tablename__ = 'performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    metric_type = Column(String(100), nullable=False)
    metric_value = Column(Numeric(10, 4), nullable=False)
    baseline_value = Column(Numeric(10, 4))
    improvement_percentage = Column(Numeric(5, 2))
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text)
    
    # Relationships
    task = relationship("Task", back_populates="performance_metrics")


class UserActivityLog(Base):
    __tablename__ = 'user_activity_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    activity_type = Column(String(100), nullable=False)
    activity_data = Column(JSONB, default={})
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")


class EstimationAccuracyHistory(Base):
    __tablename__ = 'estimation_accuracy_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_estimations = Column(Integer, default=0)
    accurate_estimations = Column(Integer, default=0)
    overestimated_count = Column(Integer, default=0)
    underestimated_count = Column(Integer, default=0)
    average_accuracy_percentage = Column(Numeric(5, 2), default=0)
    improvement_trend = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accuracy_history")


class NotificationTemplate(Base):
    __tablename__ = 'notification_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    subject = Column(String(255))
    body_template = Column(Text, nullable=False)
    variables = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    notifications = relationship("Notification", back_populates="template")


class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('notification_templates.id', ondelete='SET NULL'))
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB, default={})
    priority = Column(String(20), default='normal')
    status = Column(String(50), default='pending')
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")
    logs = relationship("NotificationLog", back_populates="notification")


class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    webhook_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(8), default='22:00:00')  # HH:MM:SS format
    quiet_hours_end = Column(String(8), default='08:00:00')
    timezone = Column(String(50), default='UTC')
    categories = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class NotificationLog(Base):
    __tablename__ = 'notification_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(UUID(as_uuid=True), ForeignKey('notifications.id', ondelete='CASCADE'), nullable=False)
    attempt_number = Column(Integer, default=1)
    delivery_method = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    response_data = Column(JSONB, default={})
    error_message = Column(Text)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    notification = relationship("Notification", back_populates="logs")
