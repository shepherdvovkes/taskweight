#!/usr/bin/env python3
"""
Тесты миграций и схемы базы данных TaskWeight
"""

import pytest
import psycopg2
import json
import os
from typing import Dict, List, Any, Generator

pytestmark = pytest.mark.database

class TestDatabaseMigrations:
    """Тесты миграций базы данных"""
    
    def test_migration_files_exist(self):
        """Тест наличия файлов миграций"""
        migration_dir = "postgres/init"
        required_migrations = [
            "01-init-database.sql",
            "02-migrations.sql", 
            "03-sample-data.sql",
            "04-views.sql",
            "05-functions.sql",
            "06-webhooks.sql",
            "07-metrics.sql",
            "08-notifications.sql",
            "09-sample-data-extended.sql"
        ]
        
        for migration in required_migrations:
            migration_path = os.path.join(migration_dir, migration)
            assert os.path.exists(migration_path), f"Файл миграции {migration} отсутствует"
    
    def test_migration_sql_syntax(self, test_cursor):
        """Тест синтаксиса SQL в миграциях"""
        # Проверяем, что все представления созданы корректно
        test_cursor.execute("""
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = 'public'
        """)
        
        views = [row[0] for row in test_cursor.fetchall()]
        expected_views = [
            'user_project_summary',
            'task_estimation_summary',
            'project_performance_metrics',
            'user_activity_summary'
        ]
        
        for view in expected_views:
            assert view in views, f"Представление {view} не создано"
    
    def test_function_signatures(self, test_cursor):
        """Тест сигнатур функций"""
        test_cursor.execute("""
            SELECT proname, proargtypes::regtype[]
            FROM pg_proc 
            WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            ORDER BY proname
        """)
        
        functions = test_cursor.fetchall()
        function_names = [func[0] for func in functions]
        
        # Проверяем наличие ключевых функций
        expected_functions = [
            'calculate_task_complexity',
            'update_project_metrics',
            'log_user_activity'
        ]
        
        for func in expected_functions:
            assert func in function_names, f"Функция {func} не найдена"

class TestSchemaConstraints:
    """Тесты ограничений схемы"""
    
    def test_primary_keys(self, test_cursor):
        """Тест первичных ключей"""
        tables_with_pk = [
            'users', 'projects', 'tasks', 'task_categories',
            'estimation_results', 'integrations', 'audit_logs'
        ]
        
        for table in tables_with_pk:
            test_cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE table_name = %s 
                AND constraint_type = 'PRIMARY KEY'
            """, (table,))
            
            pk_count = test_cursor.fetchone()[0]
            assert pk_count > 0, f"Таблица {table} не имеет первичного ключа"
    
    def test_foreign_key_relationships(self, test_cursor):
        """Тест связей внешних ключей"""
        expected_fk_relationships = [
            ('tasks', 'project_id', 'projects', 'id'),
            ('tasks', 'category_id', 'task_categories', 'id'),
            ('tasks', 'assignee_id', 'users', 'id'),
            ('projects', 'owner_id', 'users', 'id'),
            ('task_categories', 'project_id', 'projects', 'id')
        ]
        
        for table, fk_column, ref_table, ref_column in expected_fk_relationships:
            test_cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = %s 
                AND kcu.column_name = %s
                AND ccu.table_name = %s
                AND ccu.column_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
            """, (table, fk_column, ref_table, ref_column))
            
            fk_count = test_cursor.fetchone()[0]
            assert fk_count > 0, f"Отсутствует внешний ключ {table}.{fk_column} -> {ref_table}.{ref_column}"
    
    def test_check_constraints(self, test_cursor):
        """Тест проверочных ограничений"""
        # Проверяем ограничения на статус задач
        test_cursor.execute("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
            AND constraint_name LIKE '%task%'
        """)
        
        check_constraints = test_cursor.fetchall()
        assert len(check_constraints) > 0, "Должны быть проверочные ограничения для задач"
    
    def test_unique_constraints(self, test_cursor):
        """Тест уникальных ограничений"""
        # Проверяем уникальность username и email
        test_cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE table_name = 'users' 
            AND constraint_type = 'UNIQUE'
        """)
        
        unique_count = test_cursor.fetchone()[0]
        assert unique_count >= 2, "Должны быть уникальные ограничения на username и email"

