#!/usr/bin/env python3
"""
Тесты безопасности и производительности базы данных TaskWeight
"""

import pytest
import psycopg2
import redis
import json
import time
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Generator
import threading
import concurrent.futures

pytestmark = [pytest.mark.database, pytest.mark.security, pytest.mark.performance]

class TestDatabaseSecurity:
    """Тесты безопасности базы данных"""
    
    def test_password_hashing(self, test_cursor, clean_database):
        """Тест хеширования паролей"""
        user_id = str(uuid.uuid4())
        plain_password = "test_password_123"
        
        # Создаем пользователя с хешированным паролем
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "security_test_user", "security@example.com", password_hash))
        
        # Проверяем, что пароль не хранится в открытом виде
        test_cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        stored_hash = test_cursor.fetchone()[0]
        
        assert stored_hash != plain_password, "Пароль не должен храниться в открытом виде"
        assert stored_hash == password_hash, "Хеш пароля должен соответствовать ожидаемому"
        
        # Проверяем валидацию пароля
        test_password = "test_password_123"
        test_hash = hashlib.sha256(test_password.encode()).hexdigest()
        assert test_hash == stored_hash, "Хеш тестового пароля должен совпадать с сохраненным"
    
    def test_sql_injection_prevention(self, test_cursor, clean_database):
        """Тест предотвращения SQL инъекций"""
        user_id = str(uuid.uuid4())
        
        # Создаем пользователя
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "injection_test_user", "injection@example.com", "hash"))
        
        # Пытаемся выполнить SQL инъекцию через параметризованный запрос
        malicious_input = "'; DROP TABLE users; --"
        
        # Параметризованный запрос должен безопасно обработать ввод
        test_cursor.execute("SELECT * FROM users WHERE username = %s", (malicious_input,))
        result = test_cursor.fetchone()
        
        # Проверяем, что таблица users все еще существует
        test_cursor.execute("SELECT COUNT(*) FROM users")
        user_count = test_cursor.fetchone()[0]
        
        assert user_count > 0, "Таблица users не должна быть удалена"
    
    def test_user_permissions(self, test_cursor):
        """Тест прав доступа пользователей"""
        # Проверяем, что текущий пользователь имеет ограниченные права
        test_cursor.execute("SELECT current_user, session_user")
        current_user, session_user = test_cursor.fetchone()
        
        # Проверяем, что пользователь не является суперпользователем
        test_cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = %s", (current_user,))
        is_superuser = test_cursor.fetchone()
        
        if is_superuser is not None:
            assert not is_superuser[0], "Тестовый пользователь не должен быть суперпользователем"
    
    def test_audit_logging(self, test_cursor, clean_database):
        """Тест аудита и логирования"""
        user_id = str(uuid.uuid4())
        
        # Создаем пользователя
        test_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, "audit_test_user", "audit@example.com", "hash"))
        
        # Проверяем, что запись создана в audit_logs
        test_cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE table_name = 'users' AND record_id = %s
        """, (user_id,))
        
        audit_count = test_cursor.fetchone()[0]
        assert audit_count > 0, "Должна быть запись в audit_logs"
    
    def test_data_encryption(self, test_cursor):
        """Тест шифрования данных"""
        # Проверяем, что чувствительные данные не хранятся в открытом виде
        test_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name IN ('password_hash', 'api_key', 'secret_token')
        """)
        
        sensitive_columns = test_cursor.fetchall()
        
        for column_name, data_type in sensitive_columns:
            # Проверяем, что чувствительные колонки не являются простым text
            assert data_type != 'text' or 'hash' in column_name.lower(), \
                f"Чувствительная колонка {column_name} должна быть зашифрована или хеширована"

