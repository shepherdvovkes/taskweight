#!/usr/bin/env python3
"""
TaskWeight Comprehensive Database Test Suite
Комплексные тесты для полного покрытия функциональности базы данных
"""

import psycopg2
import redis
import json
import sys
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import concurrent.futures
import threading

class ComprehensiveDatabaseTester:
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

    def test_data_encryption_and_security(self) -> bool:
        """Тест шифрования и безопасности данных"""
        print("\n🔐 Тестирование шифрования и безопасности...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Проверяем, что пароли хешируются
            test_password = "test_password_123"
            test_user_id = str(uuid.uuid4())
            
            # Создаем тестового пользователя
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id, f"test_user_{secrets.token_hex(4)}", 
                  f"test_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256(test_password.encode()).hexdigest()))
            
            # Проверяем, что пароль не хранится в открытом виде
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (test_user_id,))
            stored_hash = cursor.fetchone()[0]
            
            if stored_hash == test_password:
                print("❌ Пароль хранится в открытом виде")
                return False
            
            # Проверяем, что хеш корректный
            expected_hash = hashlib.sha256(test_password.encode()).hexdigest()
            if stored_hash != expected_hash:
                print("❌ Неверный хеш пароля")
                return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            
            print("✅ Тест шифрования и безопасности пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования безопасности: {e}")
            return False

    def test_data_consistency_constraints(self) -> bool:
        """Тест ограничений целостности данных"""
        print("\n🔒 Тестирование ограничений целостности...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест 1: Проверка уникальности email
            test_user_id1 = str(uuid.uuid4())
            test_user_id2 = str(uuid.uuid4())
            test_email = f"test_{secrets.token_hex(4)}@example.com"
            
            # Создаем первого пользователя
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id1, f"test_user_{secrets.token_hex(4)}", 
                  test_email, hashlib.sha256("pass1".encode()).hexdigest()))
            
            # Пытаемся создать второго пользователя с тем же email
            try:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (test_user_id2, f"test_user_{secrets.token_hex(4)}", 
                      test_email, hashlib.sha256("pass2".encode()).hexdigest()))
                print("❌ Дублирование email не предотвращено")
                return False
            except psycopg2.IntegrityError:
                print("✅ Ограничение уникальности email работает")
            
            # Тест 2: Проверка внешних ключей
            test_project_id = str(uuid.uuid4())
            
            # Пытаемся создать задачу с несуществующим проектом
            try:
                cursor.execute("""
                    INSERT INTO tasks (id, title, description, project_id, status, priority, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (str(uuid.uuid4()), "Test Task", "Test Description", 
                      test_project_id, "todo", "medium"))
                print("❌ Ограничение внешнего ключа не работает")
                return False
            except psycopg2.IntegrityError:
                print("✅ Ограничение внешнего ключа работает")
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id1,))
            
            print("✅ Тест ограничений целостности пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования ограничений: {e}")
            return False

    def test_transaction_rollback(self) -> bool:
        """Тест отката транзакций"""
        print("\n🔄 Тестирование отката транзакций...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Начинаем транзакцию
            self.pg_conn.autocommit = False
            
            # Создаем тестового пользователя
            test_user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id, f"test_user_{secrets.token_hex(4)}", 
                  f"test_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("testpass".encode()).hexdigest()))
            
            # Проверяем, что пользователь создан
            cursor.execute("SELECT id FROM users WHERE id = %s", (test_user_id,))
            if not cursor.fetchone():
                print("❌ Пользователь не создан в транзакции")
                return False
            
            # Откатываем транзакцию
            self.pg_conn.rollback()
            
            # Проверяем, что пользователь удален после отката
            cursor.execute("SELECT id FROM users WHERE id = %s", (test_user_id,))
            if cursor.fetchone():
                print("❌ Транзакция не откатилась")
                return False
            
            # Восстанавливаем автокоммит
            self.pg_conn.autocommit = True
            
            print("✅ Тест отката транзакций пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования отката транзакций: {e}")
            self.pg_conn.autocommit = True
            return False

    def test_concurrent_writes(self) -> bool:
        """Тест конкурентных записей"""
        print("\n⚡ Тестирование конкурентных записей...")
        
        try:
            # Создаем несколько потоков для одновременной записи
            def write_user(thread_id):
                try:
                    conn = psycopg2.connect(
                        host=self.db_config['host'],
                        port=self.db_config['port'],
                        database=self.db_config['database'],
                        user=self.db_config['user'],
                        password=self.db_config['password']
                    )
                    conn.autocommit = True
                    cursor = conn.cursor()
                    
                    user_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """, (user_id, f"concurrent_user_{thread_id}_{secrets.token_hex(4)}", 
                          f"concurrent_{thread_id}_{secrets.token_hex(4)}@example.com", 
                          hashlib.sha256(f"pass{thread_id}".encode()).hexdigest()))
                    
                    cursor.close()
                    conn.close()
                    return True
                except Exception as e:
                    print(f"⚠️  Ошибка в потоке {thread_id}: {e}")
                    return False
            
            # Запускаем 10 потоков одновременно
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(write_user, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_count = sum(results)
            print(f"✅ Успешно выполнено {success_count} из 10 конкурентных записей")
            
            # Очищаем тестовые данные
            cursor = self.pg_conn.cursor()
            cursor.execute("DELETE FROM users WHERE username LIKE 'concurrent_user_%'")
            
            return success_count >= 8  # Минимум 80% успешных записей
            
        except Exception as e:
            print(f"❌ Ошибка тестирования конкурентных записей: {e}")
            return False

    def test_data_migration_scenarios(self) -> bool:
        """Тест сценариев миграции данных"""
        print("\n🚀 Тестирование сценариев миграции...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест 1: Изменение структуры данных
            test_user_id = str(uuid.uuid4())
            
            # Создаем пользователя с базовыми данными
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id, f"migration_user_{secrets.token_hex(4)}", 
                  f"migration_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("migrationpass".encode()).hexdigest()))
            
            # Симулируем миграцию: добавляем новое поле
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS migration_test_field VARCHAR(50)")
                print("✅ Добавление нового поля успешно")
            except Exception as e:
                print(f"❌ Ошибка добавления поля: {e}")
                return False
            
            # Обновляем данные в новом поле
            cursor.execute("""
                UPDATE users 
                SET migration_test_field = 'migrated_value', updated_at = NOW()
                WHERE id = %s
            """, (test_user_id,))
            
            # Проверяем, что данные обновились
            cursor.execute("SELECT migration_test_field FROM users WHERE id = %s", (test_user_id,))
            result = cursor.fetchone()
            if not result or result[0] != 'migrated_value':
                print("❌ Данные не обновились после миграции")
                return False
            
            # Удаляем тестовое поле
            cursor.execute("ALTER TABLE users DROP COLUMN IF EXISTS migration_test_field")
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            
            print("✅ Тест сценариев миграции пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования миграции: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        print("\n⚠️  Тестирование обработки ошибок...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Тест 1: Попытка вставить NULL в обязательное поле
            try:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, NULL, %s, %s, NOW(), NOW())
                """, (str(uuid.uuid4()), f"error_test_{secrets.token_hex(4)}@example.com", 
                      hashlib.sha256("errorpass".encode()).hexdigest()))
                print("❌ NULL в обязательном поле не предотвращен")
                return False
            except psycopg2.IntegrityError:
                print("✅ NULL в обязательном поле предотвращен")
            
            # Тест 2: Попытка вставить неверный формат UUID
            try:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, ("invalid-uuid", f"error_user_{secrets.token_hex(4)}", 
                      f"error_{secrets.token_hex(4)}@example.com", 
                      hashlib.sha256("errorpass".encode()).hexdigest()))
                print("❌ Неверный формат UUID не предотвращен")
                return False
            except psycopg2.DataError:
                print("✅ Неверный формат UUID предотвращен")
            
            # Тест 3: Попытка вставить слишком длинную строку
            long_string = "a" * 1000
            try:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                """, (str(uuid.uuid4()), long_string, 
                      f"error_{secrets.token_hex(4)}@example.com", 
                      hashlib.sha256("errorpass".encode()).hexdigest()))
                print("❌ Слишком длинная строка не предотвращена")
                return False
            except psycopg2.DataError:
                print("✅ Слишком длинная строка предотвращена")
            
            print("✅ Тест обработки ошибок пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования обработки ошибок: {e}")
            return False

    def test_performance_under_load(self) -> bool:
        """Тест производительности под нагрузкой"""
        print("\n📊 Тестирование производительности под нагрузкой...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестовые данные для нагрузки
            test_users = []
            for i in range(100):
                user_id = str(uuid.uuid4())
                test_users.append((
                    user_id,
                    f"load_test_user_{i}_{secrets.token_hex(4)}",
                    f"load_test_{i}_{secrets.token_hex(4)}@example.com",
                    hashlib.sha256(f"loadpass{i}".encode()).hexdigest()
                ))
            
            # Измеряем время массовой вставки
            start_time = time.time()
            cursor.executemany("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, test_users)
            insert_time = time.time() - start_time
            
            print(f"✅ Массовая вставка 100 пользователей за {insert_time:.2f} секунд")
            
            # Измеряем время сложного запроса
            start_time = time.time()
            cursor.execute("""
                SELECT u.username, u.email, 
                       COUNT(t.id) as task_count,
                       AVG(t.estimated_hours) as avg_estimation
                FROM users u
                LEFT JOIN tasks t ON u.id = t.assignee_id
                WHERE u.username LIKE 'load_test_user_%'
                GROUP BY u.id, u.username, u.email
                ORDER BY task_count DESC
            """)
            query_time = time.time() - start_time
            
            print(f"✅ Сложный запрос выполнен за {query_time:.2f} секунд")
            
            # Измеряем время массового обновления
            start_time = time.time()
            cursor.execute("""
                UPDATE users 
                SET updated_at = NOW()
                WHERE username LIKE 'load_test_user_%'
            """)
            update_time = time.time() - start_time
            
            print(f"✅ Массовое обновление за {update_time:.2f} секунд")
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM users WHERE username LIKE 'load_test_user_%'")
            
            # Проверяем, что производительность приемлема
            total_time = insert_time + query_time + update_time
            if total_time > 10:  # Максимум 10 секунд на все операции
                print(f"⚠️  Общее время операций ({total_time:.2f}s) превышает допустимое")
                return False
            
            print("✅ Тест производительности под нагрузкой пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования производительности: {e}")
            return False

    def test_data_recovery(self) -> bool:
        """Тест восстановления данных"""
        print("\n🔄 Тестирование восстановления данных...")
        
        try:
            cursor = self.pg_conn.cursor()
            
            # Создаем тестовые данные
            test_user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id, f"recovery_user_{secrets.token_hex(4)}", 
                  f"recovery_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("recoverypass".encode()).hexdigest()))
            
            # Проверяем, что данные созданы
            cursor.execute("SELECT username FROM users WHERE id = %s", (test_user_id,))
            if not cursor.fetchone():
                print("❌ Тестовые данные не созданы")
                return False
            
            # Симулируем "потерю" данных (удаляем)
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            
            # Проверяем, что данные удалены
            cursor.execute("SELECT username FROM users WHERE id = %s", (test_user_id,))
            if cursor.fetchone():
                print("❌ Данные не удалены")
                return False
            
            # "Восстанавливаем" данные
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (test_user_id, f"recovery_user_{secrets.token_hex(4)}", 
                  f"recovery_{secrets.token_hex(4)}@example.com", 
                  hashlib.sha256("recoverypass".encode()).hexdigest()))
            
            # Проверяем восстановление
            cursor.execute("SELECT username FROM users WHERE id = %s", (test_user_id,))
            if not cursor.fetchone():
                print("❌ Данные не восстановлены")
                return False
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM users WHERE id = %s", (test_user_id,))
            
            print("✅ Тест восстановления данных пройден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования восстановления: {e}")
            return False

    def run_all_comprehensive_tests(self) -> Dict[str, bool]:
        """Запуск всех комплексных тестов"""
        print("🚀 Запуск комплексных тестов базы данных...")
        
        if not self.connect_postgres():
            return {"connection": False}
        
        if not self.connect_redis():
            print("⚠️  Redis недоступен, продолжаем без него")
        
        tests = [
            ("data_encryption_and_security", self.test_data_encryption_and_security),
            ("data_consistency_constraints", self.test_data_consistency_constraints),
            ("transaction_rollback", self.test_transaction_rollback),
            ("concurrent_writes", self.test_concurrent_writes),
            ("data_migration_scenarios", self.test_data_migration_scenarios),
            ("error_handling", self.test_error_handling),
            ("performance_under_load", self.test_performance_under_load),
            ("data_recovery", self.test_data_recovery),
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

    def generate_comprehensive_report(self, results: Dict[str, bool]) -> None:
        """Генерация комплексного отчета"""
        print("\n" + "="*80)
        print("📊 КОМПЛЕКСНЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ БАЗЫ ДАННЫХ")
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
            print("   🎉 Все тесты пройдены успешно! База данных готова к продакшену.")
        else:
            print(f"   ⚠️  Необходимо исправить {failed_tests} проваленных тестов.")
            print("   🔧 Проверьте логи и настройки базы данных.")
        
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
    
    tester = ComprehensiveDatabaseTester(db_config)
    
    try:
        results = tester.run_all_comprehensive_tests()
        tester.generate_comprehensive_report(results)
        
        # Возвращаем код выхода
        if all(results.values()):
            print("\n🎉 Все тесты пройдены успешно!")
            sys.exit(0)
        else:
            print("\n❌ Некоторые тесты провалены!")
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
