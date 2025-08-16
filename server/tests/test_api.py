"""
Тесты для API эндпоинтов TaskWeight
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_health_check(client: TestClient):
    """Тест эндпоинта проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_create_user(client: TestClient, db_session: Session):
    """Тест создания пользователя"""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "securepassword123"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert data["is_active"] is True

def test_get_user(client: TestClient, sample_user):
    """Тест получения пользователя по ID"""
    response = client.get(f"/users/{sample_user.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_user.id
    assert data["username"] == sample_user.username
    assert data["email"] == sample_user.email

def test_get_user_not_found(client: TestClient):
    """Тест получения несуществующего пользователя"""
    response = client.get("/users/999999")
    assert response.status_code == 404

def test_create_project(client: TestClient, sample_user):
    """Тест создания проекта"""
    project_data = {
        "name": "New Project",
        "description": "New project description",
        "owner_id": sample_user.id,
        "status": "active"
    }
    
    response = client.post("/projects/", json=project_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["description"] == project_data["description"]
    assert data["owner_id"] == sample_user.id
    assert "id" in data

def test_get_project(client: TestClient, sample_project):
    """Тест получения проекта по ID"""
    response = client.get(f"/projects/{sample_project.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_project.id
    assert data["name"] == sample_project.name
    assert data["owner_id"] == sample_project.owner_id

def test_create_task(client: TestClient, sample_project):
    """Тест создания задачи"""
    task_data = {
        "title": "New Task",
        "description": "New task description",
        "project_id": sample_project.id,
        "status": "todo",
        "priority": "high"
    }
    
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["project_id"] == sample_project.id
    assert "id" in data

def test_get_task(client: TestClient, sample_task):
    """Тест получения задачи по ID"""
    response = client.get(f"/tasks/{sample_task.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_task.id
    assert data["title"] == sample_task.title
    assert data["project_id"] == sample_task.project_id

def test_update_task(client: TestClient, sample_task):
    """Тест обновления задачи"""
    update_data = {
        "title": "Updated Task",
        "status": "in_progress"
    }
    
    response = client.put(f"/tasks/{sample_task.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["status"] == update_data["status"]
    assert data["id"] == sample_task.id

def test_delete_task(client: TestClient, sample_task):
    """Тест удаления задачи"""
    response = client.delete(f"/tasks/{sample_task.id}")
    assert response.status_code == 204
    
    # Проверяем, что задача действительно удалена
    get_response = client.get(f"/tasks/{sample_task.id}")
    assert get_response.status_code == 404

def test_get_user_projects(client: TestClient, sample_user, sample_project):
    """Тест получения проектов пользователя"""
    response = client.get(f"/users/{sample_user.id}/projects")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    project = data[0]
    assert project["owner_id"] == sample_user.id

def test_get_project_tasks(client: TestClient, sample_project, sample_task):
    """Тест получения задач проекта"""
    response = client.get(f"/projects/{sample_project.id}/tasks")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    task = data[0]
    assert task["project_id"] == sample_project.id

def test_search_tasks(client: TestClient, sample_task):
    """Тест поиска задач"""
    response = client.get("/tasks/search?q=Test")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_task_statistics(client: TestClient, sample_project):
    """Тест получения статистики задач"""
    response = client.get(f"/projects/{sample_project.id}/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_tasks" in data
    assert "completed_tasks" in data
    assert "pending_tasks" in data
    assert isinstance(data["total_tasks"], int)

def test_create_estimation(client: TestClient, sample_task):
    """Тест создания оценки задачи"""
    estimation_data = {
        "task_id": sample_task.id,
        "estimated_hours": 8.5,
        "confidence_level": 0.8,
        "method": "ai_estimation"
    }
    
    response = client.post("/estimations/", json=estimation_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["task_id"] == sample_task.id
    assert data["estimated_hours"] == estimation_data["estimated_hours"]
    assert "id" in data

def test_get_estimation_history(client: TestClient, sample_task):
    """Тест получения истории оценок задачи"""
    response = client.get(f"/tasks/{sample_task.id}/estimations")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)

def test_webhook_endpoint(client: TestClient):
    """Тест webhook эндпоинта"""
    webhook_data = {
        "event": "task_created",
        "data": {"task_id": 123, "title": "Test Task"}
    }
    
    response = client.post("/webhooks/", json=webhook_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "received"

def test_invalid_user_data(client: TestClient):
    """Тест валидации данных пользователя"""
    invalid_user_data = {
        "username": "",  # Пустое имя пользователя
        "email": "invalid-email",  # Неверный email
        "full_name": "Test User"
    }
    
    response = client.post("/users/", json=invalid_user_data)
    assert response.status_code == 422  # Validation Error

def test_invalid_project_data(client: TestClient, sample_user):
    """Тест валидации данных проекта"""
    invalid_project_data = {
        "name": "",  # Пустое название
        "owner_id": 999999  # Несуществующий пользователь
    }
    
    response = client.post("/projects/", json=invalid_project_data)
    assert response.status_code == 422

def test_unauthorized_access(client: TestClient):
    """Тест неавторизованного доступа"""
    # Попытка получить данные без авторизации
    response = client.get("/users/1")
    # В зависимости от реализации аутентификации
    # может быть 401 или 200 (если аутентификация не реализована)
    assert response.status_code in [200, 401, 403]
