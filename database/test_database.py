#!/usr/bin/env python3
"""
TaskWeight Database Test Suite
Тестирует все аспекты базы данных после развертывания
"""

import psycopg2
import redis
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

class DatabaseTester:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.pg_conn = None
        self.redis_conn = None
        self.test_results = []
        
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
            # Проверка подключения
            self.redis_conn.ping()
            print("✅ Подключение к Redis успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            return False
    
    def test_table_structure(self) -> bool:
        """Тест структуры таблиц"""
        print("\n🔍 Тестирование структуры таблиц...")
        
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
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            missing_tables = set(expected_tables) - set(existing_tables)
            
            if missing_tables:
                print(f"❌ Отсутствуют таблицы: {missing_tables}")
                return False
            
            print(f"✅ Все {len(existing_tables)} таблиц присутствуют")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки структуры таблиц: {e}")
            return False
    
    def test_extensions(self) -> bool:
        """Тест расширений PostgreSQL"""
        print("\n🔍 Тестирование расширений...")
        
        expected_extensions = ['uuid-ossp', 'pg_trgm', 'btree_gin']
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT extname 
                FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin')
            """)
            
            existing_extensions = [row[0] for row in cursor.fetchall()]
            missing_extensions = set(expected_extensions) - set(existing_extensions)
            
            if missing_extensions:
                print(f"❌ Отсутствуют расширения: {missing_extensions}")
                return False
            
            print(f"✅ Все расширения установлены: {existing_extensions}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки расширений: {e}")
            return False
    
    def test_functions(self) -> bool:
        """Тест функций базы данных"""
        print("\n🔍 Тестирование функций...")
        
        expected_functions = [
            'update_updated_at_column', 'search_tasks', 'record_metric',
            'get_metrics', 'create_notification', 'get_pending_notifications',
            'get_user_stats', 'get_project_timeline', 'get_estimation_accuracy'
        ]
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT proname 
                FROM pg_proc p 
                JOIN pg_namespace n ON p.pronamespace = n.oid 
                WHERE n.nspname = 'public' 
                AND proname IN ('update_updated_at_column', 'search_tasks', 'record_metric', 'get_user_stats', 'get_project_timeline', 'get_estimation_accuracy')
            """)
            
            existing_functions = [row[0] for row in cursor.fetchall()]
            missing_functions = set(expected_functions[:6]) - set(existing_functions)
            
            if missing_functions:
                print(f"❌ Отсутствуют функции: {missing_functions}")
                return False
            
            print(f"✅ Основные функции присутствуют: {existing_functions}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки функций: {e}")
            return False
    
    def test_views(self) -> bool:
        """Тест представлений"""
        print("\n🔍 Тестирование представлений...")
        
        expected_views = ['task_details', 'project_stats', 'user_workload', 'estimation_analytics']
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT viewname 
                FROM pg_views 
                WHERE schemaname = 'public' 
                ORDER BY viewname
            """)
            
            existing_views = [row[0] for row in cursor.fetchall()]
            missing_views = set(expected_views) - set(existing_views)
            
            if missing_views:
                print(f"❌ Отсутствуют представления: {missing_views}")
                return False
            
            print(f"✅ Все представления присутствуют: {existing_views}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки представлений: {e}")
            return False
    
    def test_triggers(self) -> bool:
        """Тест триггеров"""
        print("\n🔍 Тестирование триггеров...")
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT trigger_name, event_object_table 
                FROM information_schema.triggers 
                WHERE trigger_schema = 'public' 
                AND trigger_name LIKE '%updated_at%'
                ORDER BY event_object_table
            """)
            
            triggers = cursor.fetchall()
            if not triggers:
                print("❌ Триггеры updated_at не найдены")
                return False
            
            print(f"✅ Найдены триггеры updated_at для таблиц: {[t[1] for t in triggers]}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки триггеров: {e}")
            return False
    
    def test_indexes(self) -> bool:
        """Тест индексов"""
        print("\n🔍 Тестирование индексов...")
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname
            """)
            
            indexes = cursor.fetchall()
            if not indexes:
                print("❌ Индексы не найдены")
                return False
            
            print(f"✅ Найдено {len(indexes)} индексов")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки индексов: {e}")
            return False
    
    def test_sample_data(self) -> bool:
        """Тест тестовых данных"""
        print("\n🔍 Тестирование тестовых данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Проверяем количество записей в основных таблицах
            tables_to_check = ['users', 'projects', 'tasks']
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    print(f"❌ Таблица {table} пуста")
                    return False
                print(f"✅ Таблица {table}: {count} записей")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки тестовых данных: {e}")
            return False
    
    def test_constraints(self) -> bool:
        """Тест ограничений и связей"""
        print("\n🔍 Тестирование ограничений и связей...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Проверяем внешние ключи
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name
            """)
            
            foreign_keys = cursor.fetchall()
            if not foreign_keys:
                print("❌ Внешние ключи не найдены")
                return False
            
            print(f"✅ Найдено {len(foreign_keys)} внешних ключей")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки ограничений: {e}")
            return False
    
    def test_redis_operations(self) -> bool:
        """Тест операций Redis"""
        print("\n🔍 Тестирование Redis...")
        
        try:
            # Тест записи и чтения
            test_key = "test:database:health"
            test_value = {"status": "healthy", "timestamp": datetime.now().isoformat()}
            
            self.redis_conn.set(test_key, json.dumps(test_value), ex=60)
            retrieved_value = self.redis_conn.get(test_key)
            
            if not retrieved_value:
                print("❌ Не удалось прочитать данные из Redis")
                return False
            
            parsed_value = json.loads(retrieved_value)
            if parsed_value['status'] != test_value['status']:
                print("❌ Данные в Redis не соответствуют записанным")
                return False
            
            # Очистка тестового ключа
            self.redis_conn.delete(test_key)
            
            print("✅ Redis операции работают корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования Redis: {e}")
            return False
    
    def test_performance(self) -> bool:
        """Тест производительности"""
        print("\n🔍 Тестирование производительности...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест простого запроса
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM users")
            cursor.fetchone()
            simple_query_time = time.time() - start_time
            
            # Тест сложного запроса с JOIN
            start_time = time.time()
            cursor.execute("""
                SELECT u.username, p.name as project_name, COUNT(t.id) as task_count
                FROM users u
                LEFT JOIN projects p ON u.id = p.owner_id
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY u.id, u.username, p.name
                ORDER BY task_count DESC
            """)
            cursor.fetchall()
            complex_query_time = time.time() - start_time
            
            print(f"✅ Простой запрос: {simple_query_time:.4f}с")
            print(f"✅ Сложный запрос: {complex_query_time:.4f}с")
            
            # Проверяем, что запросы выполняются в разумное время
            if simple_query_time > 1.0 or complex_query_time > 5.0:
                print("⚠️  Запросы выполняются медленно")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования производительности: {e}")
            return False
    
    def test_data_integrity(self) -> bool:
        """Тест целостности данных"""
        print("\n🔍 Тестирование целостности данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Проверяем, что все пользователи имеют настройки
            cursor.execute("""
                SELECT COUNT(*) FROM users u
                LEFT JOIN user_settings us ON u.id = us.user_id
                WHERE us.id IS NULL
            """)
            
            users_without_settings = cursor.fetchone()[0]
            if users_without_settings > 0:
                print(f"⚠️  {users_without_settings} пользователей без настроек")
            
            # Проверяем, что все проекты имеют владельцев
            cursor.execute("""
                SELECT COUNT(*) FROM projects p
                LEFT JOIN users u ON p.owner_id = u.id
                WHERE u.id IS NULL
            """)
            
            orphaned_projects = cursor.fetchone()[0]
            if orphaned_projects > 0:
                print(f"❌ {orphaned_projects} проектов без владельцев")
                return False
            
            print("✅ Целостность данных проверена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки целостности данных: {e}")
            return False

    def test_custom_functions(self) -> bool:
        """Тест пользовательских функций"""
        print("\n🔍 Тестирование пользовательских функций...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест функции get_user_stats
            cursor.execute("SELECT * FROM get_user_stats('550e8400-e29b-41d4-a716-446655440001')")
            user_stats = cursor.fetchone()
            if not user_stats:
                print("❌ Функция get_user_stats не работает")
                return False
            
            print(f"✅ get_user_stats: {user_stats}")
            
            # Тест функции search_tasks
            cursor.execute("SELECT * FROM search_tasks('database')")
            search_results = cursor.fetchall()
            if not search_results:
                print("❌ Функция search_tasks не работает")
                return False
            
            print(f"✅ search_tasks: найдено {len(search_results)} результатов")
            
            # Тест функции get_project_timeline
            cursor.execute("SELECT * FROM get_project_timeline('550e8400-e29b-41d4-a716-446655440010')")
            timeline = cursor.fetchall()
            if not timeline:
                print("❌ Функция get_project_timeline не работает")
                return False
            
            print(f"✅ get_project_timeline: найдено {len(timeline)} задач")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования пользовательских функций: {e}")
            return False

    def test_views_data(self) -> bool:
        """Тест данных в представлениях"""
        print("\n🔍 Тестирование данных в представлениях...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест task_details
            cursor.execute("SELECT COUNT(*) FROM task_details")
            task_details_count = cursor.fetchone()[0]
            if task_details_count == 0:
                print("❌ Представление task_details пусто")
                return False
            print(f"✅ task_details: {task_details_count} записей")
            
            # Тест project_stats
            cursor.execute("SELECT COUNT(*) FROM project_stats")
            project_stats_count = cursor.fetchone()[0]
            if project_stats_count == 0:
                print("❌ Представление project_stats пусто")
                return False
            print(f"✅ project_stats: {project_stats_count} записей")
            
            # Тест user_workload
            cursor.execute("SELECT COUNT(*) FROM user_workload")
            user_workload_count = cursor.fetchone()[0]
            if user_workload_count == 0:
                print("❌ Представление user_workload пусто")
                return False
            print(f"✅ user_workload: {user_workload_count} записей")
            
            # Тест estimation_analytics
            cursor.execute("SELECT COUNT(*) FROM estimation_analytics")
            estimation_analytics_count = cursor.fetchone()[0]
            if estimation_analytics_count == 0:
                print("❌ Представление estimation_analytics пусто")
                return False
            print(f"✅ estimation_analytics: {estimation_analytics_count} записей")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования представлений: {e}")
            return False

    def test_extended_data(self) -> bool:
        """Тест расширенных данных"""
        print("\n🔍 Тестирование расширенных данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест task_categories
            cursor.execute("SELECT COUNT(*) FROM task_categories")
            categories_count = cursor.fetchone()[0]
            if categories_count == 0:
                print("❌ Таблица task_categories пуста")
                return False
            print(f"✅ task_categories: {categories_count} записей")
            
            # Тест webhooks
            cursor.execute("SELECT COUNT(*) FROM webhooks")
            webhooks_count = cursor.fetchone()[0]
            if webhooks_count == 0:
                print("❌ Таблица webhooks пуста")
                return False
            print(f"✅ webhooks: {webhooks_count} записей")
            
            # Тест metrics
            cursor.execute("SELECT COUNT(*) FROM metrics")
            metrics_count = cursor.fetchone()[0]
            if metrics_count == 0:
                print("❌ Таблица metrics пуста")
                return False
            print(f"✅ metrics: {metrics_count} записей")
            
            # Тест performance_metrics
            cursor.execute("SELECT COUNT(*) FROM performance_metrics")
            perf_metrics_count = cursor.fetchone()[0]
            if perf_metrics_count == 0:
                print("❌ Таблица performance_metrics пуста")
                return False
            print(f"✅ performance_metrics: {perf_metrics_count} записей")
            
            # Тест user_activity_logs
            cursor.execute("SELECT COUNT(*) FROM user_activity_logs")
            activity_logs_count = cursor.fetchone()[0]
            if activity_logs_count == 0:
                print("❌ Таблица user_activity_logs пуста")
                return False
            print(f"✅ user_activity_logs: {activity_logs_count} записей")
            
            # Тест estimation_accuracy_history
            cursor.execute("SELECT COUNT(*) FROM estimation_accuracy_history")
            accuracy_history_count = cursor.fetchone()[0]
            if accuracy_history_count == 0:
                print("❌ Таблица estimation_accuracy_history пуста")
                return False
            print(f"✅ estimation_accuracy_history: {accuracy_history_count} записей")
            
            # Тест notification_templates
            cursor.execute("SELECT COUNT(*) FROM notification_templates")
            templates_count = cursor.fetchone()[0]
            if templates_count == 0:
                print("❌ Таблица notification_templates пуста")
                return False
            print(f"✅ notification_templates: {templates_count} записей")
            
            # Тест notifications
            cursor.execute("SELECT COUNT(*) FROM notifications")
            notifications_count = cursor.fetchone()[0]
            if notifications_count == 0:
                print("❌ Таблица notifications пуста")
                return False
            print(f"✅ notifications: {notifications_count} записей")
            
            # Тест notification_preferences
            cursor.execute("SELECT COUNT(*) FROM notification_preferences")
            preferences_count = cursor.fetchone()[0]
            if preferences_count == 0:
                print("❌ Таблица notification_preferences пуста")
                return False
            print(f"✅ notification_preferences: {preferences_count} записей")
            
            # Тест task_dependencies
            cursor.execute("SELECT COUNT(*) FROM task_dependencies")
            dependencies_count = cursor.fetchone()[0]
            if dependencies_count == 0:
                print("❌ Таблица task_dependencies пуста")
                return False
            print(f"✅ task_dependencies: {dependencies_count} записей")
            
            # Тест time_entries
            cursor.execute("SELECT COUNT(*) FROM time_entries")
            time_entries_count = cursor.fetchone()[0]
            if time_entries_count == 0:
                print("❌ Таблица time_entries пуста")
                return False
            print(f"✅ time_entries: {time_entries_count} записей")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования расширенных данных: {e}")
            return False

    def test_business_logic(self) -> bool:
        """Тест бизнес-логики"""
        print("\n🔍 Тестирование бизнес-логики...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест: задачи с категориями
            cursor.execute("""
                SELECT COUNT(*) FROM tasks t
                JOIN task_categories tc ON t.category_id = tc.id
                WHERE tc.name = 'Database'
            """)
            db_tasks_count = cursor.fetchone()[0]
            if db_tasks_count == 0:
                print("❌ Нет задач в категории Database")
                return False
            print(f"✅ Задач в категории Database: {db_tasks_count}")
            
            # Тест: зависимости задач
            cursor.execute("""
                SELECT COUNT(*) FROM task_dependencies td
                JOIN tasks t1 ON td.dependent_task_id = t1.id
                JOIN tasks t2 ON td.prerequisite_task_id = t2.id
                WHERE t1.title = 'User Authentication' AND t2.title = 'Setup Database'
            """)
            dependencies_count = cursor.fetchone()[0]
            if dependencies_count == 0:
                print("❌ Зависимости между задачами не найдены")
                return False
            print(f"✅ Зависимости между задачами: {dependencies_count}")
            
            # Тест: учет времени
            cursor.execute("""
                SELECT SUM(duration_minutes) FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                WHERE t.title = 'Setup Database'
            """)
            total_time = cursor.fetchone()[0]
            if total_time != 240:  # 4 часа = 240 минут
                print(f"❌ Неправильное время для Setup Database: {total_time} минут")
                return False
            print(f"✅ Время для Setup Database: {total_time} минут")
            
            # Тест: метрики производительности
            cursor.execute("""
                SELECT COUNT(*) FROM performance_metrics pm
                JOIN tasks t ON pm.task_id = t.id
                WHERE t.title = 'Setup Database' AND pm.metric_type = 'estimation_accuracy'
            """)
            perf_metrics_count = cursor.fetchone()[0]
            if perf_metrics_count == 0:
                print("❌ Метрики производительности не найдены")
                return False
            print(f"✅ Метрики производительности: {perf_metrics_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования бизнес-логики: {e}")
            return False

    def test_data_relationships(self) -> bool:
        """Тест связей между данными"""
        print("\n🔍 Тестирование связей между данными...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест: пользователи -> проекты -> задачи
            cursor.execute("""
                SELECT u.username, p.name, COUNT(t.id) as task_count
                FROM users u
                JOIN projects p ON u.id = p.owner_id
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY u.id, u.username, p.id, p.name
                ORDER BY u.username, p.name
            """)
            
            relationships = cursor.fetchall()
            if not relationships:
                print("❌ Связи пользователи-проекты-задачи не найдены")
                return False
            
            print("✅ Связи пользователи-проекты-задачи:")
            for rel in relationships:
                print(f"  {rel[0]} -> {rel[1]}: {rel[2]} задач")
            
            # Тест: webhook -> интеграции
            cursor.execute("""
                SELECT w.name, w.events, i.service_type
                FROM webhooks w
                JOIN integrations i ON w.integration_id = i.id
                ORDER BY w.name
            """)
            
            webhook_integrations = cursor.fetchall()
            if not webhook_integrations:
                print("❌ Связи webhook-интеграции не найдены")
                return False
            
            print("✅ Связи webhook-интеграции:")
            for wi in webhook_integrations:
                print(f"  {wi[0]} -> {wi[2]} ({wi[1]})")
            
            # Тест: уведомления -> шаблоны
            cursor.execute("""
                SELECT n.title, nt.name as template_name, n.status
                FROM notifications n
                JOIN notification_templates nt ON n.template_id = nt.id
                ORDER BY n.title
            """)
            
            notification_templates = cursor.fetchall()
            if not notification_templates:
                print("❌ Связи уведомления-шаблоны не найдены")
                return False
            
            print("✅ Связи уведомления-шаблоны:")
            for nt in notification_templates:
                print(f"  {nt[0]} -> {nt[1]} ({nt[2]})")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования связей: {e}")
            return False

    def test_data_validation(self) -> bool:
        """Тест валидации данных"""
        print("\n🔍 Тестирование валидации данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест: уникальность username
            cursor.execute("""
                SELECT username, COUNT(*) 
                FROM users 
                GROUP BY username 
                HAVING COUNT(*) > 1
            """)
            
            duplicate_usernames = cursor.fetchall()
            if duplicate_usernames:
                print(f"❌ Дублирующиеся username: {duplicate_usernames}")
                return False
            print("✅ Username уникальны")
            
            # Тест: уникальность email
            cursor.execute("""
                SELECT email, COUNT(*) 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)
            
            duplicate_emails = cursor.fetchall()
            if duplicate_emails:
                print(f"❌ Дублирующиеся email: {duplicate_emails}")
                return False
            print("✅ Email уникальны")
            
            # Тест: валидность статусов задач
            cursor.execute("""
                SELECT DISTINCT status FROM tasks
            """)
            
            task_statuses = [row[0] for row in cursor.fetchall()]
            valid_statuses = ['todo', 'in_progress', 'completed']
            invalid_statuses = set(task_statuses) - set(valid_statuses)
            
            if invalid_statuses:
                print(f"❌ Невалидные статусы задач: {invalid_statuses}")
                return False
            print("✅ Статусы задач валидны")
            
            # Тест: валидность приоритетов
            cursor.execute("""
                SELECT DISTINCT priority FROM tasks
            """)
            
            task_priorities = [row[0] for row in cursor.fetchall()]
            valid_priorities = ['low', 'medium', 'high']
            invalid_priorities = set(task_priorities) - set(valid_priorities)
            
            if invalid_priorities:
                print(f"❌ Невалидные приоритеты задач: {invalid_priorities}")
                return False
            print("✅ Приоритеты задач валидны")
            
            # Тест: положительные значения времени
            cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE estimated_hours < 0 OR actual_hours < 0
            """)
            
            negative_time = cursor.fetchone()[0]
            if negative_time > 0:
                print(f"❌ Найдено {negative_time} задач с отрицательным временем")
                return False
            print("✅ Время задач положительное")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования валидации: {e}")
            return False

    def test_audit_and_logging(self) -> bool:
        """Тест аудита и логирования"""
        print("\n🔍 Тестирование аудита и логирования...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест: audit_logs
            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            audit_logs_count = cursor.fetchone()[0]
            print(f"✅ audit_logs: {audit_logs_count} записей")
            
            # Тест: user_activity_logs
            cursor.execute("SELECT COUNT(*) FROM user_activity_logs")
            activity_logs_count = cursor.fetchone()[0]
            if activity_logs_count == 0:
                print("❌ user_activity_logs пуста")
                return False
            print(f"✅ user_activity_logs: {activity_logs_count} записей")
            
            # Тест: notification_logs (если таблица существует)
            try:
                cursor.execute("SELECT COUNT(*) FROM notification_logs")
                notification_logs_count = cursor.fetchone()[0]
                print(f"✅ notification_logs: {notification_logs_count} записей")
            except:
                print("⚠️  Таблица notification_logs не существует")
            
            # Тест: webhook_deliveries
            cursor.execute("SELECT COUNT(*) FROM webhook_deliveries")
            webhook_deliveries_count = cursor.fetchone()[0]
            print(f"✅ webhook_deliveries: {webhook_deliveries_count} записей")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования аудита: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Запуск всех тестов"""
        print("🚀 Запуск тестов базы данных TaskWeight...")
        print("=" * 50)
        
        tests = [
            ("Структура таблиц", self.test_table_structure),
            ("Расширения PostgreSQL", self.test_extensions),
            ("Функции", self.test_functions),
            ("Представления", self.test_views),
            ("Триггеры", self.test_triggers),
            ("Индексы", self.test_indexes),
            ("Тестовые данные", self.test_sample_data),
            ("Ограничения и связи", self.test_constraints),
            ("Redis операции", self.test_redis_operations),
            ("Производительность", self.test_performance),
            ("Целостность данных", self.test_data_integrity),
            ("Пользовательские функции", self.test_custom_functions),
            ("Данные в представлениях", self.test_views_data),
            ("Расширенные данные", self.test_extended_data),
            ("Бизнес-логика", self.test_business_logic),
            ("Связи между данными", self.test_data_relationships),
            ("Валидация данных", self.test_data_validation),
            ("Аудит и логирование", self.test_audit_and_logging)
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
    
    def generate_report(self, results: Dict[str, bool]) -> None:
        """Генерация отчета о тестах"""
        print("\n" + "=" * 50)
        print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"Всего тестов: {total}")
        print(f"Пройдено: {passed}")
        print(f"Провалено: {total - passed}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! База данных работает корректно.")
        elif success_rate >= 80:
            print("\n⚠️  Большинство тестов пройдено, но есть проблемы.")
        else:
            print("\n❌ Много тестов провалено. Требуется диагностика.")
        
        print("\nДетальные результаты:")
        for test_name, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"  {test_name}: {status}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.redis_conn:
            self.redis_conn.close()

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
    
    tester = DatabaseTester(db_config)
    
    try:
        # Подключение к базам данных
        if not tester.connect_postgres():
            print("❌ Не удалось подключиться к PostgreSQL")
            sys.exit(1)
        
        if not tester.connect_redis():
            print("❌ Не удалось подключиться к Redis")
            sys.exit(1)
        
        # Запуск тестов
        results = tester.run_all_tests()
        
        # Генерация отчета
        tester.generate_report(results)
        
        # Возвращаем код выхода в зависимости от результатов
        success_rate = (sum(1 for result in results.values() if result) / len(results)) * 100
        if success_rate >= 80:
            sys.exit(0)  # Успех
        else:
            sys.exit(1)  # Ошибка
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
