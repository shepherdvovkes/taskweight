"""
Pytest configuration and fixtures for TaskWeight server tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
import os
import sys

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.db.database import get_db, Base
from app.db.models import User, Project, Task, TaskCategory, EstimationResult
from app.logic.ai_estimator import AIEstimator

# Тестовая конфигурация базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Тестовая конфигурация Redis
TEST_REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6381,  # Другой порт для тестов
    'db': 1,
    'decode_responses': True
}

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def db_engine():
    """Создание тестового движка базы данных"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Создание тестовой сессии базы данных"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Создание тестового клиента FastAPI"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def redis_client():
    """Создание тестового клиента Redis"""
    try:
        client = redis.Redis(**TEST_REDIS_CONFIG)
        client.ping()
        yield client
        # Очистка тестовой базы Redis
        client.flushdb()
        client.close()
    except redis.ConnectionError:
        pytest.skip("Redis недоступен для тестов")

@pytest.fixture
def sample_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_project(db_session, sample_user):
    """Создание тестового проекта"""
    project = Project(
        name="Test Project",
        description="Test project description",
        owner_id=sample_user.id,
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture
def sample_task(db_session, sample_project):
    """Создание тестовой задачи"""
    task = Task(
        title="Test Task",
        description="Test task description",
        project_id=sample_project.id,
        status="todo",
        priority="medium"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task

@pytest.fixture
def sample_category(db_session):
    """Создание тестовой категории задач"""
    category = TaskCategory(
        name="Test Category",
        description="Test category description"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture
def ai_estimator():
    """Создание экземпляра AIEstimator для тестов"""
    return AIEstimator()
