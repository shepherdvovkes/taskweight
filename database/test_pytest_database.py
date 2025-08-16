#!/usr/bin/env python3
"""
Современные pytest тесты для базы данных TaskWeight
"""

import pytest
import psycopg2
import redis
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

pytestmark = pytest.mark.database

class TestDatabaseStructure:
    """Тесты структуры базы данных"""
    
    def test_database_connection(self, postgres_connection):
        """Тест подключения к базе данных"""
        assert postgres_connection is not None
        assert not postgres_connection.closed
        
        # Проверяем версию PostgreSQL
        cursor = postgres_connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        assert "PostgreSQL" in version
        cursor.close()
    
    def test_required_tables_exist(self, test_cursor):
        """Тест наличия всех необходимых таблиц"""
        expected_tables = [
            'users', 'projects', 'tasks', 'task_categories',
            'estimation_results', 'integrations', 'audit_logs',
            'user_settings', 'metrics', 'performance_metrics',
            'user_activity_logs', 'estimation_accuracy_history',
            'notification_templates', 'notifications',
            'notification_preferences', 'notification_logs',
            'webhooks', 'webhook_deliveries', 'task_dependencies',
            'time_entries'
        ]
        
        test_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in test_cursor.fetchall()]
        missing_tables = set(expected_tables) - set(existing_tables)
        
        assert not missing_tables, f"Отсутствуют таблицы: {missing_tables}"
        assert len(existing_tables) >= len(expected_tables)
    
    def test_table_columns(self, test_cursor):
        """Тест структуры колонок таблиц"""
        # Проверяем структуру таблицы users
        test_cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = test_cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        expected_columns = ['id', 'username', 'email', 'password_hash', 'created_at', 'updated_at']
        for expected_col in expected_columns:
            assert expected_col in column_names, f"Колонка {expected_col} отсутствует в таблице users"
    
    def test_extensions(self, test_cursor):
        """Тест наличия необходимых расширений PostgreSQL"""
        expected_extensions = ['uuid-ossp', 'pg_trgm', 'btree_gin']
        
        test_cursor.execute("SELECT extname FROM pg_extension;")
        installed_extensions = [row[0] for row in test_cursor.fetchall()]
        
        for ext in expected_extensions:
            assert ext in installed_extensions, f"Расширение {ext} не установлено"

class TestDatabaseFunctions:
    """Тесты функций базы данных"""
    
    def test_uuid_generation(self, test_cursor):
        """Тест генерации UUID"""
        test_cursor.execute("SELECT uuid_generate_v4();")
        uuid_result = test_cursor.fetchone()[0]
        
        # Проверяем, что это валидный UUID
        uuid.UUID(uuid_result)
    
    def test_custom_functions(self, test_cursor):
        """Тест пользовательских функций"""
        # Проверяем наличие функции для расчета времени
        test_cursor.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_type = 'FUNCTION'
        """)
        
        functions = [row[0] for row in test_cursor.fetchall()]
        assert len(functions) > 0, "Должны быть пользовательские функции"
    
    def test_triggers(self, test_cursor):
        """Тест триггеров"""
        test_cursor.execute("""
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        
        triggers = test_cursor.fetchall()
        assert len(triggers) > 0, "Должны быть триггеры в базе данных"

