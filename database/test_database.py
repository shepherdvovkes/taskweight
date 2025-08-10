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
            'get_metrics', 'create_notification', 'get_pending_notifications'
        ]
        
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute("""
                SELECT proname 
                FROM pg_proc p 
                JOIN pg_namespace n ON p.pronamespace = n.oid 
                WHERE n.nspname = 'public' 
                AND proname IN ('update_updated_at_column', 'search_tasks', 'record_metric')
            """)
            
            existing_functions = [row[0] for row in cursor.fetchall()]
            missing_functions = set(expected_functions[:3]) - set(existing_functions)
            
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
            ("Целостность данных", self.test_data_integrity)
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
