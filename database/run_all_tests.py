#!/usr/bin/env python3
"""
TaskWeight Master Test Runner
Запускает все тесты базы данных и генерирует сводный отчет
"""

import sys
import time
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any

class MasterTestRunner:
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_test_suite(self, test_file: str, description: str) -> Dict[str, Any]:
        """Запуск тестового набора"""
        print(f"\n{'='*80}")
        print(f"🚀 ЗАПУСК: {description}")
        print(f"📁 Файл: {test_file}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Запускаем тест как подпроцесс
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300  # 5 минут на каждый набор тестов
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            print(f"⏱️  Время выполнения: {duration:.2f} секунд")
            print(f"📊 Код выхода: {result.returncode}")
            
            if success:
                print("✅ Тестовый набор завершен успешно")
            else:
                print("❌ Тестовый набор завершен с ошибками")
                if result.stderr:
                    print(f"⚠️  Ошибки:\n{result.stderr}")
            
            return {
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "description": description
            }
            
        except subprocess.TimeoutExpired:
            print("⏰ Тестовый набор превысил лимит времени (5 минут)")
            return {
                "success": False,
                "duration": 300,
                "return_code": -1,
                "stdout": "",
                "stderr": "Timeout exceeded",
                "description": description
            }
        except Exception as e:
            print(f"💥 Ошибка запуска тестов: {e}")
            return {
                "success": False,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "description": description
            }
    
    def run_pytest_suite(self, test_file: str, description: str) -> Dict[str, Any]:
        """Запуск pytest тестового набора"""
        print(f"\n{'='*80}")
        print(f"🚀 ЗАПУСК PYTEST: {description}")
        print(f"📁 Файл: {test_file}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Запускаем pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=600  # 10 минут на pytest тесты
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # pytest возвращает 0 при успехе, 1 при наличии ошибок
            success = result.returncode == 0
            
            print(f"⏱️  Время выполнения: {duration:.2f} секунд")
            print(f"📊 Код выхода: {result.returncode}")
            
            if success:
                print("✅ Pytest тестовый набор завершен успешно")
            else:
                print("❌ Pytest тестовый набор завершен с ошибками")
                if result.stderr:
                    print(f"⚠️  Ошибки:\n{result.stderr}")
            
            return {
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "description": description,
                "type": "pytest"
            }
            
        except subprocess.TimeoutExpired:
            print("⏰ Pytest тестовый набор превысил лимит времени (10 минут)")
            return {
                "success": False,
                "duration": 600,
                "return_code": -1,
                "stdout": "",
                "stderr": "Timeout exceeded",
                "description": description,
                "type": "pytest"
            }
        except Exception as e:
            print(f"💥 Ошибка запуска pytest тестов: {e}")
            return {
                "success": False,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "description": description,
                "type": "pytest"
            }
    
    def run_all_test_suites(self) -> Dict[str, Any]:
        """Запуск всех тестовых наборов"""
        print("🎯 ЗАПУСК ВСЕХ ТЕСТОВ БАЗЫ ДАННЫХ TASKWEIGHT")
        print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # Определяем тестовые наборы
        test_suites = [
            ("test_database.py", "Основные тесты базы данных"),
            ("test_database_advanced.py", "Расширенные тесты производительности"),
            ("test_database_comprehensive.py", "Комплексные тесты функциональности"),
            ("test_database_integrations.py", "Тесты интеграций и бизнес-логики")
        ]
        
        # Определяем pytest тестовые наборы
        pytest_suites = [
            ("test_pytest_database.py", "Современные pytest тесты"),
            ("test_migrations.py", "Тесты миграций и схемы"),
            ("test_security_performance.py", "Тесты безопасности и производительности")
        ]
        
        # Проверяем наличие всех файлов
        missing_files = []
        for test_file, description in test_suites + pytest_suites:
            if not os.path.exists(test_file):
                missing_files.append(test_file)
        
        if missing_files:
            print(f"⚠️  Отсутствуют файлы тестов: {missing_files}")
            return {}
        
        # Запускаем обычные тесты
        for test_file, description in test_suites:
            result = self.run_test_suite(test_file, description)
            self.test_results[description] = result
        
        # Запускаем pytest тесты
        for test_file, description in pytest_suites:
            result = self.run_pytest_suite(test_file, description)
            self.test_results[description] = result
        
        self.end_time = time.time()
        return self.test_results
    
    def generate_master_report(self) -> None:
        """Генерация сводного отчета"""
        if not self.test_results:
            print("❌ Нет результатов тестов для отчета")
            return
        
        print(f"\n{'='*80}")
        print("📊 СВОДНЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        total_duration = sum(result["duration"] for result in self.test_results.values())
        
        print(f"📈 Общее количество тестовых наборов: {total_tests}")
        print(f"✅ Успешных: {successful_tests}")
        print(f"❌ Неудачных: {failed_tests}")
        print(f"⏱️  Общее время выполнения: {total_duration:.2f} секунд")
        
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            print(f"🕐 Общее время (включая накладные расходы): {total_time:.2f} секунд")
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"📊 Процент успеха: {success_rate:.1f}%")
        
        # Детальный отчет по каждому тесту
        print(f"\n{'='*80}")
        print("📋 ДЕТАЛЬНЫЙ ОТЧЕТ")
        print(f"{'='*80}")
        
        for description, result in self.test_results.items():
            status = "✅ УСПЕХ" if result["success"] else "❌ ОШИБКА"
            test_type = result.get("type", "обычный")
            print(f"{status} | {description} ({test_type}) | {result['duration']:.2f}с")
            
            if not result["success"] and result["stderr"]:
                print(f"   ⚠️  Ошибка: {result['stderr'][:200]}...")
        
        # Рекомендации
        print(f"\n{'='*80}")
        print("💡 РЕКОМЕНДАЦИИ")
        print(f"{'='*80}")
        
        if success_rate == 100:
            print("🎉 Отлично! Все тесты прошли успешно.")
            print("   База данных полностью готова к работе.")
        elif success_rate >= 80:
            print("⚠️  Хорошо, но есть проблемы для исправления.")
            print("   Проверьте логи и исправьте ошибки.")
        else:
            print("❌ Критические проблемы в тестах.")
            print("   Требуется немедленное внимание и исправление.")
        
        if failed_tests > 0:
            print(f"\n🔍 Проверьте следующие тестовые наборы:")
            for description, result in self.test_results.items():
                if not result["success"]:
                    print(f"   - {description}")
    
    def save_detailed_report(self, filename: str = "test_report_detailed.txt") -> None:
        """Сохранение детального отчета в файл"""
        if not self.test_results:
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("TaskWeight Database Test Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for description, result in self.test_results.items():
                f.write(f"Тест: {description}\n")
                f.write(f"Статус: {'УСПЕХ' if result['success'] else 'ОШИБКА'}\n")
                f.write(f"Время: {result['duration']:.2f} секунд\n")
                f.write(f"Тип: {result.get('type', 'обычный')}\n")
                
                if result["stdout"]:
                    f.write(f"Вывод:\n{result['stdout']}\n")
                
                if result["stderr"]:
                    f.write(f"Ошибки:\n{result['stderr']}\n")
                
                f.write("-" * 30 + "\n\n")
        
        print(f"📄 Детальный отчет сохранен в файл: {filename}")

def main():
    """Главная функция"""
    runner = MasterTestRunner()
    
    try:
        # Запускаем все тесты
        results = runner.run_all_test_suites()
        
        if results:
            # Генерируем отчет
            runner.generate_master_report()
            
            # Сохраняем детальный отчет
            runner.save_detailed_report()
            
            # Определяем общий статус
            all_success = all(result["success"] for result in results.values())
            exit_code = 0 if all_success else 1
            
            print(f"\n🎯 Общий статус: {'УСПЕХ' if all_success else 'ОШИБКА'}")
            print(f"🚪 Выход с кодом: {exit_code}")
            
            sys.exit(exit_code)
        else:
            print("❌ Не удалось запустить тесты")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
