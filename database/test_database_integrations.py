#!/usr/bin/env python3
"""
TaskWeight Integration and Business Logic Test Suite
Тесты для интеграций, webhook'ов, уведомлений и бизнес-логики
"""

import psycopg2
import redis
import json
import sys
import time
import requests
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import threading

class IntegrationDatabaseTester:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.pg_conn = None
        self.redis_conn = None
        self.test_results = []
        self.test_data = {}
        
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

    def test_webhook_system(self) -> bool:
        """Тест системы webhook'ов"""
        print("\n🔗 Тестирование системы webhook'ов...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестовый webhook
            webhook_id = str(uuid.uuid4())
            webhook_url = "https://httpbin.org/post"  # Тестовый сервис
            
            cursor.execute("""
                INSERT INTO webhooks (id, name, url, method, headers, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (webhook_id, f"test_webhook_{secrets.token_hex(4)}", 
                  webhook_url, "POST", json.dumps({"Content-Type": "application/json"}), True))
            
            # Создаем тестовую доставку webhook'а
            delivery_id = str(uuid.uuid4())
            test_payload = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            cursor.execute("""
                INSERT INTO webhook_deliveries (id, webhook_id, payload, status, response_code, 
                                              response_body, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (delivery_id, webhook_id, json.dumps(test_payload), "pending", None, None))
            
            # Симулируем отправку webhook'а
            try:
                response = requests.post(webhook_url, json=test_payload, timeout=10)
                
                # Обновляем статус доставки
                cursor.execute("""
                    UPDATE webhook_deliveries 
                    SET status = %s, response_code = %s, response_body = %s, updated_at = NOW()
                    WHERE id = %s
                """, ("delivered" if response.status_code == 200 else "failed", 
                      response.status_code, response.text[:500], delivery_id))
                
                print(f"✅ Webhook отправлен, статус: {response.status_code}")
                
            except requests.RequestException as e:
                print(f"⚠️  Webhook не доставлен: {e}")
                cursor.execute("""
                    UPDATE webhook_deliveries 
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s
                """, ("failed", delivery_id))
            
            # Проверяем, что webhook и доставка созданы
            cursor.execute("SELECT id FROM webhooks WHERE id = %s", (webhook_id,))
            if not cursor.fetchone():
                print("❌ Webhook не создан")
                return False
            
            cursor.execute("SELECT id FROM webhook_deliveries WHERE id = %s", (delivery_id,))
            if not cursor.fetchone():
                print("❌ Доставка webhook'а не создана")
                return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM webhook_deliveries WHERE id = %s", (delivery_id,))
            cursor.execute("DELETE FROM webhooks WHERE id = %s", (webhook_id,))
            
            print("✅ Тест системы webhook'ов пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования webhook'ов: {e}")
            return False

    def test_notification_system(self) -> bool:
        """Тест системы уведомлений"""
        print("\n🔔 Тестирование системы уведомлений...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестового пользователя
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (user_id, f"notification_user_{secrets.token_hex(4)}", 
                  f"notification_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("notificationpass".encode()).hexdigest()))
            
            # Создаем настройки уведомлений
            settings_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO user_settings (id, user_id, notification_email, notification_push, 
                                         created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (settings_id, user_id, True, True))
            
            # Создаем шаблон уведомления
            template_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notification_templates (id, name, subject, body, type, 
                                                  created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (template_id, f"test_template_{secrets.token_hex(4)}", 
                  "Test Subject", "Test notification body", "email"))
            
            # Создаем уведомление
            notification_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notifications (id, user_id, template_id, subject, body, 
                                         type, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (notification_id, user_id, template_id, "Test Subject", 
                  "Test notification body", "email", "pending"))
            
            # Создаем лог уведомления
            log_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notification_logs (id, notification_id, action, details, 
                                             created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (log_id, notification_id, "created", json.dumps({"test": True})))
            
            # Проверяем создание всех компонентов
            components = [
                ("user_settings", settings_id),
                ("notification_templates", template_id),
                ("notifications", notification_id),
                ("notification_logs", log_id)
            ]
            
            for table_name, record_id in components:
                cursor.execute(f"SELECT id FROM {table_name} WHERE id = %s", (record_id,))
                if not cursor.fetchone():
                    print(f"❌ Запись не создана в {table_name}")
                    return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM notification_logs WHERE id = %s", (log_id,))
            cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
            cursor.execute("DELETE FROM notification_templates WHERE id = %s", (template_id,))
            cursor.execute("DELETE FROM user_settings WHERE id = %s", (settings_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            print("✅ Тест системы уведомлений пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования уведомлений: {e}")
            return False

    def test_integration_management(self) -> bool:
        """Тест управления интеграциями"""
        print("\n🔌 Тестирование управления интеграциями...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестового пользователя
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (user_id, f"integration_user_{secrets.token_hex(4)}", 
                  f"integration_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("integrationpass".encode()).hexdigest()))
            
            # Создаем интеграцию с Trello
            trello_integration_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO integrations (id, user_id, service_type, service_name, 
                                        api_key, api_secret, is_active, settings, 
                                        created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (trello_integration_id, user_id, "trello", "Trello Test", 
                  f"trello_key_{secrets.token_hex(8)}", f"trello_secret_{secrets.token_hex(8)}", 
                  True, json.dumps({"board_id": "test_board", "list_id": "test_list"})))
            
            # Создаем интеграцию с Jira
            jira_integration_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO integrations (id, user_id, service_type, service_name, 
                                        api_key, api_secret, is_active, settings, 
                                        created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (jira_integration_id, user_id, "jira", "Jira Test", 
                  f"jira_key_{secrets.token_hex(8)}", f"jira_secret_{secrets.token_hex(8)}", 
                  False, json.dumps({"project_key": "TEST", "base_url": "https://test.atlassian.net"})))
            
            # Проверяем создание интеграций
            cursor.execute("SELECT COUNT(*) FROM integrations WHERE user_id = %s", (user_id,))
            integration_count = cursor.fetchone()[0]
            
            if integration_count != 2:
                print(f"❌ Создано {integration_count} интеграций вместо 2")
                return False
            
            # Проверяем активные интеграции
            cursor.execute("SELECT COUNT(*) FROM integrations WHERE user_id = %s AND is_active = true", (user_id,))
            active_count = cursor.fetchone()[0]
            
            if active_count != 1:
                print(f"❌ Активных интеграций {active_count} вместо 1")
                return False
            
            # Тестируем обновление настроек интеграции
            new_settings = {"board_id": "updated_board", "list_id": "updated_list", "new_field": "value"}
            cursor.execute("""
                UPDATE integrations 
                SET settings = %s, updated_at = NOW()
                WHERE id = %s
            """, (json.dumps(new_settings), trello_integration_id))
            
            # Проверяем обновление
            cursor.execute("SELECT settings FROM integrations WHERE id = %s", (trello_integration_id,))
            updated_settings = json.loads(cursor.fetchone()[0])
            
            if updated_settings != new_settings:
                print("❌ Настройки интеграции не обновились")
                return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM integrations WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            print("✅ Тест управления интеграциями пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования интеграций: {e}")
            return False

    def test_estimation_workflow(self) -> bool:
        """Тест рабочего процесса оценок"""
        print("\n📊 Тестирование рабочего процесса оценок...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестового пользователя
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (user_id, f"estimation_user_{secrets.token_hex(4)}", 
                  f"estimation_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("estimationpass".encode()).hexdigest()))
            
            # Создаем тестовый проект
            project_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (project_id, f"estimation_project_{secrets.token_hex(4)}", 
                  "Test project for estimation workflow", user_id))
            
            # Создаем категорию задач
            category_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO task_categories (id, name, description, color, project_id, 
                                           created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (category_id, f"estimation_category_{secrets.token_hex(4)}", 
                  "Test category", "#FF5733", project_id))
            
            # Создаем задачу
            task_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO tasks (id, title, description, project_id, assignee_id, 
                                  status, priority, estimated_hours, category_id, 
                                  created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (task_id, "Test Estimation Task", "Task for testing estimation workflow", 
                  project_id, user_id, "todo", "medium", 8.0, category_id))
            
            # Создаем результат AI-оценки
            estimation_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO estimation_results (id, card_id, task_description, 
                                              estimated_hours, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (estimation_id, f"card_{secrets.token_hex(8)}", 
                  "AI estimated task description", 6.5, "completed"))
            
            # Создаем запись о точности оценки
            accuracy_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO estimation_accuracy_history (id, estimation_id, actual_hours, 
                                                       accuracy_percentage, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (accuracy_id, estimation_id, 7.0, 92.86))  # 6.5/7.0 * 100
            
            # Создаем временные записи
            time_entry_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO time_entries (id, task_id, user_id, hours_spent, 
                                         description, date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (time_entry_id, task_id, user_id, 7.0, "Time spent on task", 
                  datetime.now().date()))
            
            # Проверяем создание всех компонентов
            components = [
                ("projects", project_id),
                ("task_categories", category_id),
                ("tasks", task_id),
                ("estimation_results", estimation_id),
                ("estimation_accuracy_history", accuracy_id),
                ("time_entries", time_entry_id)
            ]
            
            for table_name, record_id in components:
                cursor.execute(f"SELECT id FROM {table_name} WHERE id = %s", (record_id,))
                if not cursor.fetchone():
                    print(f"❌ Запись не создана в {table_name}")
                    return False
            
            # Тестируем связи между таблицами
            cursor.execute("""
                SELECT t.title, p.name as project_name, c.name as category_name,
                       e.estimated_hours, e.status
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                JOIN task_categories c ON t.category_id = c.id
                LEFT JOIN estimation_results e ON e.card_id = %s
                WHERE t.id = %s
            """, (f"card_{secrets.token_hex(8)}", task_id))
            
            task_info = cursor.fetchone()
            if not task_info:
                print("❌ Связи между таблицами не работают")
                return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM time_entries WHERE id = %s", (time_entry_id,))
            cursor.execute("DELETE FROM estimation_accuracy_history WHERE id = %s", (accuracy_id,))
            cursor.execute("DELETE FROM estimation_results WHERE id = %s", (estimation_id,))
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            cursor.execute("DELETE FROM task_categories WHERE id = %s", (category_id,))
            cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            print("✅ Тест рабочего процесса оценок пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования рабочего процесса оценок: {e}")
            return False

    def test_audit_and_logging(self) -> bool:
        """Тест аудита и логирования"""
        print("\n📝 Тестирование аудита и логирования...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестового пользователя
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (user_id, f"audit_user_{secrets.token_hex(4)}", 
                  f"audit_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("auditpass".encode()).hexdigest()))
            
            # Создаем несколько записей аудита
            audit_records = []
            for i in range(5):
                audit_id = str(uuid.uuid4())
                action = ["create", "update", "delete", "view", "export"][i % 5]
                
                cursor.execute("""
                    INSERT INTO audit_logs (id, user_id, action, table_name, record_id,
                                           old_values, new_values, ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (audit_id, user_id, action, "users", user_id,
                      json.dumps({"old_field": f"old_value_{i}"}) if action in ["update", "delete"] else None,
                      json.dumps({"new_field": f"new_value_{i}"}) if action in ["create", "update"] else None,
                      f"192.168.1.{i+1}", f"TestBrowser/{i+1}.0"))
                
                audit_records.append(audit_id)
            
            # Создаем записи активности пользователя
            activity_records = []
            for i in range(3):
                activity_id = str(uuid.uuid4())
                activity_type = ["login", "logout", "data_access"][i % 3]
                
                cursor.execute("""
                    INSERT INTO user_activity_logs (id, user_id, activity_type, details, 
                                                   ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (activity_id, user_id, activity_type, 
                      json.dumps({"session_id": f"session_{i}", "duration": i*10}),
                      f"192.168.1.{i+1}", f"TestBrowser/{i+1}.0"))
                
                activity_records.append(activity_id)
            
            # Проверяем создание записей аудита
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE user_id = %s", (user_id,))
            audit_count = cursor.fetchone()[0]
            
            if audit_count != 5:
                print(f"❌ Создано {audit_count} записей аудита вместо 5")
                return False
            
            # Проверяем создание записей активности
            cursor.execute("SELECT COUNT(*) FROM user_activity_logs WHERE user_id = %s", (user_id,))
            activity_count = cursor.fetchone()[0]
            
            if activity_count != 3:
                print(f"❌ Создано {activity_count} записей активности вместо 3")
                return False
            
            # Тестируем поиск по аудиту
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_logs 
                WHERE user_id = %s 
                GROUP BY action
                ORDER BY count DESC
            """, (user_id,))
            
            action_counts = cursor.fetchall()
            if len(action_counts) != 5:
                print("❌ Группировка по действиям не работает")
                return False
            
            # Очищаем тестовые данные
            for record_id in audit_records:
                cursor.execute("DELETE FROM audit_logs WHERE id = %s", (record_id,))
            
            for record_id in activity_records:
                cursor.execute("DELETE FROM user_activity_logs WHERE id = %s", (record_id,))
            
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            print("✅ Тест аудита и логирования пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования аудита: {e}")
            return False

    def test_metrics_and_performance(self) -> bool:
        """Тест метрик и производительности"""
        print("\n📈 Тестирование метрик и производительности...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестовые метрики
            metrics_records = []
            for i in range(10):
                metric_id = str(uuid.uuid4())
                metric_type = ["response_time", "throughput", "error_rate", "cpu_usage", "memory_usage"][i % 5]
                
                cursor.execute("""
                    INSERT INTO metrics (id, name, value, unit, tags, timestamp, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """, (metric_id, f"{metric_type}_{i}", 
                      round(100 + i * 10 + (i % 3) * 5, 2),  # Разные значения
                      "ms" if metric_type == "response_time" else "req/s" if metric_type == "throughput" else "%",
                      json.dumps({"environment": "test", "service": "database", "iteration": i})))
                
                metrics_records.append(metric_id)
            
            # Создаем метрики производительности
            perf_records = []
            for i in range(5):
                perf_id = str(uuid.uuid4())
                perf_type = ["query_time", "connection_count", "cache_hit_rate", "index_usage", "lock_wait_time"][i % 5]
                
                cursor.execute("""
                    INSERT INTO performance_metrics (id, metric_name, metric_value, 
                                                   context, timestamp, created_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (perf_id, perf_type, 
                      round(50 + i * 20 + (i % 2) * 10, 2),
                      json.dumps({"database": "taskweight", "table": f"table_{i}", "operation": "select"})))
                
                perf_records.append(perf_id)
            
            # Проверяем создание метрик
            cursor.execute("SELECT COUNT(*) FROM metrics WHERE tags->>'environment' = 'test'")
            metrics_count = cursor.fetchone()[0]
            
            if metrics_count != 10:
                print(f"❌ Создано {metrics_count} метрик вместо 10")
                return False
            
            # Проверяем создание метрик производительности
            cursor.execute("SELECT COUNT(*) FROM performance_metrics")
            perf_count = cursor.fetchone()[0]
            
            if perf_count < 5:
                print(f"❌ Создано {perf_count} метрик производительности вместо минимум 5")
                return False
            
            # Тестируем агрегацию метрик
            cursor.execute("""
                SELECT name, AVG(value) as avg_value, MAX(value) as max_value, MIN(value) as min_value
                FROM metrics 
                WHERE tags->>'environment' = 'test'
                GROUP BY name
                ORDER BY avg_value DESC
            """)
            
            aggregated_metrics = cursor.fetchall()
            if len(aggregated_metrics) != 5:  # 5 уникальных типов метрик
                print(f"❌ Агрегация метрик не работает, получено {len(aggregated_metrics)} групп")
                return False
            
            # Тестируем временные метрики
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as metric_count
                FROM metrics 
                WHERE tags->>'environment' = 'test'
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            time_metrics = cursor.fetchall()
            if len(time_metrics) != 1:  # Все метрики созданы сегодня
                print(f"❌ Временная группировка метрик не работает")
                return False
            
            # Очищаем тестовые данные
            for record_id in metrics_records:
                cursor.execute("DELETE FROM metrics WHERE id = %s", (record_id,))
            
            for record_id in perf_records:
                cursor.execute("DELETE FROM performance_metrics WHERE id = %s", (record_id,))
            
            print("✅ Тест метрик и производительности пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования метрик: {e}")
            return False

    def run_all_integration_tests(self) -> Dict[str, bool]:
        """Запуск всех тестов интеграций"""
        print("🚀 Запуск тестов интеграций и бизнес-логики...")
        
        if not self.connect_postgres():
            return {"connection": False}
        
        if not self.connect_redis():
            print("⚠️  Redis недоступен, продолжаем без него")
        
        tests = [
            ("webhook_system", self.test_webhook_system),
            ("notification_system", self.test_notification_system),
            ("integration_management", self.test_integration_management),
            ("estimation_workflow", self.test_estimation_workflow),
            ("audit_and_logging", self.test_audit_and_logging),
            ("metrics_and_performance", self.test_metrics_and_performance),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*60}")
                print(f"🧪 Тест: {test_name}")
                print(f"{'='*60}")
                
                start_time = time.time()
                result = test_func()
                test_time = time.time() - start_time
                
                results[test_name] = result
                status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
                print(f"\n{status} за {test_time:.2f} секунд")
                
                self.test_results.append({
                    "test": test_name,
                    "result": result,
                    "time": test_time,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
                results[test_name] = False
                self.test_results.append({
                    "test": test_name,
                    "result": False,
                    "time": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })
        
        return results

    def generate_integration_report(self, results: Dict[str, bool]) -> None:
        """Генерация отчета по интеграциям"""
        print("\n" + "="*80)
        print("📊 ОТЧЕТ ПО ТЕСТИРОВАНИЮ ИНТЕГРАЦИЙ И БИЗНЕС-ЛОГИКИ")
        print("="*80)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Общая статистика:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Пройдено: {passed_tests}")
        print(f"   Провалено: {failed_tests}")
        print(f"   Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n✅ Пройденные тесты:")
        for test_name, result in results.items():
            if result:
                print(f"   • {test_name}")
        
        if failed_tests > 0:
            print(f"\n❌ Проваленные тесты:")
            for test_name, result in results.items():
                if not result:
                    print(f"   • {test_name}")
        
        print(f"\n⏱️  Детальная информация по времени:")
        for test_info in self.test_results:
            status = "✅" if test_info["result"] else "❌"
            print(f"   {status} {test_info['test']}: {test_info['time']:.2f}s")
        
        print(f"\n🎯 Рекомендации:")
        if failed_tests == 0:
            print("   🎉 Все интеграции работают корректно!")
        else:
            print(f"   ⚠️  Необходимо исправить {failed_tests} проваленных тестов.")
            print("   🔧 Проверьте настройки интеграций и webhook'ов.")
        
        print("="*80)

    def cleanup(self):
        """Очистка ресурсов"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.redis_conn:
            self.redis_conn.close()

def main():
    """Главная функция"""
    # Конфигурация базы данных
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'taskweight',
        'user': 'taskweight_user',
        'password': 'taskweight_password',
        'redis_host': 'localhost',
        'redis_port': '6379',
        'redis_password': ''
    }
    
    # Переопределяем конфигурацию из переменных окружения
    import os
    if os.getenv('DB_HOST'):
        db_config['host'] = os.getenv('DB_HOST')
    if os.getenv('DB_PORT'):
        db_config['port'] = os.getenv('DB_PORT')
    if os.getenv('DB_NAME'):
        db_config['database'] = os.getenv('DB_NAME')
    if os.getenv('DB_USER'):
        db_config['user'] = os.getenv('DB_USER')
    if os.getenv('DB_PASSWORD'):
        db_config['password'] = os.getenv('DB_PASSWORD')
    if os.getenv('REDIS_HOST'):
        db_config['redis_host'] = os.getenv('REDIS_HOST')
    if os.getenv('REDIS_PORT'):
        db_config['redis_port'] = os.getenv('REDIS_PORT')
    if os.getenv('REDIS_PASSWORD'):
        db_config['redis_password'] = os.getenv('REDIS_PASSWORD')
    
    tester = IntegrationDatabaseTester(db_config)
    
    try:
        results = tester.run_all_integration_tests()
        tester.generate_integration_report(results)
        
        # Возвращаем код выхода
        if all(results.values()):
            print("\n🎉 Все тесты интеграций пройдены успешно!")
            sys.exit(0)
        else:
            print("\n❌ Некоторые тесты интеграций провалены!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
