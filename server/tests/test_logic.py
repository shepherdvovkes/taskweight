"""
Тесты для бизнес-логики TaskWeight
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.logic.ai_estimator import AIEstimator
from app.db.models import Task, Project, User, EstimationResult

class TestAIEstimator:
    """Тесты для AIEstimator"""
    
    def test_ai_estimator_initialization(self):
        """Тест инициализации AIEstimator"""
        estimator = AIEstimator()
        assert estimator is not None
        assert hasattr(estimator, 'estimate_task')
    
    @patch('app.logic.ai_estimator.openai.ChatCompletion.create')
    def test_estimate_task_success(self, mock_openai):
        """Тест успешной оценки задачи"""
        # Мокаем ответ от OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"estimated_hours": 8.5, "confidence": 0.85, "reasoning": "Medium complexity task"}'
        mock_openai.return_value = mock_response
        
        estimator = AIEstimator()
        task_description = "Create a user authentication system with JWT tokens"
        
        result = estimator.estimate_task(task_description)
        
        assert result is not None
        assert "estimated_hours" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert result["estimated_hours"] == 8.5
        assert result["confidence"] == 0.85
    
    @patch('app.logic.ai_estimator.openai.ChatCompletion.create')
    def test_estimate_task_api_error(self, mock_openai):
        """Тест обработки ошибки API"""
        mock_openai.side_effect = Exception("API Error")
        
        estimator = AIEstimator()
        task_description = "Simple task"
        
        result = estimator.estimate_task(task_description)
        
        assert result is not None
        assert result["error"] == "API Error"
        assert result["estimated_hours"] == 0
        assert result["confidence"] == 0
    
    def test_estimate_task_empty_description(self):
        """Тест оценки задачи с пустым описанием"""
        estimator = AIEstimator()
        
        result = estimator.estimate_task("")
        
        assert result is not None
        assert result["error"] == "Task description cannot be empty"
        assert result["estimated_hours"] == 0
        assert result["confidence"] == 0
    
    def test_estimate_task_very_long_description(self):
        """Тест оценки задачи с очень длинным описанием"""
        estimator = AIEstimator()
        long_description = "A" * 10000  # 10k символов
        
        result = estimator.estimate_task(long_description)
        
        assert result is not None
        assert result["error"] == "Task description too long"
        assert result["estimated_hours"] == 0
        assert result["confidence"] == 0
    
    @patch('app.logic.ai_estimator.openai.ChatCompletion.create')
    def test_estimate_task_invalid_json_response(self, mock_openai):
        """Тест обработки некорректного JSON ответа"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Invalid JSON response'
        mock_openai.return_value = mock_response
        
        estimator = AIEstimator()
        task_description = "Valid task description"
        
        result = estimator.estimate_task(task_description)
        
        assert result is not None
        assert "error" in result
        assert result["estimated_hours"] == 0
        assert result["confidence"] == 0

class TestTaskEstimationLogic:
    """Тесты для логики оценки задач"""
    
    def test_calculate_estimation_accuracy(self):
        """Тест расчета точности оценки"""
        estimated_hours = 8.0
        actual_hours = 7.5
        
        accuracy = self._calculate_accuracy(estimated_hours, actual_hours)
        
        assert accuracy > 0
        assert accuracy <= 100
        # Точность должна быть около 93.75% для этих значений
    
    def test_calculate_estimation_accuracy_zero_actual(self):
        """Тест расчета точности при нулевом фактическом времени"""
        estimated_hours = 8.0
        actual_hours = 0.0
        
        accuracy = self._calculate_accuracy(estimated_hours, actual_hours)
        
        assert accuracy == 0  # Нулевая точность при нулевом фактическом времени
    
    def test_calculate_estimation_accuracy_over_estimation(self):
        """Тест расчета точности при переоценке"""
        estimated_hours = 16.0
        actual_hours = 8.0
        
        accuracy = self._calculate_accuracy(estimated_hours, actual_hours)
        
        assert accuracy < 100  # Точность должна быть меньше 100%
    
    def _calculate_accuracy(self, estimated: float, actual: float) -> float:
        """Вспомогательный метод для расчета точности"""
        if actual == 0:
            return 0.0
        
        error = abs(estimated - actual) / actual
        accuracy = max(0, (1 - error) * 100)
        return round(accuracy, 2)

