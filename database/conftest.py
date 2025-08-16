#!/usr/bin/env python3
"""
Pytest fixtures для тестирования базы данных TaskWeight
"""

import pytest
import psycopg2
import redis
import os
import tempfile
import shutil
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

# Конфигурация тестовой базы данных
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': os.getenv('TEST_DB_PORT', '5433'),
    'database': os.getenv('TEST_DB_NAME', 'taskweight_test'),
    'user': os.getenv('TEST_DB_USER', 'taskweight_user'),
    'password': os.getenv('TEST_DB_PASSWORD', 'taskweight_password'),
    'redis_host': os.getenv('TEST_REDIS_HOST', 'localhost'),
    'redis_port': int(os.getenv('TEST_REDIS_PORT', '6380')),
    'redis_password': os.getenv('TEST_REDIS_PASSWORD', 'taskweight_redis_password')
}

@pytest.fixture(scope="session")
def db_config() -> Dict[str, Any]:
    """Конфигурация тестовой базы данных"""
    return TEST_DB_CONFIG.copy()

@pytest.fixture(scope="session")
def postgres_connection(db_config) -> Generator[psycopg2.extensions.connection, None, None]:
    """Подключение к PostgreSQL для тестов"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.autocommit = True
        yield conn
    finally:
        if conn:
            conn.close()

@pytest.fixture(scope="session")
def redis_connection(db_config) -> Generator[redis.Redis, None, None]:
    """Подключение к Redis для тестов"""
    conn = None
    try:
        conn = redis.Redis(
            host=db_config['redis_host'],
            port=db_config['redis_port'],
            password=db_config['redis_password'],
            decode_responses=True
        )
        # Проверяем подключение
        conn.ping()
        yield conn
    finally:
        if conn:
            conn.close()

@pytest.fixture(scope="function")
def test_cursor(postgres_connection) -> Generator[psycopg2.extensions.cursor, None, None]:
    """Курсор для выполнения SQL запросов в тестах"""
    cursor = postgres_connection.cursor()
    yield cursor
    cursor.close()

@pytest.fixture(scope="function")
def clean_database(postgres_connection, test_cursor):
    """Очистка базы данных перед каждым тестом"""
    # Список таблиц для очистки (в порядке зависимостей)
    tables_to_clean = [
        'webhook_deliveries', 'webhooks', 'notifications', 'notification_logs',
        'notification_preferences', 'notification_templates', 'time_entries',
        'task_dependencies', 'estimation_accuracy_history', 'performance_metrics',
        'user_activity_logs', 'metrics', 'estimation_results', 'tasks',
        'task_categories', 'projects', 'user_settings', 'integrations',
        'audit_logs', 'users'
    ]
    
    # Отключаем проверку внешних ключей
    test_cursor.execute("SET session_replication_role = replica;")
    
    # Очищаем таблицы
    for table in tables_to_clean:
        try:
            test_cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
        except Exception:
            pass  # Игнорируем ошибки, если таблица не существует
    
    # Включаем обратно проверку внешних ключей
    test_cursor.execute("SET session_replication_role = DEFAULT;")
    
    yield
    
    # Дополнительная очистка после теста
    test_cursor.execute("SET session_replication_role = replica;")
    for table in tables_to_clean:
        try:
            test_cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
        except Exception:
            pass
    test_cursor.execute("SET session_replication_role = DEFAULT;")

@pytest.fixture(scope="function")
def sample_data(postgres_connection, test_cursor, clean_database):
    """Создание тестовых данных для тестов"""
    # Создаем тестового пользователя
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    test_cursor.execute("""
        INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (user_id, "test_user", "test@example.com", "test_hash"))
    
    # Создаем тестовый проект
    project_id = "550e8400-e29b-41d4-a716-446655440001"
    test_cursor.execute("""
        INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (project_id, "Test Project", "Test Description", user_id))
    
    # Создаем тестовую категорию задач
    category_id = "550e8400-e29b-41d4-a716-446655440002"
    test_cursor.execute("""
        INSERT INTO task_categories (id, name, description, project_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    """, (category_id, "Test Category", "Test Category Description", project_id))
    
    # Создаем тестовую задачу
    task_id = "550e8400-e29b-41d4-a716-446655440003"
    test_cursor.execute("""
        INSERT INTO tasks (id, title, description, project_id, category_id, assignee_id, 
                          estimated_hours, actual_hours, status, priority, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
    """, (task_id, "Test Task", "Test Task Description", project_id, category_id, user_id,
          8.0, 0.0, 'in_progress', 'medium'))
    
    yield {
        'user_id': user_id,
        'project_id': project_id,
        'category_id': category_id,
        'task_id': task_id
    }

@pytest.fixture(scope="function")
def mock_redis():
    """Мок Redis для тестов без реального подключения"""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 0
        mock_redis_class.return_value = mock_redis
        yield mock_redis

@pytest.fixture(scope="function")
def temp_dir():
    """Временная директория для тестов"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def benchmark_config():
    """Конфигурация для бенчмарк тестов"""
    return {
        'min_rounds': 10,
        'max_time': 1.0,
        'warmup': True,
        'warmup_iterations': 3
    }
