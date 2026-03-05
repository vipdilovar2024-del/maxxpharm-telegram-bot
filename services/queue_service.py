"""
🏗️ Queue Service - Система очередей задач для Uber-архитектуры
Redis + Celery для распределения нагрузки
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("queue_service")

class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

class TaskPriority(Enum):
    """Приоритеты задач"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Задача в очереди"""
    id: str
    name: str
    data: Dict[str, Any]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None

class QueueService:
    """Сервис управления очередями задач"""
    
    def __init__(self):
        self.redis_client = None
        self.logger = logging.getLogger("queue_service")
        self.tasks = {}  # In-memory cache для активных задач
        self.task_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_processing_time": 0.0
        }
    
    async def initialize(self):
        """Инициализация Redis подключения"""
        try:
            import redis
            from bot.config import REDIS_URL
            
            self.redis_client = redis.from_url(
                REDIS_URL or "redis://localhost:6379/0",
                decode_responses=True
            )
            
            # Проверяем соединение
            self.redis_client.ping()
            self.logger.info("✅ Queue service initialized with Redis")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize queue service: {e}")
            raise
    
    async def enqueue_task(self, task_name: str, task_data: Dict[str, Any], 
                          priority: TaskPriority = TaskPriority.NORMAL, 
                          delay: Optional[int] = None) -> str:
        """Добавление задачи в очередь"""
        try:
            # Генерируем ID задачи
            task_id = f"{task_name}_{datetime.now().timestamp()}_{id(task_data)}"
            
            # Создаем объект задачи
            task = Task(
                id=task_id,
                name=task_name,
                data=task_data,
                status=TaskStatus.PENDING,
                priority=priority,
                created_at=datetime.now()
            )
            
            # Сохраняем в Redis
            task_dict = {
                "id": task.id,
                "name": task.name,
                "data": json.dumps(task.data),
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat(),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries
            }
            
            # Выбираем очередь в зависимости от приоритета
            queue_name = f"queue:{task_name}"
            
            if delay:
                # Отложенная задача
                self.redis_client.zadd(
                    f"delayed:{queue_name}",
                    {task_id: json.dumps(task_dict)},
                    datetime.now().timestamp() + delay
                )
            else:
                # Немедленная задача
                self.redis_client.lpush(queue_name, json.dumps(task_dict))
            
            # Сохраняем в кэш
            self.tasks[task_id] = task
            
            # Обновляем статистику
            self.task_stats["total_tasks"] += 1
            
            self.logger.info(f"📋 Task {task_id} enqueued to {queue_name}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"❌ Error enqueuing task: {e}")
            raise
    
    async def dequeue_task(self, queue_name: str) -> Optional[Task]:
        """Получение задачи из очереди"""
        try:
            # Сначала проверяем отложенные задачи
            now = datetime.now().timestamp()
            delayed_tasks = self.redis_client.zrangebyscore(
                f"delayed:{queue_name}", 0, now, withscores=True
            )
            
            for task_id, task_json in delayed_tasks:
                # Перемещаем отложенную задачу в основную очередь
                self.redis_client.lpush(queue_name, task_json)
                self.redis_client.zrem(f"delayed:{queue_name}", task_id)
            
            # Получаем задачу из основной очереди
            task_json = self.redis_client.rpop(queue_name)
            
            if task_json:
                task_dict = json.loads(task_json)
                
                # Восстанавливаем объект задачи
                task = Task(
                    id=task_dict["id"],
                    name=task_dict["name"],
                    data=json.loads(task_dict["data"]),
                    status=TaskStatus(task_dict["status"]),
                    priority=TaskPriority(task_dict["priority"]),
                    created_at=datetime.fromisoformat(task_dict["created_at"]),
                    retry_count=task_dict.get("retry_count", 0),
                    max_retries=task_dict.get("max_retries", 3)
                )
                
                # Обновляем статус
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                # Сохраняем обновленный статус
                await self.update_task_status(task)
                
                self.logger.info(f"📤 Task {task.id} dequeued from {queue_name}")
                return task
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error dequeuing task: {e}")
            return None
    
    async def update_task_status(self, task: Task, error: Optional[str] = None):
        """Обновление статуса задачи"""
        try:
            task.error = error
            
            # Обновляем в Redis
            task_dict = {
                "id": task.id,
                "name": task.name,
                "data": json.dumps(task.data),
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "error": task.error
            }
            
            self.redis_client.hset(f"task:{task.id}", mapping=task_dict)
            
            # Обновляем в кэше
            self.tasks[task.id] = task
            
            # Обновляем статистику
            if task.status == TaskStatus.SUCCESS:
                self.task_stats["completed_tasks"] += 1
                if task.started_at and task.completed_at:
                    processing_time = (task.completed_at - task.started_at).total_seconds()
                    self._update_avg_processing_time(processing_time)
            elif task.status == TaskStatus.FAILED:
                self.task_stats["failed_tasks"] += 1
            
            self.logger.info(f"📊 Task {task.id} status updated to {task.status.value}")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating task status: {e}")
    
    async def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """Завершение задачи"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                # Загружаем из Redis
                task_data = self.redis_client.hgetall(f"task:{task_id}")
                if task_data:
                    task = Task(
                        id=task_data["id"],
                        name=task_data["name"],
                        data=json.loads(task_data["data"]),
                        status=TaskStatus(task_data["status"]),
                        priority=TaskPriority(task_data["priority"]),
                        created_at=datetime.fromisoformat(task_data["created_at"]),
                        retry_count=int(task_data.get("retry_count", 0)),
                        max_retries=int(task_data.get("max_retries", 3))
                    )
                else:
                    self.logger.error(f"❌ Task {task_id} not found")
                    return
            
            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.now()
            
            await self.update_task_status(task)
            
            # Сохраняем результат если есть
            if result:
                self.redis_client.hset(f"task_result:{task_id}", mapping=result)
            
            self.logger.info(f"✅ Task {task_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error completing task {task_id}: {e}")
    
    async def fail_task(self, task_id: str, error: str, retry: bool = True):
        """Завершение задачи с ошибкой"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                self.logger.error(f"❌ Task {task_id} not found")
                return
            
            task.error = error
            task.retry_count += 1
            
            if retry and task.retry_count < task.max_retries:
                # Повторная попытка
                task.status = TaskStatus.RETRY
                await self.update_task_status(task, error)
                
                # Добавляем обратно в очередь с задержкой
                delay = min(300, 60 * task.retry_count)  # Экспоненциальная задержка
                await self.enqueue_task(task.name, task.data, task.priority, delay)
                
                self.logger.info(f"🔄 Task {task_id} failed, retry {task.retry_count}/{task.max_retries}")
            else:
                # Окончательный провал
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                await self.update_task_status(task, error)
                
                self.logger.error(f"❌ Task {task_id} failed permanently: {error}")
            
        except Exception as e:
            self.logger.error(f"❌ Error failing task {task_id}: {e}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Получение статуса очереди"""
        try:
            status = {
                "queues": {},
                "delayed_tasks": 0,
                "active_tasks": 0,
                "stats": self.task_stats.copy()
            }
            
            # Получаем информацию по всем очередям
            for queue_name in ["process_new_order", "process_accepted_order", 
                              "process_status_update", "send_notification", 
                              "ai_analysis", "daily_report"]:
                
                # Основная очередь
                queue_length = self.redis_client.llen(f"queue:{queue_name}")
                
                # Отложенные задачи
                delayed_length = self.redis_client.zcard(f"delayed:{queue_name}")
                
                status["queues"][queue_name] = {
                    "pending": queue_length,
                    "delayed": delayed_length
                }
                
                status["delayed_tasks"] += delayed_length
            
            # Активные задачи
            status["active_tasks"] = len([
                task for task in self.tasks.values() 
                if task.status == TaskStatus.RUNNING
            ])
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Error getting queue status: {e}")
            return {}
    
    async def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о задаче"""
        try:
            task_data = self.redis_client.hgetall(f"task:{task_id}")
            
            if task_data:
                # Получаем результат если есть
                result = self.redis_client.hgetall(f"task_result:{task_id}")
                
                return {
                    **task_data,
                    "result": result if result else None
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting task info {task_id}: {e}")
            return None
    
    async def cleanup_old_tasks(self, days: int = 7):
        """Очистка старых задач"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # Получаем все старые задачи
            old_tasks = []
            
            for key in self.redis_client.scan_iter(match="task:*"):
                task_data = self.redis_client.hgetall(key)
                if task_data:
                    created_at = datetime.fromisoformat(task_data.get("created_at", ""))
                    if created_at.timestamp() < cutoff_timestamp:
                        old_tasks.append(key.decode())
            
            # Удаляем старые задачи
            for task_key in old_tasks:
                self.redis_client.delete(task_key)
                self.redis_client.delete(f"task_result:{task_key.split(':')[1]}")
            
            self.logger.info(f"🧹 Cleaned up {len(old_tasks)} old tasks")
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old tasks: {e}")
    
    def _update_avg_processing_time(self, processing_time: float):
        """Обновление среднего времени обработки"""
        if self.task_stats["completed_tasks"] == 1:
            self.task_stats["avg_processing_time"] = processing_time
        else:
            # Скользящее среднее
            alpha = 0.1  # Коэффициент сглаживания
            self.task_stats["avg_processing_time"] = (
                alpha * processing_time + 
                (1 - alpha) * self.task_stats["avg_processing_time"]
            )

# Глобальный экземпляр
queue_service: Optional[QueueService] = None

async def get_queue_service() -> QueueService:
    """Получение экземпляра queue service"""
    global queue_service
    if queue_service is None:
        queue_service = QueueService()
        await queue_service.initialize()
    return queue_service

# Удобные функции для использования
async def enqueue_task(task_name: str, task_data: Dict[str, Any], 
                      priority: TaskPriority = TaskPriority.NORMAL) -> str:
    """Добавление задачи в очередь (удобная функция)"""
    service = await get_queue_service()
    return await service.enqueue_task(task_name, task_data, priority)

async def dequeue_task(queue_name: str) -> Optional[Task]:
    """Получение задачи из очереди (удобная функция)"""
    service = await get_queue_service()
    return await service.dequeue_task(queue_name)

async def complete_task(task_id: str, result: Optional[Dict[str, Any]] = None):
    """Завершение задачи (удобная функция)"""
    service = await get_queue_service()
    await service.complete_task(task_id, result)

async def fail_task(task_id: str, error: str, retry: bool = True):
    """Завершение задачи с ошибкой (удобная функция)"""
    service = await get_queue_service()
    await service.fail_task(task_id, error, retry)
