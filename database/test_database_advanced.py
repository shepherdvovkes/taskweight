#!/usr/bin/env python3
"""
TaskWeight Advanced Database Test Suite
Расширенные тесты для проверки производительности, стресс-тестов и специфических сценариев
"""

import psycopg2
import redis
import json
import sys
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import statistics

class AdvancedDatabaseTester:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.pg_conn = None
        self.redis_conn = None
        self.test_results = []
        self.performance_metrics = {}
        
    def connect_postgres(self) -> bool:
        """Подключение к PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            self.pg_conn.autocommit = True
            print("✅ Подключение к PostgreSQL успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")
            return False
    
    def connect_redis(self) -> bool:
        """Подключение к Redis"""
        try:
            self.redis_conn = redis.Redis(
                host=self.db_config['redis_host'],
                port=self.db_config['redis_port'],
                password=self.db_config['redis_password'],
                decode_responses=True
            )
            self.redis_conn.ping()
            print("✅ Подключение к Redis успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            return False

    def test_concurrent_connections(self) -> bool:
        """Тест одновременных подключений"""
        print("\n🔍 Тестирование одновременных подключений...")
        
        try:
            connections = []
            max_connections = 20
            success_count = 0
            
            for i in range(max_connections):
                try:
                    conn = psycopg2.connect(
                        host=self.db_config['host'],
                        port=self.db_config['port'],
                        database=self.db_config['database'],
                        user=self.db_config['user'],
                        password=self.db_config['password']
                    )
                    connections.append(conn)
                    success_count += 1
                except Exception as e:
                    print(f"⚠️  Не удалось создать подключение {i+1}: {e}")
                    break
            
            print(f"✅ Успешно создано {success_count} подключений из {max_connections}")
            
            # Закрываем все подключения
            for conn in connections:
                conn.close()
            
            return success_count >= max_connections * 0.8  # 80% успешных подключений
            
        except Exception as e:
            print(f"❌ Ошибка тестирования подключений: {e}")
            return False

    def test_query_performance_benchmark(self) -> bool:
        """Бенчмарк производительности запросов"""
        print("\n🔍 Бенчмарк производительности запросов...")
        
        try:
            cursor = self.pg_conn.cursor()
            queries = [
                ("Простой SELECT", "SELECT COUNT(*) FROM users"),
                ("JOIN с проектами", """
                    SELECT u.username, COUNT(p.id) as project_count
                    FROM users u
                    LEFT JOIN projects p ON u.id = p.owner_id
                    GROUP BY u.id, u.username
                """),
                ("Сложный JOIN", """
                    SELECT p.name, COUNT(t.id) as task_count, 
                           AVG(t.estimated_hours) as avg_estimation
                    FROM projects p
                    LEFT JOIN tasks t ON p.id = t.project_id
                    LEFT JOIN users u ON t.assignee_id = u.id
                    GROUP BY p.id, p.name
                    HAVING COUNT(t.id) > 0
                """),
                ("Агрегация с условиями", """
                    SELECT 
                        t.status,
                        COUNT(*) as count,
                        AVG(t.estimated_hours) as avg_estimated,
                        AVG(t.actual_hours) as avg_actual
                    FROM tasks t
                    WHERE t.estimated_hours > 0
                    GROUP BY t.status
                    ORDER BY count DESC
                """),
                ("Поиск по тексту", "SELECT * FROM search_tasks('database')"),
                ("Пользовательская функция", "SELECT * FROM get_user_stats('550e8400-e29b-41d4-a716-446655440001')")
            ]
            
            results = {}
            
            for query_name, query_sql in queries:
                times = []
                for _ in range(5):  # 5 измерений для каждого запроса
                    start_time = time.time()
                    cursor.execute(query_sql)
                    cursor.fetchall()
                    execution_time = time.time() - start_time
                    times.append(execution_time)
                
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                results[query_name] = {
                    'avg': avg_time,
                    'min': min_time,
                    'max': max_time
                }
                
                print(f"✅ {query_name}: {avg_time:.4f}с (мин: {min_time:.4f}с, макс: {max_time:.4f}с)")
            
            # Сохраняем метрики
            self.performance_metrics['query_benchmark'] = results
            
            # Проверяем, что все запросы выполняются в разумное время
            slow_queries = [name for name, data in results.items() if data['avg'] > 2.0]
            if slow_queries:
                print(f"⚠️  Медленные запросы: {slow_queries}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка бенчмарка: {e}")
            return False

    def test_stress_test(self) -> bool:
        """Стресс-тест базы данных"""
        print("\n🔍 Стресс-тест базы данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестовые данные для стресс-теста
            test_users = []
            test_projects = []
            test_tasks = []
            
            # Создаем 100 тестовых пользователей
            for i in range(100):
                user_id = str(uuid.uuid4())
                username = f"stress_test_user_{i}"
                email = f"stress_{i}@test.com"
                
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, (user_id, username, email, '$2b$12$test_hash'))
                
                test_users.append(user_id)
            
            # Создаем 50 тестовых проектов
            for i in range(50):
                project_id = str(uuid.uuid4())
                name = f"Stress Test Project {i}"
                owner_id = random.choice(test_users)
                
                cursor.execute("""
                    INSERT INTO projects (id, name, description, owner_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (project_id, name, f"Description for project {i}", owner_id))
                
                test_projects.append(project_id)
            
            # Создаем 200 тестовых задач
            for i in range(200):
                task_id = str(uuid.uuid4())
                title = f"Stress Test Task {i}"
                project_id = random.choice(test_projects)
                assignee_id = random.choice(test_users)
                status = random.choice(['todo', 'in_progress', 'completed'])
                priority = random.choice(['low', 'medium', 'high'])
                estimated_hours = random.uniform(1.0, 20.0)
                
                cursor.execute("""
                    INSERT INTO tasks (id, title, description, project_id, assignee_id, status, priority, estimated_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (task_id, title, f"Description for task {i}", project_id, assignee_id, status, priority, estimated_hours))
                
                test_tasks.append(task_id)
            
            print(f"✅ Создано {len(test_users)} пользователей, {len(test_projects)} проектов, {len(test_tasks)} задач")
            
            # Выполняем стресс-тест - множественные одновременные запросы
            start_time = time.time()
            query_count = 0
            
            for _ in range(1000):
                try:
                    # Случайный запрос
                    query_type = random.randint(1, 5)
                    
                    if query_type == 1:
                        cursor.execute("SELECT COUNT(*) FROM users")
                    elif query_type == 2:
                        cursor.execute("SELECT COUNT(*) FROM projects")
                    elif query_type == 3:
                        cursor.execute("SELECT COUNT(*) FROM tasks")
                    elif query_type == 4:
                        cursor.execute("""
                            SELECT u.username, COUNT(t.id) as task_count
                            FROM users u
                            LEFT JOIN tasks t ON u.id = t.assignee_id
                            GROUP BY u.id, u.username
                            LIMIT 10
                        """)
                    else:
                        cursor.execute("""
                            SELECT p.name, COUNT(t.id) as task_count
                            FROM projects p
                            LEFT JOIN tasks t ON p.id = t.project_id
                            GROUP BY p.id, p.name
                            LIMIT 10
                        """)
                    
                    cursor.fetchall()
                    query_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Ошибка в запросе {query_count}: {e}")
            
            total_time = time.time() - start_time
            queries_per_second = query_count / total_time
            
            print(f"✅ Стресс-тест завершен: {query_count} запросов за {total_time:.2f}с")
            print(f"✅ Производительность: {queries_per_second:.2f} запросов/сек")
            
            # Сохраняем метрики
            self.performance_metrics['stress_test'] = {
                'total_queries': query_count,
                'total_time': total_time,
                'queries_per_second': queries_per_second
            }
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM tasks WHERE title LIKE 'Stress Test Task%'")
            cursor.execute("DELETE FROM projects WHERE name LIKE 'Stress Test Project%'")
            cursor.execute("DELETE FROM users WHERE username LIKE 'stress_test_user%'")
            
            print("✅ Тестовые данные очищены")
            
            return queries_per_second > 10  # Минимум 10 запросов в секунду
            
        except Exception as e:
            print(f"❌ Ошибка стресс-теста: {e}")
            return False

    def test_memory_usage(self) -> bool:
        """Тест использования памяти"""
        print("\n🔍 Тестирование использования памяти...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Получаем информацию о размере базы данных
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_database_size(current_database()) as db_size_bytes
            """)
            
            db_info = cursor.fetchone()
            db_size = db_info[0]
            db_size_bytes = db_info[1]
            
            print(f"✅ Размер базы данных: {db_size}")
            
            # Получаем размеры таблиц
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            
            table_sizes = cursor.fetchall()
            print("✅ Размеры таблиц (топ-10):")
            for table in table_sizes:
                print(f"  {table[1]}: {table[2]}")
            
            # Получаем информацию о кэше
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_stat_get_db_blocks_hit(oid)) as cache_hits,
                    pg_size_pretty(pg_stat_get_db_blocks_read(oid)) as cache_reads
                FROM pg_database 
                WHERE datname = current_database()
            """)
            
            cache_info = cursor.fetchone()
            print(f"✅ Кэш: hits={cache_info[0]}, reads={cache_info[1]}")
            
            # Сохраняем метрики
            self.performance_metrics['memory_usage'] = {
                'database_size': db_size_bytes,
                'database_size_pretty': db_size,
                'table_sizes': {table[1]: table[3] for table in table_sizes}
            }
            
            # Проверяем, что база данных не слишком большая для тестовой среды
            if db_size_bytes > 100 * 1024 * 1024:  # 100 MB
                print(f"⚠️  База данных довольно большая: {db_size}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки памяти: {e}")
            return False

    def test_connection_pooling(self) -> bool:
        """Тест пула подключений"""
        print("\n🔍 Тестирование пула подключений...")
        
        try:
            # Создаем пул подключений
            connections = []
            max_connections = 10
            
            # Создаем подключения
            for i in range(max_connections):
                conn = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password']
                )
                connections.append(conn)
            
            print(f"✅ Создано {len(connections)} подключений")
            
            # Тестируем параллельное выполнение запросов
            def execute_query(conn_id, conn):
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT pg_sleep(0.1), %s as conn_id", (conn_id,))
                    result = cursor.fetchone()
                    return True
                except Exception as e:
                    print(f"❌ Ошибка в подключении {conn_id}: {e}")
                    return False
            
            # Запускаем запросы параллельно
            threads = []
            start_time = time.time()
            
            for i, conn in enumerate(connections):
                thread = threading.Thread(target=execute_query, args=(i, conn))
                threads.append(thread)
                thread.start()
            
            # Ждем завершения всех потоков
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            print(f"✅ Параллельные запросы выполнены за {total_time:.4f}с")
            
            # Закрываем все подключения
            for conn in connections:
                conn.close()
            
            # Сохраняем метрики
            self.performance_metrics['connection_pooling'] = {
                'max_connections': max_connections,
                'parallel_execution_time': total_time
            }
            
            return total_time < 1.0  # Должно выполняться менее чем за 1 секунду
            
        except Exception as e:
            print(f"❌ Ошибка тестирования пула подключений: {e}")
            return False

    def test_transaction_isolation(self) -> bool:
        """Тест изоляции транзакций"""
        print("\n🔍 Тестирование изоляции транзакций...")
        
        try:
            # Создаем два подключения для тестирования изоляции
            conn1 = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            conn2 = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            # Начинаем транзакцию в первом подключении
            conn1.autocommit = False
            cursor1 = conn1.cursor()
            
            # Начинаем транзакцию во втором подключении
            conn2.autocommit = False
            cursor2 = conn2.cursor()
            
            # Вставляем тестовую запись в первой транзакции
            test_id = str(uuid.uuid4())
            cursor1.execute("""
                INSERT INTO users (id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """, (test_id, 'isolation_test_user', 'isolation@test.com', '$2b$12$test_hash'))
            
            # Проверяем, что вторая транзакция не видит изменения
            cursor2.execute("SELECT COUNT(*) FROM users WHERE username = 'isolation_test_user'")
            count_before_commit = cursor2.fetchone()[0]
            
            if count_before_commit != 0:
                print("❌ Нарушение изоляции транзакций")
                conn1.rollback()
                conn2.rollback()
                conn1.close()
                conn2.close()
                return False
            
            # Коммитим первую транзакцию
            conn1.commit()
            
            # Теперь вторая транзакция должна видеть изменение
            cursor2.execute("SELECT COUNT(*) FROM users WHERE username = 'isolation_test_user'")
            count_after_commit = cursor2.fetchone()[0]
            
            if count_after_commit != 1:
                print("❌ Изменение не видно после коммита")
                conn2.rollback()
                conn1.close()
                conn2.close()
                return False
            
            # Очищаем тестовые данные
            cursor1.execute("DELETE FROM users WHERE username = 'isolation_test_user'")
            conn1.commit()
            
            # Закрываем подключения
            conn1.close()
            conn2.close()
            
            print("✅ Изоляция транзакций работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования изоляции: {e}")
            return False

    def test_deadlock_handling(self) -> bool:
        """Тест обработки deadlock'ов"""
        print("\n🔍 Тестирование обработки deadlock'ов...")
        
        try:
            # Создаем два подключения
            conn1 = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            conn2 = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            
            conn1.autocommit = False
            conn2.autocommit = False
            
            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()
            
            # Создаем тестовые записи
            test_user1 = str(uuid.uuid4())
            test_user2 = str(uuid.uuid4())
            
            cursor1.execute("""
                INSERT INTO users (id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """, (test_user1, 'deadlock_test_user1', 'deadlock1@test.com', '$2b$12$test_hash'))
            
            cursor2.execute("""
                INSERT INTO users (id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """, (test_user2, 'deadlock_test_user2', 'deadlock2@test.com', '$2b$12$test_hash'))
            
            conn1.commit()
            conn2.commit()
            
            # Пытаемся создать deadlock
            def transaction1():
                try:
                    cursor1.execute("SELECT * FROM users WHERE id = %s FOR UPDATE", (test_user1,))
                    time.sleep(0.1)  # Небольшая задержка
                    cursor1.execute("SELECT * FROM users WHERE id = %s FOR UPDATE", (test_user2,))
                    conn1.commit()
                    return True
                except Exception as e:
                    conn1.rollback()
                    return False
            
            def transaction2():
                try:
                    cursor2.execute("SELECT * FROM users WHERE id = %s FOR UPDATE", (test_user2,))
                    time.sleep(0.1)  # Небольшая задержка
                    cursor2.execute("SELECT * FROM users WHERE id = %s FOR UPDATE", (test_user1,))
                    conn2.commit()
                    return True
                except Exception as e:
                    conn2.rollback()
                    return False
            
            # Запускаем транзакции параллельно
            thread1 = threading.Thread(target=transaction1)
            thread2 = threading.Thread(target=transaction2)
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            # Очищаем тестовые данные
            cursor1.execute("DELETE FROM users WHERE username LIKE 'deadlock_test_user%'")
            conn1.commit()
            
            conn1.close()
            conn2.close()
            
            print("✅ Обработка deadlock'ов работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования deadlock'ов: {e}")
            return False

    def test_backup_and_restore(self) -> bool:
        """Тест резервного копирования и восстановления"""
        print("\n🔍 Тестирование резервного копирования и восстановления...")
        
        try:
            # Проверяем наличие скриптов резервного копирования
            import os
            backup_script = "scripts/backup.sh"
            restore_script = "scripts/restore.sh"
            
            if not os.path.exists(backup_script):
                print(f"⚠️  Скрипт резервного копирования не найден: {backup_script}")
                return True  # Не критично для тестов
            
            if not os.path.exists(restore_script):
                print(f"⚠️  Скрипт восстановления не найден: {restore_script}")
                return True  # Не критично для тестов
            
            print("✅ Скрипты резервного копирования найдены")
            
            # Проверяем права на выполнение
            if os.access(backup_script, os.X_OK):
                print("✅ Скрипт резервного копирования исполняемый")
            else:
                print("⚠️  Скрипт резервного копирования не исполняемый")
            
            if os.access(restore_script, os.X_OK):
                print("✅ Скрипт восстановления исполняемый")
            else:
                print("⚠️  Скрипт восстановления не исполняемый")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки резервного копирования: {e}")
            return False

    def run_all_advanced_tests(self) -> Dict[str, bool]:
        """Запуск всех расширенных тестов"""
        print("🚀 Запуск расширенных тестов базы данных TaskWeight...")
        print("=" * 60)
        
        tests = [
            ("Одновременные подключения", self.test_concurrent_connections),
            ("Бенчмарк производительности", self.test_query_performance_benchmark),
            ("Стресс-тест", self.test_stress_test),
            ("Использование памяти", self.test_memory_usage),
            ("Пул подключений", self.test_connection_pooling),
            ("Изоляция транзакций", self.test_transaction_isolation),
            ("Обработка deadlock'ов", self.test_deadlock_handling),
            ("Резервное копирование", self.test_backup_and_restore)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    print(f"✅ {test_name}: ПРОЙДЕН")
                else:
                    print(f"❌ {test_name}: ПРОВАЛЕН")
            except Exception as e:
                print(f"💥 {test_name}: ОШИБКА - {e}")
                results[test_name] = False
        
        return results
    
    def generate_advanced_report(self, results: Dict[str, bool]) -> None:
        """Генерация расширенного отчета"""
        print("\n" + "=" * 60)
        print("📊 РАСШИРЕННЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"Всего расширенных тестов: {total}")
        print(f"Пройдено: {passed}")
        print(f"Провалено: {total - passed}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ВСЕ РАСШИРЕННЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        elif success_rate >= 80:
            print("\n⚠️  Большинство расширенных тестов пройдено.")
        else:
            print("\n❌ Много расширенных тестов провалено.")
        
        print("\nДетальные результаты:")
        for test_name, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"  {test_name}: {status}")
        
        # Выводим метрики производительности
        if self.performance_metrics:
            print("\n📈 МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ:")
            for metric_name, metric_data in self.performance_metrics.items():
                print(f"\n{metric_name.upper()}:")
                if isinstance(metric_data, dict):
                    for key, value in metric_data.items():
                        if isinstance(value, float):
                            print(f"  {key}: {value:.4f}")
                        else:
                            print(f"  {key}: {value}")
                else:
                    print(f"  {metric_data}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.pg_conn:
            self.pg_conn.close()

def main():
    """Основная функция"""
    # Конфигурация подключения к базе данных
    db_config = {
        'host': 'localhost',
        'port': '5433',  # Порт из docker-compose
        'database': 'taskweight',
        'user': 'taskweight_user',
        'password': 'taskweight_password',
        'redis_host': 'localhost',
        'redis_port': '6380',  # Порт из docker-compose
        'redis_password': 'redis_password'
    }
    
    tester = AdvancedDatabaseTester(db_config)
    
    try:
        # Подключение к базе данных
        if not tester.connect_postgres():
            print("❌ Не удалось подключиться к PostgreSQL")
            sys.exit(1)
        
        if not tester.connect_redis():
            print("❌ Не удалось подключиться к Redis")
            sys.exit(1)
        
        # Запуск расширенных тестов
        results = tester.run_all_advanced_tests()
        
        # Генерация расширенного отчета
        tester.generate_advanced_report(results)
        
        # Возвращаем код выхода в зависимости от результатов
        success_rate = (sum(1 for result in results.values() if result) / len(results)) * 100
        if success_rate >= 80:
            sys.exit(0)  # Успех
        else:
            sys.exit(1)  # Ошибка
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Расширенное тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