class TestProjectManagementLogic:
    """Тесты для логики управления проектами"""
    
    def test_calculate_project_progress(self):
        """Тест расчета прогресса проекта"""
        total_tasks = 10
        completed_tasks = 6
        in_progress_tasks = 2
        pending_tasks = 2
        
        progress = self._calculate_progress(completed_tasks, in_progress_tasks, pending_tasks)
        
        assert progress["total"] == total_tasks
        assert progress["completed"] == completed_tasks
        assert progress["in_progress"] == in_progress_tasks
        assert progress["pending"] == pending_tasks
        assert progress["completion_percentage"] == 60.0
    
    def test_calculate_project_progress_no_tasks(self):
        """Тест расчета прогресса проекта без задач"""
        progress = self._calculate_progress(0, 0, 0)
        
        assert progress["total"] == 0
        assert progress["completion_percentage"] == 0.0
    
    def test_calculate_project_progress_all_completed(self):
        """Тест расчета прогресса проекта со всеми выполненными задачами"""
        progress = self._calculate_progress(10, 0, 0)
        
        assert progress["completion_percentage"] == 100.0
    
    def _calculate_progress(self, completed: int, in_progress: int, pending: int) -> dict:
        """Вспомогательный метод для расчета прогресса"""
        total = completed + in_progress + pending
        
        if total == 0:
            completion_percentage = 0.0
        else:
            completion_percentage = (completed / total) * 100
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percentage": round(completion_percentage, 1)
        }

class TestUserActivityLogic:
    """Тесты для логики активности пользователей"""
    
    def test_calculate_user_productivity(self):
        """Тест расчета продуктивности пользователя"""
        tasks_completed = 15
        total_time_spent = 120.5  # часы
        estimated_time = 150.0  # часы
        
        productivity = self._calculate_productivity(tasks_completed, total_time_spent, estimated_time)
        
        assert productivity["tasks_completed"] == tasks_completed
        assert productivity["total_time_spent"] == total_time_spent
        assert productivity["estimated_time"] == estimated_time
        assert productivity["efficiency"] > 0
        assert productivity["tasks_per_hour"] > 0
    
    def test_calculate_user_productivity_no_tasks(self):
        """Тест расчета продуктивности без выполненных задач"""
        productivity = self._calculate_productivity(0, 0, 0)
        
        assert productivity["efficiency"] == 0.0
        assert productivity["tasks_per_hour"] == 0.0
    
    def test_calculate_user_productivity_over_estimated(self):
        """Тест расчета продуктивности при превышении оценок"""
        productivity = self._calculate_productivity(5, 20.0, 15.0)
        
        assert productivity["efficiency"] < 100  # Эффективность должна быть меньше 100%
    
    def _calculate_productivity(self, tasks_completed: int, time_spent: float, estimated_time: float) -> dict:
        """Вспомогательный метод для расчета продуктивности"""
        if tasks_completed == 0 or time_spent == 0:
            efficiency = 0.0
            tasks_per_hour = 0.0
        else:
            efficiency = (estimated_time / time_spent) * 100 if time_spent > 0 else 0
            tasks_per_hour = tasks_completed / time_spent
        
        return {
            "tasks_completed": tasks_completed,
            "total_time_spent": time_spent,
            "estimated_time": estimated_time,
            "efficiency": round(efficiency, 2),
            "tasks_per_hour": round(tasks_per_hour, 2)
        }

