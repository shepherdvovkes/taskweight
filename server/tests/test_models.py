"""
Тесты для моделей данных TaskWeight
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.db.models import (
    User, Project, Task, TaskCategory, EstimationResult,
    Integration, AuditLog, UserSettings, Metric,
    PerformanceMetric, UserActivityLog, EstimationAccuracyHistory,
    NotificationTemplate, Notification, NotificationPreference,
    NotificationLog, Webhook, WebhookDelivery, TaskDependency,
    TimeEntry
)

def test_user_model(db_session: Session):
    """Тест модели пользователя"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None

def test_user_password_hashing(db_session: Session):
    """Тест хеширования пароля пользователя"""
    user = User(
        username="passworduser",
        email="password@example.com",
        full_name="Password User"
    )
    user.set_password("securepassword123")
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.check_password("securepassword123") is True
    assert user.check_password("wrongpassword") is False

def test_project_model(db_session: Session, sample_user):
    """Тест модели проекта"""
    project = Project(
        name="Test Project",
        description="Test project description",
        owner_id=sample_user.id,
        status="active",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30)
    )
    
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.owner_id == sample_user.id
    assert project.status == "active"
    assert project.created_at is not None

def test_task_model(db_session: Session, sample_project):
    """Тест модели задачи"""
    task = Task(
        title="Test Task",
        description="Test task description",
        project_id=sample_project.id,
        status="todo",
        priority="high",
        estimated_hours=8.0,
        actual_hours=0.0
    )
    
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.project_id == sample_project.id
    assert task.status == "todo"
    assert task.priority == "high"
    assert task.estimated_hours == 8.0

def test_task_category_model(db_session: Session):
    """Тест модели категории задач"""
    category = TaskCategory(
        name="Development",
        description="Software development tasks",
        color="#007bff"
    )
    
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    
    assert category.id is not None
    assert category.name == "Development"
    assert category.color == "#007bff"

def test_estimation_result_model(db_session: Session, sample_task):
    """Тест модели результата оценки"""
    estimation = EstimationResult(
        task_id=sample_task.id,
        estimated_hours=12.5,
        confidence_level=0.85,
        method="ai_estimation",
        factors={"complexity": "high", "experience": "medium"}
    )
    
    db_session.add(estimation)
    db_session.commit()
    db_session.refresh(estimation)
    
    assert estimation.id is not None
    assert estimation.task_id == sample_task.id
    assert estimation.estimated_hours == 12.5
    assert estimation.confidence_level == 0.85
    assert estimation.method == "ai_estimation"

def test_integration_model(db_session: Session, sample_user):
    """Тест модели интеграции"""
    integration = Integration(
        user_id=sample_user.id,
        platform="jira",
        api_key="test_api_key",
        base_url="https://test.atlassian.net",
        is_active=True
    )
    
    db_session.add(integration)
    db_session.commit()
    db_session.refresh(integration)
    
    assert integration.id is not None
    assert integration.user_id == sample_user.id
    assert integration.platform == "jira"
    assert integration.is_active is True

def test_audit_log_model(db_session: Session, sample_user):
    """Тест модели аудит лога"""
    audit_log = AuditLog(
        user_id=sample_user.id,
        action="user_login",
        resource_type="user",
        resource_id=sample_user.id,
        details={"ip_address": "192.168.1.1"}
    )
    
    db_session.add(audit_log)
    db_session.commit()
    db_session.refresh(audit_log)
    
    assert audit_log.id is not None
    assert audit_log.user_id == sample_user.id
    assert audit_log.action == "user_login"
    assert audit_log.timestamp is not None

def test_user_settings_model(db_session: Session, sample_user):
    """Тест модели настроек пользователя"""
    settings = UserSettings(
        user_id=sample_user.id,
        theme="dark",
        language="en",
        notifications_enabled=True,
        timezone="UTC"
    )
    
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)
    
    assert settings.id is not None
    assert settings.user_id == sample_user.id
    assert settings.theme == "dark"
    assert settings.notifications_enabled is True

def test_metric_model(db_session: Session):
    """Тест модели метрики"""
    metric = Metric(
        name="task_completion_rate",
        value=0.85,
        unit="percentage",
        tags={"category": "productivity"}
    )
    
    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)
    
    assert metric.id is not None
    assert metric.name == "task_completion_rate"
    assert metric.value == 0.85
    assert metric.unit == "percentage"

def test_performance_metric_model(db_session: Session, sample_task):
    """Тест модели метрики производительности"""
    perf_metric = PerformanceMetric(
        task_id=sample_task.id,
        metric_name="execution_time",
        value=2.5,
        unit="hours",
        timestamp=datetime.now()
    )
    
    db_session.add(perf_metric)
    db_session.commit()
    db_session.refresh(perf_metric)
    
    assert perf_metric.id is not None
    assert perf_metric.task_id == sample_task.id
    assert perf_metric.metric_name == "execution_time"
    assert perf_metric.value == 2.5

