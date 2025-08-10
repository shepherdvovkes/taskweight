from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    projects = relationship("Project", back_populates="owner")
    tasks = relationship("Task", back_populates="assignee")
    integrations = relationship("Integration", back_populates="user")
    user_settings = relationship("UserSettings", back_populates="user", uselist=False)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="todo")
    priority = Column(String(20), default="medium")
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")

class EstimationResult(Base):
    __tablename__ = "estimation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(String(255), nullable=False, index=True)
    task_description = Column(Text, nullable=False)
    repo_url = Column(String(500))
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    status = Column(String(50), default="processing", index=True)
    error_message = Column(Text)
    confidence_score = Column(Float)
    priority = Column(String(20), default="medium")
    complexity = Column(String(20), default="medium")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    team_id = Column(String(255))
    project_id = Column(String(255))
    batch_id = Column(String(255))
    metadata = Column(JSONB, default={})
    reasoning = Column(Text)
    breakdown = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Связи
    user = relationship("User")
    feedback = relationship("EstimationFeedback", back_populates="estimation")

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    service_type = Column(String(50), nullable=False, index=True)
    service_name = Column(String(100), nullable=False)
    api_key = Column(String(500))
    api_secret = Column(String(500))
    access_token = Column(String(1000))
    refresh_token = Column(String(1000))
    webhook_url = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="integrations")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    notification_email = Column(Boolean, default=True)
    notification_push = Column(Boolean, default=False)
    theme = Column(String(20), default="light")
    estimation_preferences = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="user_settings")

class EstimationFeedback(Base):
    __tablename__ = "estimation_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estimation_id = Column(UUID(as_uuid=True), ForeignKey("estimation_results.id"), nullable=False)
    feedback = Column(Text, nullable=False)
    actual_hours = Column(Float)
    accuracy = Column(Integer)
    difficulty = Column(Integer)
    blockers = Column(JSONB, default=[])
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    estimation = relationship("EstimationResult", back_populates="feedback")

class BatchEstimation(Base):
    __tablename__ = "batch_estimations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(255), unique=True, nullable=False)
    total_tasks = Column(Integer, nullable=False)
    processing_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    status = Column(String(50), default="processing")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    team_id = Column(String(255))
    project_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    estimated_completion_time = Column(DateTime(timezone=True))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), index=True)
    record_id = Column(UUID(as_uuid=True))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Связи
    user = relationship("User")

class Webhook(Base):
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, default=[])
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"))
    is_active = Column(Boolean, default=True)
    secret_key = Column(String(255))
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    integration = relationship("Integration")

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    tags = Column(JSONB, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source = Column(String(255))
