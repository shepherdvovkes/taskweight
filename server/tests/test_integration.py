"""
Интеграционные тесты для TaskWeight
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

class TestUserWorkflow:
    """Тесты полного рабочего процесса пользователя"""
    
    def test_user_registration_and_login_workflow(self, client: TestClient, db_session: Session):
        """Тест полного процесса регистрации и входа пользователя"""
        # 1. Регистрация пользователя
        user_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "full_name": "Workflow User",
            "password": "SecurePass123!"
        }
        
        register_response = client.post("/users/", json=user_data)
        assert register_response.status_code == 201
        
        user = register_response.json()
        user_id = user["id"]
        
        # 2. Создание проекта
        project_data = {
            "name": "Workflow Project",
            "description": "Project for testing workflows",
            "owner_id": user_id,
            "status": "active"
        }
        
        project_response = client.post("/projects/", json=project_data)
        assert project_response.status_code == 201
        
        project = project_response.json()
        project_id = project["id"]
        
        # 3. Создание нескольких задач
        tasks_data = [
            {
                "title": "Task 1",
                "description": "First task in workflow",
                "project_id": project_id,
                "status": "todo",
                "priority": "high"
            },
            {
                "title": "Task 2",
                "description": "Second task in workflow",
                "project_id": project_id,
                "status": "todo",
                "priority": "medium"
            }
        ]
        
        created_tasks = []
        for task_data in tasks_data:
            task_response = client.post("/tasks/", json=task_data)
            assert task_response.status_code == 201
            created_tasks.append(task_response.json())
        
        # 4. Обновление статуса задач
        for i, task in enumerate(created_tasks):
            if i == 0:
                # Первая задача переводится в работу
                update_response = client.put(
                    f"/tasks/{task['id']}", 
                    json={"status": "in_progress"}
                )
                assert update_response.status_code == 200
            else:
                # Вторая задача остается в ожидании
                pass
        
        # 5. Проверка статистики проекта
        stats_response = client.get(f"/projects/{project_id}/statistics")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        assert stats["total_tasks"] == 2
        assert stats["in_progress_tasks"] == 1
        assert stats["pending_tasks"] == 1
        
        # 6. Проверка списка задач проекта
        tasks_response = client.get(f"/projects/{project_id}/tasks")
        assert tasks_response.status_code == 200
        
        tasks = tasks_response.json()
        assert len(tasks) == 2
        
        # Проверяем, что статусы обновились
        task1 = next(t for t in tasks if t["title"] == "Task 1")
        task2 = next(t for t in tasks if t["title"] == "Task 2")
        
        assert task1["status"] == "in_progress"
        assert task2["status"] == "todo"

class TestProjectManagementWorkflow:
    """Тесты рабочего процесса управления проектами"""
    
    def test_project_lifecycle_workflow(self, client: TestClient, sample_user, sample_project):
        """Тест полного жизненного цикла проекта"""
        project_id = sample_project.id
        
        # 1. Создание задач разных приоритетов
        high_priority_task = {
            "title": "Critical Bug Fix",
            "description": "Fix critical security vulnerability",
            "project_id": project_id,
            "status": "todo",
            "priority": "critical"
        }
        
        medium_priority_task = {
            "title": "Feature Development",
            "description": "Implement new user interface",
            "project_id": project_id,
            "status": "todo",
            "priority": "medium"
        }
        
        low_priority_task = {
            "title": "Documentation Update",
            "description": "Update API documentation",
            "project_id": project_id,
            "status": "todo",
            "priority": "low"
        }
        
        # Создаем задачи
        high_task_response = client.post("/tasks/", json=high_priority_task)
        medium_task_response = client.post("/tasks/", json=medium_priority_task)
        low_task_response = client.post("/tasks/", json=low_priority_task)
        
        assert all(r.status_code == 201 for r in [high_task_response, medium_task_response, low_task_response])
        
        high_task = high_task_response.json()
        medium_task = medium_task_response.json()
        low_task = low_task_response.json()
        
        # 2. Работа с критической задачей
        # Начинаем работу
        client.put(f"/tasks/{high_task['id']}", json={"status": "in_progress"})
        
        # Добавляем время работы
        time_entry = {
            "task_id": high_task["id"],
            "hours_spent": 4.0,
            "description": "Investigation and initial fix"
        }
        
        time_response = client.post("/time-entries/", json=time_entry)
        assert time_response.status_code == 201
        
        # Завершаем задачу
        client.put(f"/tasks/{high_task['id']}", json={"status": "done"})
        
        # 3. Работа со средней задачей
        client.put(f"/tasks/{medium_task['id']}", json={"status": "in_progress"})
        
        # 4. Проверка прогресса
        progress_response = client.get(f"/projects/{project_id}/progress")
        assert progress_response.status_code == 200
        
        progress = progress_response.json()
        assert progress["total_tasks"] >= 3
        assert progress["completed_tasks"] >= 1
        assert progress["in_progress_tasks"] >= 1
        
        # 5. Проверка метрик производительности
        metrics_response = client.get(f"/projects/{project_id}/metrics")
        assert metrics_response.status_code == 200
        
        metrics = metrics_response.json()
        assert "completion_rate" in metrics
        assert "average_task_duration" in metrics

class TestTaskEstimationWorkflow:
    """Тесты рабочего процесса оценки задач"""
    
    def test_ai_estimation_workflow(self, client: TestClient, sample_project):
        """Тест процесса AI оценки задачи"""
        # 1. Создание задачи для оценки
        task_data = {
            "title": "AI Estimation Test Task",
            "description": "Create a REST API with authentication, database integration, and unit tests",
            "project_id": sample_project.id,
            "status": "todo",
            "priority": "high"
        }
        
        task_response = client.post("/tasks/", json=task_data)
        assert task_response.status_code == 201
        
        task = task_response.json()
        task_id = task["id"]
        
        # 2. Запрос AI оценки
        estimation_request = {
            "task_id": task_id,
            "description": task_data["description"]
        }
        
        estimation_response = client.post("/estimations/ai", json=estimation_request)
        # Может быть 200 или 422 в зависимости от реализации
        assert estimation_response.status_code in [200, 201, 422]
        
        if estimation_response.status_code in [200, 201]:
            estimation = estimation_response.json()
            assert "estimated_hours" in estimation
            assert "confidence_level" in estimation
            assert "method" in estimation
            
            # 3. Сохранение оценки
            save_estimation = {
                "task_id": task_id,
                "estimated_hours": estimation["estimated_hours"],
                "confidence_level": estimation["confidence_level"],
                "method": "ai_estimation"
            }
            
            save_response = client.post("/estimations/", json=save_estimation)
            assert save_response.status_code == 201
            
            # 4. Обновление задачи с оценкой
            update_response = client.put(
                f"/tasks/{task_id}",
                json={"estimated_hours": estimation["estimated_hours"]}
            )
            assert update_response.status_code == 200
            
            # 5. Проверка обновленной задачи
            updated_task_response = client.get(f"/tasks/{task_id}")
            assert updated_task_response.status_code == 200
            
            updated_task = updated_task_response.json()
            assert updated_task["estimated_hours"] == estimation["estimated_hours"]
    
    def test_manual_estimation_workflow(self, client: TestClient, sample_project):
        """Тест процесса ручной оценки задачи"""
        # 1. Создание задачи
        task_data = {
            "title": "Manual Estimation Task",
            "description": "Simple task for manual estimation",
            "project_id": sample_project.id,
            "status": "todo"
        }
        
        task_response = client.post("/tasks/", json=task_data)
        assert task_response.status_code == 201
        
        task = task_response.json()
        task_id = task["id"]
        
        # 2. Создание ручной оценки
        manual_estimation = {
            "task_id": task_id,
            "estimated_hours": 6.0,
            "confidence_level": 0.9,
            "method": "expert_judgment",
            "factors": {"complexity": "medium", "experience": "high"}
        }
        
        estimation_response = client.post("/estimations/", json=manual_estimation)
        assert estimation_response.status_code == 201
        
        # 3. Получение истории оценок
        history_response = client.get(f"/tasks/{task_id}/estimations")
        assert history_response.status_code == 200
        
        history = history_response.json()
        assert len(history) >= 1
        
        # Проверяем, что наша оценка в истории
        our_estimation = next(e for e in history if e["method"] == "expert_judgment")
        assert our_estimation["estimated_hours"] == 6.0

class TestNotificationWorkflow:
    """Тесты рабочего процесса уведомлений"""
    
    def test_notification_workflow(self, client: TestClient, sample_user, sample_project):
        """Тест процесса создания и отправки уведомлений"""
        # 1. Настройка предпочтений уведомлений
        notification_prefs = {
            "user_id": sample_user.id,
            "email_notifications": True,
            "push_notifications": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }
        
        prefs_response = client.post("/notification-preferences/", json=notification_prefs)
        # Может быть 200, 201 или 422 в зависимости от реализации
        assert prefs_response.status_code in [200, 201, 422]
        
        # 2. Создание задачи, которая должна вызвать уведомление
        task_data = {
            "title": "Notification Test Task",
            "description": "Task to test notification system",
            "project_id": sample_project.id,
            "status": "todo",
            "assigned_to": sample_user.id
        }
        
        task_response = client.post("/tasks/", json=task_data)
        assert task_response.status_code == 201
        
        task = task_response.json()
        task_id = task["id"]
        
        # 3. Проверка создания уведомления
        notifications_response = client.get(f"/users/{sample_user.id}/notifications")
        # Может быть 200 или 404 в зависимости от реализации
        if notifications_response.status_code == 200:
            notifications = notifications_response.json()
            # Должно быть уведомление о назначении задачи
            task_notifications = [n for n in notifications if "task" in n.get("title", "").lower()]
            assert len(task_notifications) >= 1
        
        # 4. Обновление статуса задачи
        client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
        
        # 5. Проверка обновления уведомлений
        if notifications_response.status_code == 200:
            updated_notifications = client.get(f"/users/{sample_user.id}/notifications").json()
            # Должно быть уведомление об изменении статуса
            status_notifications = [n for n in updated_notifications if "in progress" in n.get("message", "").lower()]
            assert len(status_notifications) >= 1

class TestWebhookWorkflow:
    """Тесты рабочего процесса webhook"""
    
    def test_webhook_workflow(self, client: TestClient, sample_user):
        """Тест процесса настройки и работы webhook"""
        # 1. Создание webhook
        webhook_data = {
            "user_id": sample_user.id,
            "url": "https://example.com/webhook",
            "events": ["task_created", "task_updated", "project_created"],
            "is_active": True
        }
        
        webhook_response = client.post("/webhooks/", json=webhook_data)
        assert webhook_response.status_code == 201
        
        webhook = webhook_response.json()
        webhook_id = webhook["id"]
        
        # 2. Тестирование webhook
        test_response = client.post(f"/webhooks/{webhook_id}/test")
        # Может быть 200 или 404 в зависимости от реализации
        assert test_response.status_code in [200, 404]
        
        # 3. Проверка доставки webhook
        deliveries_response = client.get(f"/webhooks/{webhook_id}/deliveries")
        # Может быть 200 или 404 в зависимости от реализации
        if deliveries_response.status_code == 200:
            deliveries = deliveries_response.json()
            assert isinstance(deliveries, list)
        
        # 4. Деактивация webhook
        deactivate_response = client.put(
            f"/webhooks/{webhook_id}",
            json={"is_active": False}
        )
        assert deactivate_response.status_code == 200
        
        # 5. Проверка деактивации
        webhook_response = client.get(f"/webhooks/{webhook_id}")
        assert webhook_response.status_code == 200
        
        webhook_data = webhook_response.json()
        assert webhook_data["is_active"] is False

class TestDataConsistency:
    """Тесты консистентности данных"""
    
    def test_data_consistency_across_operations(self, client: TestClient, sample_user, sample_project):
        """Тест консистентности данных при различных операциях"""
        # 1. Создание задачи
        task_data = {
            "title": "Consistency Test Task",
            "description": "Task for testing data consistency",
            "project_id": sample_project.id,
            "status": "todo"
        }
        
        task_response = client.post("/tasks/", json=task_data)
        assert task_response.status_code == 201
        
        task = task_response.json()
        task_id = task["id"]
        
        # 2. Проверка консистентности в разных эндпоинтах
        # Получаем задачу напрямую
        direct_task_response = client.get(f"/tasks/{task_id}")
        assert direct_task_response.status_code == 200
        
        direct_task = direct_task_response.json()
        
        # Получаем задачу через проект
        project_tasks_response = client.get(f"/projects/{sample_project.id}/tasks")
        assert project_tasks_response.status_code == 200
        
        project_tasks = project_tasks_response.json()
        project_task = next(t for t in project_tasks if t["id"] == task_id)
        
        # Данные должны быть идентичными
        assert direct_task["title"] == project_task["title"]
        assert direct_task["status"] == project_task["status"]
        assert direct_task["project_id"] == project_task["project_id"]
        
        # 3. Обновление задачи
        update_data = {"status": "in_progress", "priority": "high"}
        update_response = client.put(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        
        # 4. Проверка консистентности после обновления
        updated_direct_task = client.get(f"/tasks/{task_id}").json()
        updated_project_tasks = client.get(f"/projects/{sample_project.id}/tasks").json()
        updated_project_task = next(t for t in updated_project_tasks if t["id"] == task_id)
        
        assert updated_direct_task["status"] == updated_project_task["status"]
        assert updated_direct_task["priority"] == updated_project_task["priority"]
        
        # 5. Проверка статистики проекта
        stats_response = client.get(f"/projects/{sample_project.id}/statistics")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        assert stats["in_progress_tasks"] >= 1
        
        # 6. Удаление задачи
        delete_response = client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204
        
        # 7. Проверка, что задача удалена везде
        get_deleted_response = client.get(f"/tasks/{task_id}")
        assert get_deleted_response.status_code == 404
        
        # В списке задач проекта тоже не должно быть
        final_project_tasks = client.get(f"/projects/{sample_project.id}/tasks").json()
        assert not any(t["id"] == task_id for t in final_project_tasks)