def test_user_activity_log_model(db_session: Session, sample_user):
    """Тест модели лога активности пользователя"""
    activity_log = UserActivityLog(
        user_id=sample_user.id,
        activity_type="task_view",
        details={"task_id": 123, "duration": 30}
    )
    
    db_session.add(activity_log)
    db_session.commit()
    db_session.refresh(activity_log)
    
    assert activity_log.id is not None
    assert activity_log.user_id == sample_user.id
    assert activity_log.activity_type == "task_view"
    assert activity_log.timestamp is not None

def test_estimation_accuracy_history_model(db_session: Session, sample_task):
    """Тест модели истории точности оценок"""
    accuracy_history = EstimationAccuracyHistory(
        task_id=sample_task.id,
        estimated_hours=8.0,
        actual_hours=7.5,
        accuracy_percentage=93.75,
        feedback="Good estimation"
    )
    
    db_session.add(accuracy_history)
    db_session.commit()
    db_session.refresh(accuracy_history)
    
    assert accuracy_history.id is not None
    assert accuracy_history.task_id == sample_task.id
    assert accuracy_history.accuracy_percentage == 93.75

def test_notification_template_model(db_session: Session):
    """Тест модели шаблона уведомления"""
    template = NotificationTemplate(
        name="task_assigned",
        subject="New task assigned",
        body_template="You have been assigned to {task_title}",
        variables=["task_title"]
    )
    
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    
    assert template.id is not None
    assert template.name == "task_assigned"
    assert "task_title" in template.variables

def test_notification_model(db_session: Session, sample_user):
    """Тест модели уведомления"""
    notification = Notification(
        user_id=sample_user.id,
        title="Task assigned",
        message="You have been assigned to a new task",
        type="info",
        is_read=False
    )
    
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    
    assert notification.id is not None
    assert notification.user_id == sample_user.id
    assert notification.is_read is False
    assert notification.created_at is not None

def test_webhook_model(db_session: Session, sample_user):
    """Тест модели webhook"""
    webhook = Webhook(
        user_id=sample_user.id,
        url="https://example.com/webhook",
        events=["task_created", "task_updated"],
        is_active=True
    )
    
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    
    assert webhook.id is not None
    assert webhook.user_id == sample_user.id
    assert "task_created" in webhook.events
    assert webhook.is_active is True

def test_task_dependency_model(db_session: Session, sample_task):
    """Тест модели зависимости задач"""
    # Создаем зависимую задачу
    dependent_task = Task(
        title="Dependent Task",
        description="Task that depends on another",
        project_id=sample_task.project_id,
        status="blocked"
    )
    db_session.add(dependent_task)
    db_session.commit()
    
    dependency = TaskDependency(
        dependent_task_id=dependent_task.id,
        prerequisite_task_id=sample_task.id,
        dependency_type="finish_to_start"
    )
    
    db_session.add(dependency)
    db_session.commit()
    db_session.refresh(dependency)
    
    assert dependency.id is not None
    assert dependency.dependent_task_id == dependent_task.id
    assert dependency.prerequisite_task_id == sample_task.id

def test_time_entry_model(db_session: Session, sample_user, sample_task):
    """Тест модели записи времени"""
    time_entry = TimeEntry(
        user_id=sample_user.id,
        task_id=sample_task.id,
        hours_spent=4.5,
        description="Development work",
        date=datetime.now().date()
    )
    
    db_session.add(time_entry)
    db_session.commit()
    db_session.refresh(time_entry)
    
    assert time_entry.id is not None
    assert time_entry.user_id == sample_user.id
    assert time_entry.task_id == sample_task.id
    assert time_entry.hours_spent == 4.5

def test_model_relationships(db_session: Session, sample_user, sample_project, sample_task):
    """Тест связей между моделями"""
    # Проверяем связь пользователь -> проекты
    user_projects = db_session.query(Project).filter(Project.owner_id == sample_user.id).all()
    assert len(user_projects) >= 1
    assert sample_project in user_projects
    
    # Проверяем связь проект -> задачи
    project_tasks = db_session.query(Task).filter(Task.project_id == sample_project.id).all()
    assert len(project_tasks) >= 1
    assert sample_task in project_tasks
    
    # Проверяем связь задача -> проект
    assert sample_task.project_id == sample_project.id
    
    # Проверяем связь проект -> владелец
    assert sample_project.owner_id == sample_user.id

def test_model_validation(db_session: Session):
    """Тест валидации моделей"""
    # Тест на уникальность username
    user1 = User(username="duplicate", email="user1@example.com", full_name="User 1")
    user2 = User(username="duplicate", email="user2@example.com", full_name="User 2")
    
    db_session.add(user1)
    db_session.commit()
    
    with pytest.raises(Exception):  # Должна быть ошибка уникальности
        db_session.add(user2)
        db_session.commit()
    
    db_session.rollback()

def test_model_timestamps(db_session: Session):
    """Тест автоматических временных меток"""
    user = User(
        username="timestamptest",
        email="timestamp@example.com",
        full_name="Timestamp Test"
    )
    
    before_create = datetime.now()
    db_session.add(user)
    db_session.commit()
    after_create = datetime.now()
    
    assert user.created_at is not None
    assert user.updated_at is not None
    assert before_create <= user.created_at <= after_create
    assert before_create <= user.updated_at <= after_create
