import os
import asyncio
import re
from typing import Optional, Dict, Any, List, Union
import openai
from ..models.estimation import (
    EstimationResult, EstimationStatus, EstimationRequest, 
    BatchEstimationRequest, UserPerformanceUpdate
)
from ..db.storage import InMemoryStorage
from ..db.postgres_storage import PostgreSQLStorage
from datetime import datetime

class AIEstimator:
    def __init__(self, storage: Union[InMemoryStorage, PostgreSQLStorage]):
        self.storage = storage
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def estimate_task(self, card_id: str, task_description: str, repo_url: str, 
                           priority: str = "medium", complexity: str = "medium",
                           user_id: Optional[str] = None, team_id: Optional[str] = None,
                           project_id: Optional[str] = None, batch_id: Optional[str] = None) -> EstimationResult:
        """Асинхронно оценивает задачу с помощью AI"""
        # Создаем запись в хранилище
        if hasattr(self.storage, 'create_estimation') and asyncio.iscoroutinefunction(self.storage.create_estimation):
            estimation = await self.storage.create_estimation(
                card_id, user_id, team_id, project_id, batch_id
            )
        else:
            estimation = self.storage.create_estimation(
                card_id, user_id, team_id, project_id, batch_id
            )
        
        try:
            # Формируем промпт для AI с учетом истории пользователя
            prompt = self._create_estimation_prompt(
                task_description, repo_url, priority, complexity, user_id
            )
            
            # Вызываем OpenAI API
            response = await self._call_openai(prompt)
            
            # Парсим ответ и извлекаем детали оценки
            estimation_data = self._parse_estimation_response(response)
            
            # Обновляем запись
            if hasattr(self.storage, 'update_estimation') and asyncio.iscoroutinefunction(self.storage.update_estimation):
                await self.storage.update_estimation(
                    estimation.id,
                    status=EstimationStatus.ESTIMATED,
                    estimatedHours=estimation_data['estimated_hours'],
                    confidence=estimation_data.get('confidence', 80),
                    reasoning=estimation_data.get('reasoning', ''),
                    breakdown=estimation_data.get('breakdown', {}),
                    task_metadata={
                        'priority': priority,
                        'complexity': complexity,
                        'repo_url': repo_url,
                        'ai_model': self.model
                    }
                )
            else:
                self.storage.update_estimation(
                    estimation.id,
                    status=EstimationStatus.ESTIMATED,
                    estimatedHours=estimation_data['estimated_hours'],
                    confidence=estimation_data.get('confidence', 80),
                    reasoning=estimation_data.get('reasoning', ''),
                    breakdown=estimation_data.get('breakdown', {}),
                    task_metadata={
                        'priority': priority,
                        'complexity': complexity,
                        'repo_url': repo_url,
                        'ai_model': self.model
                    }
                )
            
            if hasattr(self.storage, 'get_estimation_by_card_id') and asyncio.iscoroutinefunction(self.storage.get_estimation_by_card_id):
                return await self.storage.get_estimation_by_card_id(card_id)
            else:
                return self.storage.get_estimation_by_card_id(card_id)
            
        except Exception as e:
            # В случае ошибки обновляем статус
            if hasattr(self.storage, 'update_estimation') and asyncio.iscoroutinefunction(self.storage.update_estimation):
                await self.storage.update_estimation(
                    estimation.id,
                    status=EstimationStatus.FAILED,
                    error=str(e)
                )
            else:
                self.storage.update_estimation(
                    estimation.id,
                    status=EstimationStatus.FAILED,
                    error=str(e)
                )
            raise
    
    async def estimate_batch_tasks(self, batch_request: BatchEstimationRequest) -> str:
        """Оценивает множество задач в batch режиме"""
        # Создаем batch estimation
        if hasattr(self.storage, 'create_batch_estimation') and asyncio.iscoroutinefunction(self.storage.create_batch_estimation):
            batch = await self.storage.create_batch_estimation(
                batch_request.tasks,
                batch_request.userId,
                batch_request.teamId,
                batch_request.projectId
            )
        else:
            batch = self.storage.create_batch_estimation(
                batch_request.tasks,
                batch_request.userId,
                batch_request.teamId,
                batch_request.projectId
            )
        
        # Запускаем асинхронную обработку
        asyncio.create_task(self._process_batch_estimation(batch.batchId, batch_request))
        
        return batch.batchId
    
    async def _process_batch_estimation(self, batch_id: str, batch_request: BatchEstimationRequest):
        """Асинхронно обрабатывает batch estimation"""
        completed = 0
        failed = 0
        
        for task in batch_request.tasks:
            try:
                await self.estimate_task(
                    task.cardId,
                    task.taskDescription,
                    task.repoUrl,
                    task.priority,
                    task.complexity,
                    batch_request.userId,
                    batch_request.teamId,
                    batch_request.projectId,
                    batch_id
                )
                completed += 1
            except Exception as e:
                failed += 1
                print(f"Ошибка оценки задачи {task.cardId}: {e}")
            
            # Обновляем статус batch
            self.storage.update_batch_status(batch_id, completed, failed)
    
    async def update_user_performance(self, performance_update: UserPerformanceUpdate) -> EstimationResult:
        """Обновляет производительность пользователя и улучшает будущие оценки"""
        try:
            # Обновляем статистику в storage
            estimation = self.storage.update_user_performance(
                performance_update.estimationId,
                performance_update.actualHours,
                performance_update.userId,
                performance_update.notes,
                performance_update.difficulty,
                performance_update.blockers
            )
            
            if not estimation:
                raise ValueError("Оценка не найдена")
            
            # Анализируем производительность пользователя
            user_stats = self.storage.get_user_performance_stats(performance_update.userId)
            
            # Создаем промпт для анализа производительности
            analysis_prompt = self._create_performance_analysis_prompt(
                estimation, performance_update, user_stats
            )
            
            # Получаем AI анализ
            analysis_response = await self._call_openai(analysis_prompt)
            
            # Обновляем метаданные оценки с анализом
            self.storage.update_estimation(
                estimation.id,
                metadata={
                    **estimation.metadata,
                    'performance_analysis': analysis_response,
                    'actual_difficulty': performance_update.difficulty,
                    'blockers': performance_update.blockers,
                    'performance_updated_at': datetime.now().isoformat()
                }
            )
            
            return estimation
            
        except Exception as e:
            raise ValueError(f"Ошибка обновления производительности: {e}")
    
    def _create_performance_analysis_prompt(self, estimation: EstimationResult, 
                                          performance_update: UserPerformanceUpdate,
                                          user_stats: Any) -> str:
        """Создает промпт для анализа производительности пользователя"""
        return f"""
        Ты - эксперт по анализу производительности разработчиков. Проанализируй выполнение задачи и дай рекомендации.

        ЗАДАЧА:
        - Описание: {estimation.reasoning or 'Не указано'}
        - Оценка: {estimation.estimatedHours} часов
        - Фактическое время: {performance_update.actualHours} часов
        - Сложность: {estimation.metadata.get('complexity', 'Не указано')}
        - Приоритет: {estimation.metadata.get('priority', 'Не указано')}

        ВЫПОЛНЕНИЕ:
        - Фактическая сложность: {performance_update.difficulty}/10
        - Блокеры: {', '.join(performance_update.blockers) if performance_update.blockers else 'Не указано'}
        - Заметки: {performance_update.notes or 'Не указано'}

        СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ:
        - Всего задач: {user_stats.totalTasks}
        - Завершено: {user_stats.completedTasks}
        - Средняя точность: {user_stats.averageAccuracy:.1f}%
        - Bias оценки: {user_stats.estimationBias:.1f} часов

        ПРОАНАЛИЗИРУЙ и дай рекомендации в формате:

        PERFORMANCE_ANALYSIS: [анализ производительности]
        ACCURACY_IMPROVEMENT: [рекомендации по улучшению точности]
        ESTIMATION_BIAS: [анализ bias в оценках]
        COMPLEXITY_ASSESSMENT: [оценка сложности задачи]
        FUTURE_ESTIMATIONS: [рекомендации для будущих оценок]
        """
    
    def _create_estimation_prompt(self, task_description: str, repo_url: str, 
                                 priority: str, complexity: str, user_id: Optional[str] = None) -> str:
        """Создает детальный промпт для AI с учетом истории пользователя"""
        priority_weights = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.2,
            "urgent": 1.5
        }
        
        complexity_factors = {
            "simple": 0.7,
            "medium": 1.0,
            "complex": 1.4,
            "very-complex": 2.0
        }
        
        # Добавляем информацию о пользователе, если доступна
        user_context = ""
        if user_id:
            user_stats = self.storage.get_user_performance_stats(user_id)
            if user_stats.completedTasks > 0:
                user_context = f"""
                
                КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
                - Средняя точность оценок: {user_stats.averageAccuracy:.1f}%
                - Bias в оценках: {user_stats.estimationBias:.1f} часов
                - Предпочтения по сложности: {', '.join([f'{k}: {v}' for k, v in user_stats.complexityPreference.items()])}
                
                УЧТИ историю пользователя при оценке!
                """
        
        return f"""
        Ты - опытный разработчик-архитектор с 10+ лет опыта. Твоя задача - дать детальную оценку времени выполнения задачи.

        ЗАДАЧА:
        {task_description}
        
        РЕПОЗИТОРИЙ:
        {repo_url}
        
        ПАРАМЕТРЫ:
        - Приоритет: {priority} (множитель: {priority_weights.get(priority, 1.0)})
        - Ожидаемая сложность: {complexity} (множитель: {complexity_factors.get(complexity, 1.0)}){user_context}
        
        ПРОАНАЛИЗИРУЙ задачу и дай детальную оценку в следующем формате:

        ESTIMATED_HOURS: [число в часах, например 8.5]
        CONFIDENCE: [процент уверенности 0-100]
        REASONING: [краткое обоснование оценки]
        BREAKDOWN: {{
            "analysis": [время на анализ задачи],
            "development": [время на разработку],
            "testing": [время на тестирование],
            "review": [время на code review],
            "deployment": [время на развертывание],
            "documentation": [время на документацию]
        }}
        
        УЧТИ:
        1. Сложность технической реализации
        2. Необходимость тестирования и отладки
        3. Возможные непредвиденные сложности
        4. Время на code review и правки
        5. Приоритет и срочность задачи
        6. Сложность и размер репозитория
        7. Историю производительности пользователя (если доступна)
        
        ОТВЕТЬ строго в указанном формате без дополнительного текста.
        """
    
    async def _call_openai(self, prompt: str) -> str:
        """Вызывает OpenAI API с улучшенными параметрами"""
        loop = asyncio.get_event_loop()
        
        def _make_request():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты - эксперт по оценке времени разработки. Отвечай строго в указанном формате."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1,
                top_p=0.9
            )
            return response.choices[0].message.content
        
        # Выполняем запрос в отдельном потоке
        response = await loop.run_in_executor(None, _make_request)
        return response
    
    def _parse_estimation_response(self, response: str) -> Dict[str, Any]:
        """Парсит детальный ответ AI и извлекает все данные"""
        try:
            # Извлекаем основные данные
            estimated_hours_match = re.search(r'ESTIMATED_HOURS:\s*(\d+\.?\d*)', response)
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
            reasoning_match = re.search(r'REASONING:\s*(.+?)(?=\n|$)', response)
            
            if not estimated_hours_match:
                raise ValueError("Не удалось извлечь оценку времени из ответа AI")
            
            estimated_hours = float(estimated_hours_match.group(1))
            confidence = int(confidence_match.group(1)) if confidence_match else 80
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Оценка основана на анализе задачи"
            
            # Извлекаем детализацию
            breakdown = self._parse_breakdown(response)
            
            return {
                'estimated_hours': estimated_hours,
                'confidence': confidence,
                'reasoning': reasoning,
                'breakdown': breakdown
            }
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Ошибка парсинга ответа AI: {e}")
    
    def _parse_breakdown(self, response: str) -> Dict[str, float]:
        """Парсит детализацию времени по этапам"""
        breakdown = {}
        
        # Ищем секцию BREAKDOWN
        breakdown_match = re.search(r'BREAKDOWN:\s*\{([^}]+)\}', response, re.DOTALL)
        if breakdown_match:
            breakdown_text = breakdown_match.group(1)
            
            # Парсим каждый этап
            patterns = {
                'analysis': r'"analysis":\s*(\d+\.?\d*)',
                'development': r'"development":\s*(\d+\.?\d*)',
                'testing': r'"testing":\s*(\d+\.?\d*)',
                'review': r'"review":\s*(\d+\.?\d*)',
                'deployment': r'"deployment":\s*(\d+\.?\d*)',
                'documentation': r'"documentation":\s*(\d+\.?\d*)'
            }
            
            for stage, pattern in patterns.items():
                match = re.search(pattern, breakdown_text)
                if match:
                    breakdown[stage] = float(match.group(1))
        
        # Если детализация не найдена, создаем базовую
        if not breakdown:
            breakdown = {
                'analysis': 0.5,
                'development': 0.7,
                'testing': 0.2,
                'review': 0.1,
                'deployment': 0.1,
                'documentation': 0.1
            }
        
        return breakdown
    
    async def refine_estimation(self, estimation_id: str, feedback: str) -> EstimationResult:
        """Улучшает оценку на основе обратной связи"""
        try:
            estimation = self.storage.get_estimation(estimation_id)
            if not estimation:
                raise ValueError("Оценка не найдена")
            
            # Создаем промпт для улучшения
            refinement_prompt = f"""
            Предыдущая оценка: {estimation.estimatedHours} часов
            
            Обратная связь: {feedback}
            
            Улучши оценку на основе обратной связи и дай новую оценку в том же формате.
            """
            
            response = await self._call_openai(refinement_prompt)
            refined_data = self._parse_estimation_response(response)
            
            # Обновляем оценку
            self.storage.update_estimation(
                estimation_id,
                estimatedHours=refined_data['estimated_hours'],
                confidence=refined_data.get('confidence', estimation.confidence),
                reasoning=refined_data.get('reasoning', estimation.reasoning),
                breakdown=refined_data.get('breakdown', estimation.breakdown),
                metadata={
                    **estimation.metadata,
                    'refined': True,
                    'feedback': feedback,
                    'refined_at': datetime.now().isoformat()
                }
            )
            
            return self.storage.get_estimation(estimation_id)
            
        except Exception as e:
            raise ValueError(f"Ошибка улучшения оценки: {e}")
    
    def get_estimation_insights(self, estimation: EstimationResult) -> Dict[str, Any]:
        """Анализирует оценку и предоставляет инсайты"""
        insights = {
            'accuracy_score': self._calculate_accuracy_score(estimation),
            'complexity_level': self._assess_complexity_level(estimation),
            'risk_factors': self._identify_risk_factors(estimation),
            'recommendations': self._generate_recommendations(estimation)
        }
        
        return insights
    
    def _calculate_accuracy_score(self, estimation: EstimationResult) -> float:
        """Вычисляет оценку точности на основе исторических данных"""
        # TODO: Реализовать на основе исторических данных
        return 85.0  # Заглушка
    
    def _assess_complexity_level(self, estimation: EstimationResult) -> str:
        """Оценивает уровень сложности задачи"""
        hours = estimation.estimatedHours or 0
        
        if hours <= 2:
            return "Простая"
        elif hours <= 8:
            return "Средняя"
        elif hours <= 24:
            return "Сложная"
        else:
            return "Очень сложная"
    
    def _identify_risk_factors(self, estimation: EstimationResult) -> list:
        """Определяет факторы риска"""
        risks = []
        
        if estimation.estimatedHours and estimation.estimatedHours > 40:
            risks.append("Высокая оценка времени может указывать на неопределенность")
        
        if estimation.confidence and estimation.confidence < 70:
            risks.append("Низкая уверенность в оценке")
        
        if estimation.breakdown:
            dev_time = estimation.breakdown.get('development', 0)
            total_time = estimation.estimatedHours or 0
            
            if total_time > 0 and dev_time / total_time > 0.8:
                risks.append("Недостаточно времени на тестирование и review")
        
        return risks
    
    def _generate_recommendations(self, estimation: EstimationResult) -> list:
        """Генерирует рекомендации по улучшению оценки"""
        recommendations = []
        
        if estimation.estimatedHours and estimation.estimatedHours > 16:
            recommendations.append("Разбейте задачу на подзадачи для более точной оценки")
        
        if estimation.confidence and estimation.confidence < 80:
            recommendations.append("Добавьте больше деталей в описание задачи")
        
        if estimation.breakdown:
            test_time = estimation.breakdown.get('testing', 0)
            total_time = estimation.estimatedHours or 0
            
            if total_time > 0 and test_time / total_time < 0.15:
                recommendations.append("Увеличьте время на тестирование")
        
        return recommendations

    async def estimate_trello_task(self, card_id: str, card_data: dict, repo_url: str = None,
                                 priority: str = "medium", complexity: str = "medium",
                                 user_id: Optional[str] = None, team_id: Optional[str] = None,
                                 project_id: Optional[str] = None) -> EstimationResult:
        """Специализированная оценка для Trello карточек с анализом метаданных"""
        try:
            # Анализируем метаданные карточки
            card_analysis = self._analyze_trello_card(card_data)
            
            # Создаем запись в хранилище
            estimation = self.storage.create_estimation(
                card_id, user_id, team_id, project_id
            )
            
            # Формируем улучшенный промпт с учетом Trello контекста
            prompt = self._create_trello_enhanced_prompt(
                card_data, card_analysis, repo_url, priority, complexity
            )
            
            # Получаем оценку от AI
            ai_response = await self._call_openai(prompt)
            
            # Парсим ответ
            estimation_data = self._parse_estimation_response(ai_response)
            
            # Обновляем запись с Trello метаданными
            self.storage.update_estimation(
                estimation.id,
                status=EstimationStatus.ESTIMATED,
                estimatedHours=estimation_data['estimated_hours'],
                confidence=estimation_data.get('confidence', 80),
                reasoning=estimation_data.get('reasoning', ''),
                breakdown=estimation_data.get('breakdown', {}),
                metadata={
                    'priority': priority,
                    'complexity': complexity,
                    'repo_url': repo_url,
                    'ai_model': self.model,
                    'trello_analysis': card_analysis,
                    'card_labels': card_data.get('labels', []),
                    'card_due': card_data.get('due'),
                    'card_members': card_data.get('idMembers', []),
                    'estimation_method': 'trello_enhanced'
                }
            )
            
            return self.storage.get_estimation_by_card_id(card_id)
        except Exception as e:
            if estimation:
                self.storage.update_estimation(
                    estimation.id,
                    status=EstimationStatus.FAILED,
                    error=str(e)
                )
            raise

    def _analyze_trello_card(self, card_data: dict) -> dict:
        """Анализирует метаданные Trello карточки для улучшения оценки"""
        try:
            analysis = {
                "complexity_indicators": [],
                "priority_indicators": [],
                "label_count": len(card_data.get("labels", [])),
                "has_due_date": bool(card_data.get("due")),
                "member_count": len(card_data.get("idMembers", [])),
                "checklist_count": len(card_data.get("checklists", [])),
                "attachment_count": len(card_data.get("attachments", [])),
                "estimated_complexity": "medium",
                "estimated_priority": "medium",
                "confidence_factors": []
            }
            
            # Анализируем метки
            labels = card_data.get("labels", [])
            for label in labels:
                label_name = label.get("name", "").lower()
                label_color = label.get("color", "")
                
                # Анализ сложности по меткам
                if any(word in label_name for word in ["сложно", "hard", "difficult", "challenging"]):
                    analysis["complexity_indicators"].append("Высокая сложность по метке")
                    analysis["estimated_complexity"] = "high"
                elif any(word in label_name for word in ["просто", "easy", "simple", "quick"]):
                    analysis["complexity_indicators"].append("Низкая сложность по метке")
                    analysis["estimated_complexity"] = "low"
                
                # Анализ приоритета по меткам
                if any(word in label_name for word in ["срочно", "urgent", "критично", "critical", "важно", "important"]):
                    analysis["priority_indicators"].append("Высокий приоритет по метке")
                    analysis["estimated_priority"] = "high"
                elif any(word in label_name for word in ["низкий", "low", "неважно", "unimportant"]):
                    analysis["priority_indicators"].append("Низкий приоритет по метке")
                    analysis["estimated_priority"] = "low"
                
                # Анализ по цвету меток
                if label_color in ["red", "orange"]:
                    analysis["priority_indicators"].append("Высокий приоритет по цвету")
                    analysis["estimated_priority"] = "high"
                elif label_color in ["green", "blue"]:
                    analysis["priority_indicators"].append("Средний приоритет по цвету")
            
            # Анализ по описанию
            description = card_data.get("desc", "").lower()
            if description:
                # Сложность по описанию
                if any(word in description for word in ["сложно", "трудно", "много", "большой", "масштабный"]):
                    analysis["complexity_indicators"].append("Высокая сложность по описанию")
                    analysis["estimated_complexity"] = "high"
                elif any(word in description for word in ["просто", "быстро", "мало", "небольшой"]):
                    analysis["complexity_indicators"].append("Низкая сложность по описанию")
                    analysis["estimated_complexity"] = "low"
                
                # Приоритет по описанию
                if any(word in description for word in ["срочно", "критично", "важно", "приоритет"]):
                    analysis["priority_indicators"].append("Высокий приоритет по описанию")
                    analysis["estimated_priority"] = "high"
            
            # Анализ по чеклистам
            checklists = card_data.get("checklists", [])
            if checklists:
                total_items = sum(len(checklist.get("checkItems", [])) for checklist in checklists)
                if total_items > 10:
                    analysis["complexity_indicators"].append("Много пунктов в чеклистах")
                    analysis["estimated_complexity"] = "high"
                elif total_items < 3:
                    analysis["complexity_indicators"].append("Мало пунктов в чеклистах")
                    analysis["estimated_complexity"] = "low"
            
            # Анализ по вложениям
            attachments = card_data.get("attachments", [])
            if attachments:
                if len(attachments) > 5:
                    analysis["complexity_indicators"].append("Много вложений")
                    analysis["estimated_complexity"] = "high"
            
            # Анализ по участникам
            members = card_data.get("idMembers", [])
            if members:
                if len(members) > 3:
                    analysis["complexity_indicators"].append("Много участников")
                    analysis["estimated_complexity"] = "high"
                elif len(members) == 1:
                    analysis["complexity_indicators"].append("Один участник")
                    analysis["estimated_complexity"] = "low"
            
            # Факторы уверенности
            if analysis["label_count"] > 0:
                analysis["confidence_factors"].append("Есть метки для анализа")
            if analysis["has_due_date"]:
                analysis["confidence_factors"].append("Установлен срок")
            if analysis["member_count"] > 0:
                analysis["confidence_factors"].append("Назначены участники")
            if analysis["checklist_count"] > 0:
                analysis["confidence_factors"].append("Есть чеклисты")
            
            return analysis
            
        except Exception as e:
            print(f"Ошибка анализа Trello карточки: {e}")
            return {
                "complexity_indicators": [],
                "priority_indicators": [],
                "label_count": 0,
                "has_due_date": False,
                "member_count": 0,
                "checklist_count": 0,
                "attachment_count": 0,
                "estimated_complexity": "medium",
                "estimated_priority": "medium",
                "confidence_factors": ["Ошибка анализа"]
            }

    def _create_trello_enhanced_prompt(self, card_data: dict, card_analysis: dict, 
                                     repo_url: str, priority: str, complexity: str) -> str:
        """Создает улучшенный промпт для AI с учетом Trello контекста"""
        
        # Базовый промпт
        prompt = f"""
        Оцени время выполнения задачи на основе следующей информации:

        ЗАДАЧА: {card_data.get('name', 'Без названия')}
        ОПИСАНИЕ: {card_data.get('desc', 'Без описания')}
        РЕПОЗИТОРИЙ: {repo_url}
        
        АНАЛИЗ TRELLO КАРТОЧКИ:
        - Метки: {len(card_data.get('labels', []))} шт.
        - Участники: {len(card_data.get('idMembers', []))} чел.
        - Чеклисты: {len(card_data.get('checklists', []))} шт.
        - Вложения: {len(card_data.get('attachments', []))} шт.
        - Срок: {'Установлен' if card_data.get('due') else 'Не установлен'}
        
        ИНДИКАТОРЫ СЛОЖНОСТИ: {', '.join(card_analysis.get('complexity_indicators', []))}
        ИНДИКАТОРЫ ПРИОРИТЕТА: {', '.join(card_analysis.get('priority_indicators', []))}
        
        ПРИОРИТЕТ: {priority}
        СЛОЖНОСТЬ: {complexity}
        
        Пожалуйста, оцени время выполнения в часах, учитывая:
        1. Сложность задачи по описанию и меткам
        2. Количество участников и их взаимодействие
        3. Объем работы по чеклистам
        4. Техническую сложность по репозиторию
        5. Приоритет и срочность
        
        Ответ должен содержать:
        - estimated_hours: число часов (например, 8.5)
        - confidence_score: уверенность от 0.1 до 1.0
        - reasoning: краткое объяснение оценки
        """
        
        return prompt

    async def reestimate_trello_task(self, card_id: str, reason: str = "Изменения в карточке") -> EstimationResult:
        """Переоценивает задачу на основе изменений в Trello карточке"""
        try:
            estimation = self.storage.get_estimation_by_card_id(card_id)
            if not estimation:
                raise ValueError("Оценка не найдена")
            
            # Получаем актуальные данные карточки (в реальном приложении - через Trello API)
            # Пока используем существующие метаданные
            card_data = estimation.metadata.get('trello_data', {})
            if not card_data:
                card_data = {
                    'name': 'Переоценка',
                    'desc': estimation.reasoning or 'Описание отсутствует'
                }
            
            # Анализируем изменения
            card_analysis = self._analyze_trello_card(card_data)
            
            # Создаем промпт для переоценки
            reestimation_prompt = f"""
            Предыдущая оценка: {estimation.estimatedHours} часов
            
            Причина переоценки: {reason}
            
            Текущие данные карточки:
            {self._build_trello_context(card_data, card_analysis)}
            
            Переоцени задачу с учетом изменений и дай новую оценку в том же формате.
            """
            
            response = await self._call_openai(reestimation_prompt)
            refined_data = self._parse_estimation_response(response)
            
            # Создаем новую оценку с пометкой о переоценке
            new_estimation = self.storage.create_estimation(
                card_id,
                user_id=estimation.userId,
                team_id=estimation.teamId,
                project_id=estimation.projectId
            )
            
            # Обновляем новую оценку
            self.storage.update_estimation(
                new_estimation.id,
                status=EstimationStatus.ESTIMATED,
                estimatedHours=refined_data['estimated_hours'],
                confidence=refined_data.get('confidence', estimation.confidence),
                reasoning=refined_data.get('reasoning', estimation.reasoning),
                breakdown=refined_data.get('breakdown', estimation.breakdown),
                metadata={
                    **estimation.metadata,
                    'reestimated': True,
                    'reestimation_reason': reason,
                    'original_estimation_id': estimation.id,
                    'reestimated_at': datetime.now().isoformat(),
                    'trello_analysis': card_analysis
                }
            )
            
            return self.storage.get_estimation(new_estimation.id)
            
        except Exception as e:
            raise ValueError(f"Ошибка переоценки: {e}")