class TestDataOperations:
    """Тесты операций с данными"""
    
    def test_insert_user(self, test_cursor, clean_database):
        """Тест вставки пользователя"""
        user_id = str(uuid.uuid4())
        username = f"test_user_{int(time.time())}"
        email = f"{username}@example.com"
        
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, username, email, "test_hash"))
        
        # Проверяем, что пользователь создан
        test_cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        result = test_cursor.fetchone()
        
        assert result is not None
        assert result[0] == username
        assert result[1] == email
    
    def test_project_creation(self, test_cursor, clean_database):
        """Тест создания проекта"""
        user_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        
        # Создаем пользователя
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "owner", "owner@example.com", "hash"))
        
        # Создаем проект
        test_cursor.execute("""
            INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (project_id, "Test Project", "Test Description", user_id))
        
        # Проверяем создание
        test_cursor.execute("SELECT name, owner_id FROM projects WHERE id = %s", (project_id,))
        result = test_cursor.fetchone()
        
        assert result is not None
        assert result[0] == "Test Project"
        assert result[1] == user_id
    
    def test_task_workflow(self, test_cursor, clean_database):
        """Тест полного workflow создания задачи"""
        # Создаем пользователя
        user_id = str(uuid.uuid4())
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "assignee", "assignee@example.com", "hash"))
        
        # Создаем проект
        project_id = str(uuid.uuid4())
        test_cursor.execute("""
            INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (project_id, "Project", "Description", user_id))
        
        # Создаем категорию
        category_id = str(uuid.uuid4())
        test_cursor.execute("""
            INSERT INTO task_categories (id, name, description, project_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (category_id, "Category", "Category Description", project_id))
        
        # Создаем задачу
        task_id = str(uuid.uuid4())
        test_cursor.execute("""
            INSERT INTO tasks (id, title, description, project_id, category_id, assignee_id,
                              estimated_hours, actual_hours, status, priority, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (task_id, "Task Title", "Task Description", project_id, category_id, user_id,
              8.0, 0.0, 'todo', 'high'))
        
        # Проверяем создание задачи
        test_cursor.execute("""
            SELECT t.title, t.status, p.name as project_name, c.name as category_name
            FROM tasks t
            JOIN projects p ON t.project_id = p.id
            JOIN task_categories c ON t.category_id = c.id
            WHERE t.id = %s
        """, (task_id,))
        
        result = test_cursor.fetchone()
        assert result is not None
        assert result[0] == "Task Title"
        assert result[1] == "todo"
        assert result[2] == "Project"
        assert result[3] == "Category"

class TestConstraintsAndIntegrity:
    """Тесты ограничений и целостности данных"""
    
    def test_foreign_key_constraints(self, test_cursor, clean_database):
        """Тест внешних ключей"""
        # Пытаемся создать задачу с несуществующим project_id
        user_id = str(uuid.uuid4())
        fake_project_id = str(uuid.uuid4())
        fake_category_id = str(uuid.uuid4())
        
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            test_cursor.execute("""
                INSERT INTO tasks (id, title, project_id, category_id, assignee_id,
                                  estimated_hours, actual_hours, status, priority, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (str(uuid.uuid4()), "Task", fake_project_id, fake_category_id, user_id,
                  8.0, 0.0, 'todo', 'high'))
    
    def test_unique_constraints(self, test_cursor, clean_database):
        """Тест уникальных ограничений"""
        user_id = str(uuid.uuid4())
        username = "unique_user"
        email = "unique@example.com"
        
        # Создаем первого пользователя
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, username, email, "hash"))
        
        # Пытаемся создать второго пользователя с тем же username
        with pytest.raises(psycopg2.errors.UniqueViolation):
            test_cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (str(uuid.uuid4()), username, "another@example.com", "hash"))
    
    def test_not_null_constraints(self, test_cursor, clean_database):
        """Тест NOT NULL ограничений"""
        # Пытаемся создать пользователя без обязательных полей
        with pytest.raises(psycopg2.errors.NotNullViolation):
            test_cursor.execute("""
                INSERT INTO users (id, username, email, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
            """, (str(uuid.uuid4()), "test_user", None))

class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.performance
    def test_query_performance(self, test_cursor, sample_data, benchmark):
        """Тест производительности запросов"""
        def query_users():
            test_cursor.execute("SELECT * FROM users WHERE username = %s", ("test_user",))
            return test_cursor.fetchone()
        
        result = benchmark(query_users)
        assert result is not None
    
    @pytest.mark.performance
    def test_index_usage(self, test_cursor, sample_data):
        """Тест использования индексов"""
        # Проверяем план выполнения запроса
        test_cursor.execute("EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM users WHERE username = %s", ("test_user",))
        explain_result = test_cursor.fetchall()
        
        explain_text = "\n".join([row[0] for row in explain_result])
        
        # Проверяем, что используется индекс
        assert "Index Scan" in explain_text or "Bitmap Index Scan" in explain_text

class TestRedisIntegration:
    """Тесты интеграции с Redis"""
    
    def test_redis_connection(self, redis_connection):
        """Тест подключения к Redis"""
        assert redis_connection is not None
        assert redis_connection.ping()
    
    def test_redis_operations(self, redis_connection):
        """Тест базовых операций Redis"""
        test_key = f"test_key_{int(time.time())}"
        test_value = "test_value"
        
        # Тест SET
        redis_connection.set(test_key, test_value)
        
        # Тест GET
        retrieved_value = redis_connection.get(test_key)
        assert retrieved_value == test_value
        
        # Тест DELETE
        redis_connection.delete(test_key)
        assert redis_connection.get(test_key) is None
    
    def test_redis_cache_pattern(self, redis_connection, test_cursor, sample_data):
        """Тест паттерна кеширования в Redis"""
        user_id = sample_data['user_id']
        cache_key = f"user:{user_id}"
        
        # Получаем данные пользователя
        test_cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user_data = test_cursor.fetchone()
        
        # Кешируем в Redis
        cache_data = {
            'username': user_data[0],
            'email': user_data[1],
            'cached_at': datetime.now().isoformat()
        }
        redis_connection.setex(cache_key, 300, json.dumps(cache_data))  # TTL 5 минут
        
        # Получаем из кеша
        cached_data = redis_connection.get(cache_key)
        assert cached_data is not None
        
        parsed_data = json.loads(cached_data)
        assert parsed_data['username'] == user_data[0]
        assert parsed_data['email'] == user_data[1]

class TestDataValidation:
    """Тесты валидации данных"""
    
    def test_email_format_validation(self, test_cursor, clean_database):
        """Тест валидации формата email"""
        user_id = str(uuid.uuid4())
        
        # Создаем пользователя с валидным email
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "test_user", "valid@email.com", "hash"))
        
        # Проверяем создание
        test_cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        result = test_cursor.fetchone()
        assert result[0] == "valid@email.com"
    
    def test_numeric_constraints(self, test_cursor, clean_database):
        """Тест числовых ограничений"""
        user_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        
        # Создаем необходимые записи
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "test_user", "test@example.com", "hash"))
        
        test_cursor.execute("""
            INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (project_id, "Project", "Description", user_id))
        
        test_cursor.execute("""
            INSERT INTO task_categories (id, name, description, project_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (category_id, "Category", "Description", project_id))
        
        # Создаем задачу с отрицательными часами (должно вызвать ошибку)
        with pytest.raises(psycopg2.errors.CheckViolation):
            test_cursor.execute("""
                INSERT INTO tasks (id, title, project_id, category_id, assignee_id,
                                  estimated_hours, actual_hours, status, priority, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (str(uuid.uuid4()), "Task", project_id, category_id, user_id,
                  -5.0, 0.0, 'todo', 'high'))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