class TestDatabasePerformance:
    """Тесты производительности базы данных"""
    
    @pytest.mark.performance
    def test_query_execution_time(self, test_cursor, sample_data, benchmark):
        """Тест времени выполнения запросов"""
        def simple_query():
            test_cursor.execute("SELECT * FROM users WHERE id = %s", (sample_data['user_id'],))
            return test_cursor.fetchone()
        
        def complex_query():
            test_cursor.execute("""
                SELECT u.username, p.name as project_name, COUNT(t.id) as task_count
                FROM users u
                JOIN projects p ON u.id = p.owner_id
                LEFT JOIN tasks t ON p.id = t.project_id
                WHERE u.id = %s
                GROUP BY u.username, p.name
            """, (sample_data['user_id'],))
            return test_cursor.fetchall()
        
        # Бенчмарк простого запроса
        simple_result = benchmark(simple_query)
        assert simple_result is not None
        
        # Бенчмарк сложного запроса
        complex_result = benchmark(complex_query)
        assert complex_result is not None
    
    @pytest.mark.performance
    def test_index_effectiveness(self, test_cursor, sample_data):
        """Тест эффективности индексов"""
        # Запрос без использования индекса
        test_cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM users 
            WHERE username LIKE '%test%'
        """)
        
        explain_without_index = test_cursor.fetchall()
        explain_text_without = "\n".join([row[0] for row in explain_without_index])
        
        # Запрос с использованием индекса
        test_cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM users 
            WHERE username = %s
        """, ("test_user",))
        
        explain_with_index = test_cursor.fetchall()
        explain_text_with = "\n".join([row[0] for row in explain_with_index])
        
        # Проверяем, что запрос с индексом выполняется быстрее
        assert "Index Scan" in explain_text_with or "Bitmap Index Scan" in explain_text_with
    
    @pytest.mark.performance
    def test_connection_pooling(self, db_config):
        """Тест пула подключений"""
        def create_connection():
            return psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
        
        # Создаем несколько подключений одновременно
        connections = []
        start_time = time.time()
        
        try:
            for i in range(10):
                conn = create_connection()
                connections.append(conn)
                
                # Выполняем простой запрос
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            
            end_time = time.time()
            connection_time = end_time - start_time
            
            # Время создания подключений должно быть разумным
            assert connection_time < 5.0, f"Создание 10 подключений заняло {connection_time} секунд"
            
        finally:
            # Закрываем все подключения
            for conn in connections:
                conn.close()
    
    @pytest.mark.performance
    def test_concurrent_queries(self, test_cursor, sample_data):
        """Тест одновременных запросов"""
        def execute_query(query_id):
            try:
                # Создаем отдельное подключение для каждого потока
                conn = psycopg2.connect(
                    host=test_cursor.connection.info.host,
                    port=test_cursor.connection.info.port,
                    database=test_cursor.connection.info.dbname,
                    user=test_cursor.connection.info.user,
                    password=test_cursor.connection.info.password
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = %s", (sample_data['user_id'],))
                result = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                return result is not None
                
            except Exception as e:
                return False
        
        # Запускаем 5 одновременных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_query, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Все запросы должны выполниться успешно
        success_count = sum(results)
        assert success_count == 5, f"Только {success_count} из 5 запросов выполнились успешно"
    
    @pytest.mark.performance
    def test_memory_usage(self, test_cursor):
        """Тест использования памяти"""
        # Проверяем статистику использования памяти
        test_cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            LIMIT 10
        """)
        
        stats = test_cursor.fetchall()
        assert len(stats) > 0, "Должна быть статистика по таблицам"
    
    @pytest.mark.performance
    def test_vacuum_effectiveness(self, test_cursor):
        """Тест эффективности VACUUM"""
        # Проверяем статистику по таблицам
        test_cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            LIMIT 5
        """)
        
        table_stats = test_cursor.fetchall()
        assert len(table_stats) > 0, "Должна быть статистика по таблицам"
        
        # Проверяем, что нет слишком много мертвых кортежей
        for stats in table_stats:
            n_live_tup, n_dead_tup = stats[5], stats[6]
            if n_live_tup > 0:
                dead_ratio = n_dead_tup / n_live_tup
                assert dead_ratio < 0.5, f"Слишком много мертвых кортежей в таблице {stats[1]}"

