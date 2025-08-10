import os
import asyncio
from typing import Optional
import openai
from ..models.estimation import EstimationResult, EstimationStatus
from ..db.storage import InMemoryStorage

class AIEstimator:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def estimate_task(self, card_id: str, task_description: str, repo_url: str) -> EstimationResult:
        """Асинхронно оценивает задачу с помощью AI"""
        # Создаем запись в хранилище
        estimation = self.storage.create_estimation(card_id)
        
        try:
            # Формируем промпт для AI
            prompt = self._create_estimation_prompt(task_description, repo_url)
            
            # Вызываем OpenAI API
            response = await self._call_openai(prompt)
            
            # Парсим ответ и извлекаем оценку в часах
            estimated_hours = self._parse_estimation_response(response)
            
            # Обновляем запись
            self.storage.update_estimation(
                estimation.id,
                status=EstimationStatus.ESTIMATED,
                estimatedHours=estimated_hours
            )
            
            return self.storage.get_estimation_by_card_id(card_id)
            
        except Exception as e:
            # В случае ошибки обновляем статус
            self.storage.update_estimation(
                estimation.id,
                status=EstimationStatus.FAILED,
                error=str(e)
            )
            raise
    
    def _create_estimation_prompt(self, task_description: str, repo_url: str) -> str:
        """Создает промпт для AI"""
        return f"""
        Ты - опытный разработчик-архитектор. Твоя задача - оценить время выполнения задачи в часах.

        Описание задачи: {task_description}
        Репозиторий: {repo_url}

        Проанализируй задачу и дай оценку времени в часах. Учти:
        1. Сложность технической реализации
        2. Необходимость тестирования
        3. Возможные непредвиденные сложности
        4. Время на code review и правки

        Ответь ТОЛЬКО числом (например: 8.5), представляющим оценку в часах.
        """
    
    async def _call_openai(self, prompt: str) -> str:
        """Вызывает OpenAI API"""
        loop = asyncio.get_event_loop()
        
        def _make_request():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            return response.choices[0].message.content
        
        # Выполняем запрос в отдельном потоке
        response = await loop.run_in_executor(None, _make_request)
        return response
    
    def _parse_estimation_response(self, response: str) -> float:
        """Парсит ответ AI и извлекает оценку в часах"""
        try:
            # Ищем число в ответе
            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            if numbers:
                return float(numbers[0])
            else:
                raise ValueError("Не удалось извлечь числовую оценку из ответа AI")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Ошибка парсинга ответа AI: {e}")