class TestIndexes:
    """Тесты индексов"""
    
    def test_required_indexes(self, test_cursor):
        """Тест наличия необходимых индексов"""
        expected_indexes = [
            ('users', 'username'),
            ('users', 'email'),
            ('tasks', 'project_id'),
            ('tasks', 'assignee_id'),
            ('tasks', 'status'),
            ('projects', 'owner_id')
        ]
        
        for table, column in expected_indexes:
            test_cursor.execute(f"""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = %s 
                AND indexdef LIKE %s
            """, (table, f'%{column}%'))
            
            index_count = test_cursor.fetchone()[0]
            assert index_count > 0, f"Отсутствует индекс для {table}.{column}"
    
    def test_index_types(self, test_cursor):
        """Тест типов индексов"""
        # Проверяем наличие GIN индексов для полнотекстового поиска
        test_cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE indexdef LIKE '%GIN%'
        """)
        
        gin_index_count = test_cursor.fetchone()[0]
        assert gin_index_count > 0, "Должны быть GIN индексы для полнотекстового поиска"
    
    def test_partial_indexes(self, test_cursor):
        """Тест частичных индексов"""
        # Проверяем частичные индексы для активных записей
        test_cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE indexdef LIKE '%WHERE%'
        """)
        
        partial_index_count = test_cursor.fetchone()[0]
        assert partial_index_count > 0, "Должны быть частичные индексы"

class TestViews:
    """Тесты представлений"""
    
    def test_view_definitions(self, test_cursor):
        """Тест определений представлений"""
        test_cursor.execute("""
            SELECT viewname, definition 
            FROM pg_views 
            WHERE schemaname = 'public'
        """)
        
        views = test_cursor.fetchall()
        assert len(views) > 0, "Должны быть представления в базе данных"
        
        for view_name, definition in views:
            assert definition is not None, f"Представление {view_name} не имеет определения"
            assert len(definition) > 0, f"Представление {view_name} имеет пустое определение"
    
    def test_view_data_access(self, test_cursor, sample_data):
        """Тест доступа к данным через представления"""
        # Проверяем представление user_project_summary
        test_cursor.execute("""
            SELECT * FROM user_project_summary 
            WHERE user_id = %s
        """, (sample_data['user_id'],))
        
        result = test_cursor.fetchone()
        assert result is not None, "Представление user_project_summary должно возвращать данные"
    
    def test_view_performance(self, test_cursor, sample_data):
        """Тест производительности представлений"""
        # Проверяем план выполнения для представления
        test_cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM user_project_summary 
            WHERE user_id = %s
        """, (sample_data['user_id'],))
        
        explain_result = test_cursor.fetchall()
        explain_text = "\n".join([row[0] for row in explain_result])
        
        # Проверяем, что запрос выполняется эффективно
        assert "Seq Scan" not in explain_text or "Index Scan" in explain_text

class TestTriggers:
    """Тесты триггеров"""
    
    def test_trigger_existence(self, test_cursor):
        """Тест наличия триггеров"""
        test_cursor.execute("""
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        
        triggers = test_cursor.fetchall()
        assert len(triggers) > 0, "Должны быть триггеры в базе данных"
        
        # Проверяем наличие ключевых триггеров
        trigger_names = [t[0] for t in triggers]
        expected_triggers = [
            'update_updated_at',
            'log_audit_changes'
        ]
        
        for trigger in expected_triggers:
            assert any(trigger in name for name in trigger_names), f"Триггер {trigger} не найден"
    
    def test_trigger_functionality(self, test_cursor, clean_database):
        """Тест функциональности триггеров"""
        # Создаем тестового пользователя
        user_id = str(uuid.uuid4())
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "trigger_test_user", "trigger@example.com", "hash"))
        
        # Получаем время создания
        test_cursor.execute("SELECT created_at, updated_at FROM users WHERE id = %s", (user_id,))
        created_time, updated_time = test_cursor.fetchone()
        
        # Обновляем пользователя
        test_cursor.execute("""
            UPDATE users 
            SET username = 'updated_username' 
            WHERE id = %s
        """, (user_id,))
        
        # Проверяем, что updated_at обновился
        test_cursor.execute("SELECT updated_at FROM users WHERE id = %s", (user_id,))
        new_updated_time = test_cursor.fetchone()[0]
        
        assert new_updated_time > updated_time, "Триггер должен обновлять updated_at"

class TestDataTypes:
    """Тесты типов данных"""
    
    def test_uuid_columns(self, test_cursor):
        """Тест колонок с UUID"""
        test_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND data_type = 'uuid'
        """)
        
        uuid_columns = test_cursor.fetchall()
        expected_uuid_columns = ['id', 'user_id', 'project_id', 'task_id']
        
        for expected_col in expected_uuid_columns:
            assert any(expected_col in col[0] for col in uuid_columns), f"Колонка {expected_col} должна быть UUID"
    
    def test_timestamp_columns(self, test_cursor):
        """Тест колонок с временными метками"""
        test_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND data_type IN ('timestamp without time zone', 'timestamp with time zone')
        """)
        
        timestamp_columns = test_cursor.fetchall()
        expected_timestamp_columns = ['created_at', 'updated_at']
        
        for expected_col in expected_timestamp_columns:
            assert any(expected_col in col[0] for col in timestamp_columns), f"Колонка {expected_col} должна быть timestamp"
    
    def test_text_columns(self, test_cursor):
        """Тест текстовых колонок"""
        test_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND data_type IN ('text', 'character varying')
        """)
        
        text_columns = test_cursor.fetchall()
        assert len(text_columns) > 0, "Должны быть текстовые колонки"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