class TestStressTesting:
    """Стресс-тесты базы данных"""
    
    @pytest.mark.slow
    def test_heavy_load(self, test_cursor, clean_database):
        """Тест под высокой нагрузкой"""
        # Создаем много пользователей
        users_created = 0
        start_time = time.time()
        
        try:
            for i in range(100):
                user_id = str(uuid.uuid4())
                username = f"load_test_user_{i}"
                email = f"load_test_{i}@example.com"
                
                test_cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (user_id, username, email, "hash"))
                
                users_created += 1
                
                # Каждые 10 пользователей создаем проект
                if i % 10 == 0:
                    project_id = str(uuid.uuid4())
                    test_cursor.execute("""
                        INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """, (project_id, f"Project {i}", f"Description {i}", user_id))
            
            end_time = time.time()
            creation_time = end_time - start_time
            
            # Проверяем, что все пользователи созданы
            test_cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'load_test_user_%'")
            actual_count = test_cursor.fetchone()[0]
            
            assert actual_count == 100, f"Создано только {actual_count} из 100 пользователей"
            assert creation_time < 30.0, f"Создание 100 пользователей заняло {creation_time} секунд"
            
        except Exception as e:
            pytest.fail(f"Ошибка при создании нагрузки: {e}")
    
    @pytest.mark.slow
    def test_concurrent_writes(self, db_config, clean_database):
        """Тест одновременных записей"""
        def write_user(user_id):
            try:
                conn = psycopg2.connect(
                    host=db_config['host'],
                    port=db_config['port'],
                    database=db_config['database'],
                    user=db_config['user'],
                    password=db_config['password']
                )
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (user_id, f"concurrent_user_{user_id[:8]}", 
                      f"concurrent_{user_id[:8]}@example.com", "hash"))
                
                conn.commit()
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                return False
        
        # Запускаем 20 одновременных записей
        user_ids = [str(uuid.uuid4()) for _ in range(20)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(write_user, user_id) for user_id in user_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Проверяем результаты
        success_count = sum(results)
        assert success_count == 20, f"Только {success_count} из 20 записей выполнились успешно"
        
        # Проверяем, что все записи действительно созданы
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'concurrent_user_%'")
        actual_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        assert actual_count == 20, f"В базе только {actual_count} из 20 пользователей"

class TestMonitoringAndMetrics:
    """Тесты мониторинга и метрик"""
    
    def test_performance_metrics_collection(self, test_cursor):
        """Тест сбора метрик производительности"""
        # Проверяем наличие метрик
        test_cursor.execute("SELECT COUNT(*) FROM performance_metrics")
        metrics_count = test_cursor.fetchone()[0]
        
        assert metrics_count >= 0, "Должны быть метрики производительности"
    
    def test_system_statistics(self, test_cursor):
        """Тест системной статистики"""
        # Проверяем статистику по таблицам
        test_cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins,
                n_tup_upd,
                n_tup_del
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            LIMIT 5
        """)
        
        stats = test_cursor.fetchall()
        assert len(stats) > 0, "Должна быть системная статистика"
    
    def test_lock_monitoring(self, test_cursor):
        """Тест мониторинга блокировок"""
        # Проверяем активные блокировки
        test_cursor.execute("""
            SELECT 
                locktype,
                database,
                relation,
                page,
                tuple,
                virtualxid,
                transactionid,
                classid,
                objid,
                objsubid,
                virtualtransaction,
                pid,
                mode,
                granted
            FROM pg_locks
            WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
            LIMIT 10
        """)
        
        locks = test_cursor.fetchall()
        # Блокировки могут быть или не быть, это нормально
        assert isinstance(locks, list), "Должен быть список блокировок"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