class TestNotificationLogic:
    """Тесты для логики уведомлений"""
    
    def test_should_send_notification(self):
        """Тест определения необходимости отправки уведомления"""
        user_preferences = {
            "notifications_enabled": True,
            "email_notifications": True,
            "push_notifications": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }
        
        # Тест в рабочее время
        current_time = datetime.now().replace(hour=14, minute=30)
        should_send = self._should_send_notification(user_preferences, current_time)
        assert should_send is True
        
        # Тест в тихие часы
        current_time = datetime.now().replace(hour=23, minute=30)
        should_send = self._should_send_notification(user_preferences, current_time)
        assert should_send is False
    
    def test_should_send_notification_disabled(self):
        """Тест отключенных уведомлений"""
        user_preferences = {
            "notifications_enabled": False,
            "email_notifications": False,
            "push_notifications": False
        }
        
        current_time = datetime.now()
        should_send = self._should_send_notification(user_preferences, current_time)
        assert should_send is False
    
    def test_should_send_notification_edge_cases(self):
        """Тест граничных случаев для уведомлений"""
        user_preferences = {
            "notifications_enabled": True,
            "quiet_hours_start": "00:00",
            "quiet_hours_end": "23:59"
        }
        
        # Все время - тихие часы
        current_time = datetime.now().replace(hour=12, minute=0)
        should_send = self._should_send_notification(user_preferences, current_time)
        assert should_send is False
    
    def _should_send_notification(self, preferences: dict, current_time: datetime) -> bool:
        """Вспомогательный метод для определения необходимости уведомления"""
        if not preferences.get("notifications_enabled", True):
            return False
        
        # Проверка тихих часов
        if "quiet_hours_start" in preferences and "quiet_hours_end" in preferences:
            start_hour, start_minute = map(int, preferences["quiet_hours_start"].split(":"))
            end_hour, end_minute = map(int, preferences["quiet_hours_end"].split(":"))
            
            current_minutes = current_time.hour * 60 + current_time.minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            if start_minutes <= end_minutes:
                # Обычный случай: 08:00 - 22:00
                if start_minutes <= current_minutes <= end_minutes:
                    return False
            else:
                # Переход через полночь: 22:00 - 08:00
                if current_minutes >= start_minutes or current_minutes <= end_minutes:
                    return False
        
        return True

class TestDataValidationLogic:
    """Тесты для логики валидации данных"""
    
    def test_validate_email_format(self):
        """Тест валидации формата email"""
        valid_emails = [
            "user@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com"
        ]
        
        for email in valid_emails:
            assert self._is_valid_email(email) is True
        
        for email in invalid_emails:
            assert self._is_valid_email(email) is False
    
    def test_validate_password_strength(self):
        """Тест валидации силы пароля"""
        strong_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "Str0ng#Pass"
        ]
        
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty"
        ]
        
        for password in strong_passwords:
            assert self._is_strong_password(password) is True
        
        for password in weak_passwords:
            assert self._is_strong_password(password) is False
    
    def test_validate_task_data(self):
        """Тест валидации данных задачи"""
        valid_task = {
            "title": "Valid Task",
            "description": "Valid description",
            "priority": "high",
            "status": "todo"
        }
        
        invalid_task = {
            "title": "",  # Пустой заголовок
            "description": "Valid description",
            "priority": "invalid_priority",  # Неверный приоритет
            "status": "invalid_status"  # Неверный статус
        }
        
        assert self._validate_task_data(valid_task) == {"valid": True, "errors": []}
        
        validation_result = self._validate_task_data(invalid_task)
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
    
    def _is_valid_email(self, email: str) -> bool:
        """Вспомогательный метод для валидации email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_strong_password(self, password: str) -> bool:
        """Вспомогательный метод для валидации пароля"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _validate_task_data(self, task_data: dict) -> dict:
        """Вспомогательный метод для валидации данных задачи"""
        errors = []
        
        if not task_data.get("title", "").strip():
            errors.append("Title cannot be empty")
        
        valid_priorities = ["low", "medium", "high", "critical"]
        if task_data.get("priority") not in valid_priorities:
            errors.append(f"Priority must be one of: {', '.join(valid_priorities)}")
        
        valid_statuses = ["todo", "in_progress", "review", "done", "blocked"]
        if task_data.get("status") not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
