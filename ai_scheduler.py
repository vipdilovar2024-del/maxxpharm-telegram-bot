# ⏰ AI SCHEDULER - MAXXPHARM
# Автоматический запуск AI-анализа и уведомлений

import asyncio
import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging
from enum import Enum

# Импорты наших модулей
import ai_brain
import data_pipeline
import database

# ================================
# ⏰ КОНФИГУРАЦИЯ SCHEDULER
# ================================

SCHEDULER_CONFIG = {
    'timezone': 'UTC',
    'daily_report_time': '08:00',  # Утренний отчет
    'evening_report_time': '20:00',  # Вечерний отчет
    'analysis_intervals': {
        'quick_check': 300,      # 5 минут - быстрая проверка
        'full_analysis': 1800,   # 30 минут - полный анализ
        'deep_analysis': 3600    # 1 час - глубокий анализ
    },
    'notification_intervals': {
        'immediate': 0,          # Немедленно
        'urgent': 300,           # 5 минут
        'normal': 1800,          # 30 минут
        'low_priority': 3600      # 1 час
    }
}

logger = logging.getLogger(__name__)

# ================================
# 📋 МОДЕЛИ SCHEDULER
# ================================

class TaskType(Enum):
    """Типы задач"""
    QUICK_CHECK = "quick_check"
    FULL_ANALYSIS = "full_analysis"
    DEEP_ANALYSIS = "deep_analysis"
    DAILY_REPORT = "daily_report"
    EVENING_REPORT = "evening_report"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"

class TaskPriority(Enum):
    """Приоритеты задач"""
    LOW = 1
    NORMAL = 2
    URGENT = 3
    IMMEDIATE = 4

@dataclass
class ScheduledTask:
    """Запланированная задача"""
    id: str
    type: TaskType
    priority: TaskPriority
    scheduled_time: datetime.datetime
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    repeat_interval: Optional[int] = None
    enabled: bool = True
    last_run: Optional[datetime.datetime] = None
    next_run: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.next_run is None:
            self.next_run = self.scheduled_time

@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime.datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

# ================================
# ⏰ TASK SCHEDULER
# ================================

class TaskScheduler:
    """Планировщик задач"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.running = False
        self.worker_task = None
        self.results: List[TaskResult] = []
        self.max_results = 1000
    
    def add_task(self, task: ScheduledTask):
        """Добавление задачи"""
        self.tasks[task.id] = task
        logger.info(f"📅 Added task: {task.id} ({task.type.value}) at {task.scheduled_time}")
    
    def remove_task(self, task_id: str):
        """Удаление задачи"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"🗑️ Removed task: {task_id}")
    
    def schedule_recurring_task(self, task_id: str, task_type: TaskType, 
                            function: Callable, interval: int, 
                            priority: TaskPriority = TaskPriority.NORMAL,
                            start_time: Optional[datetime.datetime] = None):
        """Планирование повторяющейся задачи"""
        if start_time is None:
            start_time = datetime.datetime.now()
        
        task = ScheduledTask(
            id=task_id,
            type=task_type,
            priority=priority,
            scheduled_time=start_time,
            function=function,
            repeat_interval=interval
        )
        
        self.add_task(task)
    
    def schedule_daily_task(self, task_id: str, task_type: TaskType,
                          function: Callable, time_str: str,
                          priority: TaskPriority = TaskPriority.NORMAL):
        """Планирование ежедневной задачи"""
        hour, minute = map(int, time_str.split(':'))
        now = datetime.datetime.now()
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Если время уже прошло, планируем на завтра
        if scheduled_time <= now:
            scheduled_time += datetime.timedelta(days=1)
        
        task = ScheduledTask(
            id=task_id,
            type=task_type,
            priority=priority,
            scheduled_time=scheduled_time,
            function=function,
            repeat_interval=24 * 3600  # 24 часа
        )
        
        self.add_task(task)
    
    async def start(self):
        """Запуск планировщика"""
        if self.running:
            logger.warning("⚠️ Scheduler is already running")
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("⏰ Task Scheduler started")
    
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("⏰ Task Scheduler stopped")
    
    async def _worker_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                # Обновление очереди задач
                await self._update_task_queue()
                
                # Выполнение готовых задач
                if not self.task_queue.empty():
                    await self._execute_ready_tasks()
                
                # Ожидание до следующей проверки
                await asyncio.sleep(10)  # Проверка каждые 10 секунд
                
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _update_task_queue(self):
        """Обновление очереди задач"""
        now = datetime.datetime.now()
        
        for task in self.tasks.values():
            if task.enabled and task.next_run <= now:
                # Приоритет: чем ниже число, тем выше приоритет
                priority_value = 5 - task.priority.value
                await self.task_queue.put((priority_value, task.scheduled_time, task))
    
    async def _execute_ready_tasks(self):
        """Выполнение готовых задач"""
        while not self.task_queue.empty():
            try:
                priority, scheduled_time, task = self.task_queue.get_nowait()
                
                # Проверяем, что задача все еще актуальна
                if task.id not in self.tasks or not task.enabled:
                    continue
                
                # Выполняем задачу
                result = await self._execute_task(task)
                self.results.append(result)
                
                # Обновляем время следующего запуска для повторяющихся задач
                if task.repeat_interval:
                    task.last_run = datetime.datetime.now()
                    task.next_run = task.last_run + datetime.timedelta(seconds=task.repeat_interval)
                else:
                    # Одноразовая задача - удаляем
                    self.remove_task(task.id)
                
                self.task_queue.task_done()
                
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"❌ Error executing task: {e}")
    
    async def _execute_task(self, task: ScheduledTask) -> TaskResult:
        """Выполнение отдельной задачи"""
        start_time = datetime.datetime.now()
        
        try:
            logger.info(f"⏰ Executing task: {task.id}")
            
            # Выполнение функции
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function(*task.args, **task.kwargs)
            else:
                result = task.function(*task.args, **task.kwargs)
            
            execution_time = (datetime.datetime.now() - start_time).total_seconds()
            
            task_result = TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
            logger.info(f"✅ Task {task.id} completed in {execution_time:.2f}s")
            return task_result
            
        except Exception as e:
            execution_time = (datetime.datetime.now() - start_time).total_seconds()
            
            task_result = TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            
            logger.error(f"❌ Task {task.id} failed: {e}")
            return task_result
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса планировщика"""
        return {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': len([t for t in self.tasks.values() if t.enabled]),
            'queue_size': self.task_queue.qsize(),
            'recent_results': self.results[-10:],
            'config': SCHEDULER_CONFIG
        }

# ================================
# 🧠 AI TASKS
# ================================

class AITasks:
    """AI-задачи для планировщика"""
    
    def __init__(self):
        self.ai_controller = ai_brain.ai_controller
        self.pipeline_manager = data_pipeline.pipeline_manager
    
    async def quick_check_task(self) -> Dict[str, Any]:
        """Быстрая проверка системы"""
        logger.info("🔍 Running quick system check...")
        
        try:
            # Проверка статуса pipeline
            pipeline_status = self.pipeline_manager.get_status()
            
            # Базовая проверка метрик
            db = await database.get_db()
            recent_metrics = await db.get_ai_metrics(hours=1)
            
            # Проверка активных алертов
            alerts_count = len(pipeline_status.get('active_alerts', 0))
            
            result = {
                'status': 'healthy' if alerts_count == 0 else 'warning',
                'pipeline_running': pipeline_status.get('running', False),
                'recent_metrics_count': len(recent_metrics),
                'active_alerts': alerts_count,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"✅ Quick check completed: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Quick check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def full_analysis_task(self) -> Dict[str, Any]:
        """Полный AI-анализ"""
        logger.info("🧠 Running full AI analysis...")
        
        try:
            # Получение данных для анализа
            db = await database.get_db()
            orders = await db.get_orders(limit=200)
            
            # Конвертация в формат AI
            ai_data = []
            for order in orders:
                ai_data.append({
                    'id': order.id,
                    'client_id': order.client_id,
                    'created_at': order.created_at.isoformat(),
                    'status': order.status,
                    'operator_id': order.operator_id,
                    'courier_id': order.courier_id,
                    'delivery_time': order.delivery_time,
                    'price': float(order.price),
                    'cancel_reason': order.cancel_reason
                })
            
            # Запуск AI-анализа
            analysis_result = await self.ai_controller.full_analysis_cycle(ai_data)
            
            # Сохранение результатов
            await db.save_ai_metric(
                metric_type='full_ai_analysis',
                value=1.0,
                details={
                    'problems_count': len(analysis_result.get('problems', [])),
                    'recommendations_count': len(analysis_result.get('recommendations', [])),
                    'forecast_orders': analysis_result.get('forecast', {}).get('tomorrow_orders', 0),
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            logger.info("✅ Full AI analysis completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Full analysis failed: {e}")
            return {'error': str(e)}
    
    async def deep_analysis_task(self) -> Dict[str, Any]:
        """Глубокий AI-анализ"""
        logger.info("🔬 Running deep AI analysis...")
        
        try:
            # Расширенный анализ за последние 7 дней
            db = await database.get_db()
            orders = await db.get_orders(limit=500)
            
            # Анализ трендов
            analytics = await db.get_orders_analytics(days=7)
            
            # Прогноз на неделю
            forecast_result = await self.ai_controller.brain.forecast_metrics()
            
            # Генерация стратегических рекомендаций
            strategy_result = await self.ai_controller.strategy_advisor.generate_strategy()
            
            result = {
                'analytics': analytics,
                'forecast': forecast_result,
                'strategy': strategy_result,
                'analysis_period': '7_days',
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Сохранение результатов
            await db.save_ai_metric(
                metric_type='deep_ai_analysis',
                value=1.0,
                details=result
            )
            
            logger.info("✅ Deep AI analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Deep analysis failed: {e}")
            return {'error': str(e)}
    
    async def daily_report_task(self) -> Dict[str, Any]:
        """Ежедневный отчет"""
        logger.info("📊 Generating daily report...")
        
        try:
            # Полный анализ
            analysis_result = await self.full_analysis_task()
            
            if 'error' not in analysis_result:
                # Формирование отчета
                report = await self.ai_controller.brain.generate_report()
                
                # TODO: Отправка отчета администраторам через Telegram
                logger.info("📊 Daily report generated successfully")
                
                return {
                    'report': report,
                    'sent': False,  # TODO: Implement sending
                    'timestamp': datetime.datetime.now().isoformat()
                }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Daily report failed: {e}")
            return {'error': str(e)}
    
    async def evening_report_task(self) -> Dict[str, Any]:
        """Вечерний отчет"""
        logger.info("🌙 Generating evening report...")
        
        try:
            # Краткий анализ за день
            db = await database.get_db()
            analytics = await db.get_orders_analytics(days=1)
            
            # Прогноз на завтра
            forecast = await self.ai_controller.brain.forecast_metrics()
            
            report = (
                f"🌙 <b>Вечерний отчет MAXXPHARM</b>\n\n"
                f"📊 <b>Сегодня:</b>\n"
                f"📦 Заказов: {analytics.get('total_orders', 0)}\n"
                f"✅ Выполнено: {analytics.get('completed_orders', 0)}\n"
                f"❌ Отменено: {analytics.get('cancelled_orders', 0)}\n"
                f"🔄 Конверсия: {(analytics.get('completed_orders', 0) / max(analytics.get('total_orders', 1), 1) * 100):.1f}%\n\n"
                f"🔮 <b>Прогноз на завтра:</b>\n"
                f"📦 Ожидаемые заказы: {forecast.get('tomorrow_orders', 0)}\n"
                f"⚠️ Риск: {forecast.get('risk_level', 'unknown')}\n\n"
                f"🤖 <b>AI Brain</b>\n"
                f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # TODO: Отправка отчета администраторам
            logger.info("🌙 Evening report generated")
            
            return {
                'report': report,
                'sent': False,  # TODO: Implement sending
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Evening report failed: {e}")
            return {'error': str(e)}
    
    async def cleanup_task(self) -> Dict[str, Any]:
        """Задача очистки"""
        logger.info("🧹 Running cleanup task...")
        
        try:
            db = await database.get_db()
            
            # Очистка истекших сессий
            cleaned_sessions = await db.cleanup_expired_sessions()
            
            # TODO: Очистка старых метрик (retention policy)
            # TODO: Очистка старых логов
            
            result = {
                'cleaned_sessions': cleaned_sessions,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"🧹 Cleanup completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {'error': str(e)}

# ================================
# ⏰ AI SCHEDULER MANAGER
# ================================

class AISchedulerManager:
    """Менеджер AI-планировщика"""
    
    def __init__(self):
        self.scheduler = TaskScheduler()
        self.ai_tasks = AITasks()
        self.running = False
    
    async def start(self):
        """Запуск AI-планировщика"""
        if self.running:
            logger.warning("⚠️ AI Scheduler is already running")
            return
        
        logger.info("🚀 Starting AI Scheduler...")
        
        # Планирование задач
        self._schedule_tasks()
        
        # Запуск планировщика
        await self.scheduler.start()
        self.running = True
        
        logger.info("✅ AI Scheduler started successfully")
    
    async def stop(self):
        """Остановка AI-планировщика"""
        await self.scheduler.stop()
        self.running = False
        logger.info("🛑 AI Scheduler stopped")
    
    def _schedule_tasks(self):
        """Планирование всех задач"""
        # Быстрая проверка каждые 5 минут
        self.scheduler.schedule_recurring_task(
            task_id="quick_check",
            task_type=TaskType.QUICK_CHECK,
            function=self.ai_tasks.quick_check_task,
            interval=SCHEDULER_CONFIG['analysis_intervals']['quick_check'],
            priority=TaskPriority.IMMEDIATE
        )
        
        # Полный анализ каждые 30 минут
        self.scheduler.schedule_recurring_task(
            task_id="full_analysis",
            task_type=TaskType.FULL_ANALYSIS,
            function=self.ai_tasks.full_analysis_task,
            interval=SCHEDULER_CONFIG['analysis_intervals']['full_analysis'],
            priority=TaskPriority.URGENT
        )
        
        # Глубокий анализ каждый час
        self.scheduler.schedule_recurring_task(
            task_id="deep_analysis",
            task_type=TaskType.DEEP_ANALYSIS,
            function=self.ai_tasks.deep_analysis_task,
            interval=SCHEDULER_CONFIG['analysis_intervals']['deep_analysis'],
            priority=TaskPriority.NORMAL
        )
        
        # Утренний отчет в 8:00
        self.scheduler.schedule_daily_task(
            task_id="daily_report",
            task_type=TaskType.DAILY_REPORT,
            function=self.ai_tasks.daily_report_task,
            time_str=SCHEDULER_CONFIG['daily_report_time'],
            priority=TaskPriority.NORMAL
        )
        
        # Вечерний отчет в 20:00
        self.scheduler.schedule_daily_task(
            task_id="evening_report",
            task_type=TaskType.EVENING_REPORT,
            function=self.ai_tasks.evening_report_task,
            time_str=SCHEDULER_CONFIG['evening_report_time'],
            priority=TaskPriority.NORMAL
        )
        
        # Очистка каждый час
        self.scheduler.schedule_recurring_task(
            task_id="cleanup",
            task_type=TaskType.CLEANUP,
            function=self.ai_tasks.cleanup_task,
            interval=SCHEDULER_CONFIG['cleanup_interval'],
            priority=TaskPriority.LOW
        )
        
        logger.info("📅 All AI tasks scheduled")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса AI-планировщика"""
        return {
            'running': self.running,
            'scheduler_status': self.scheduler.get_status(),
            'config': SCHEDULER_CONFIG
        }

# ================================
# ⏰ ГЛОБАЛЬНЫЙ AI SCHEDULER
# ================================

# Глобальный экземпляр AI-планировщика
ai_scheduler = AISchedulerManager()

# Функции для управления AI-планировщиком
async def start_ai_scheduler():
    """Запуск AI-планировщика"""
    return await ai_scheduler.start()

async def stop_ai_scheduler():
    """Остановка AI-планировщика"""
    return await ai_scheduler.stop()

def get_ai_scheduler_status():
    """Получение статуса AI-планировщика"""
    return ai_scheduler.get_status()

print("⏰ AI Scheduler module loaded")
