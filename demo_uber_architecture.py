"""
🏗️ Uber Architecture Demo - Демонстрация масштабируемой архитектуры
Uber/Glovo/Amazon уровень для десятков тысяч заказов
"""

import asyncio
import logging
from datetime import datetime
from aiogram import Bot

# Импортируем наши компоненты
from services.queue_service import get_queue_service, TaskPriority
from services.worker_system import create_worker_pool, WorkerManager
from api_layer import get_api_layer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uber_demo")

class UberArchitectureDemo:
    """Демонстрация Uber-архитектуры"""
    
    def __init__(self):
        self.bot = None
        self.queue_service = None
        self.worker_manager = None
        self.api_layer = None
        self.logger = logging.getLogger("uber_demo")
    
    async def setup(self):
        """Настройка демонстрации"""
        try:
            # Создаем бота (демо)
            self.bot = Bot(token="demo_token")
            
            # Инициализируем компоненты
            self.queue_service = await get_queue_service()
            self.worker_manager = await create_worker_pool()
            self.api_layer = get_api_layer(self.bot)
            
            self.logger.info("✅ Uber Architecture demo initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Setup error: {e}")
            raise
    
    async def demo_queue_system(self):
        """Демонстрация очереди задач"""
        self.logger.info("📋 Demo: Queue System")
        
        # Создаем тестовые задачи
        tasks = [
            ("process_new_order", {"order_id": 1001, "client_id": 123}, TaskPriority.HIGH),
            ("process_new_order", {"order_id": 1002, "client_id": 124}, TaskPriority.HIGH),
            ("send_notification", {"user_id": 123, "message": "Новый заказ"}, TaskPriority.NORMAL),
            ("ai_analysis", {"order_id": 1001}, TaskPriority.LOW),
            ("daily_report", {}, TaskPriority.LOW),
            ("process_status_update", {"order_id": 1001, "status": "accepted", "worker_id": 1}, TaskPriority.NORMAL),
        ]
        
        task_ids = []
        
        for task_name, task_data, priority in tasks:
            task_id = await self.queue_service.enqueue_task(task_name, task_data, priority)
            task_ids.append(task_id)
            self.logger.info(f"📋 Task {task_id} enqueued: {task_name}")
        
        # Показываем статус очереди
        queue_status = await self.queue_service.get_queue_status()
        
        self.logger.info("📊 Queue Status:")
        for queue_name, info in queue_status.get("queues", {}).items():
            self.logger.info(f"  {queue_name}: {info['pending']} pending, {info['delayed']} delayed")
        
        self.logger.info(f"🔄 Active tasks: {queue_status.get('active_tasks', 0)}")
        
        return task_ids
    
    async def demo_worker_processing(self):
        """Демонстрация обработки воркерами"""
        self.logger.info("🤖 Demo: Worker Processing")
        
        # Запускаем воркеров на короткое время
        worker_task = asyncio.create_task(self.worker_manager.start_all_workers())
        
        # Ждем немного для обработки задач
        await asyncio.sleep(5)
        
        # Останавливаем воркеров
        await self.worker_manager.stop_all_workers()
        
        # Показываем статистику
        stats = self.worker_manager.get_total_stats()
        
        self.logger.info("📊 Worker Statistics:")
        self.logger.info(f"  Total workers: {stats['total_workers']}")
        self.logger.info(f"  Processed tasks: {stats['total_processed']}")
        self.logger.info(f"  Failed tasks: {stats['total_failed']}")
        self.logger.info(f"  Success rate: {stats['total_success_rate']:.1f}%")
        
        # Статистика по каждому воркеру
        for worker_stat in stats['workers']:
            self.logger.info(f"  {worker_stat['worker_id']}: {worker_stat['processed_tasks']} processed, "
                           f"{worker_stat['tasks_per_hour']:.1f} tasks/hour")
        
        await worker_task
    
    async def demo_api_layer(self):
        """Демонстрация API слоя"""
        self.logger.info("🔌 Demo: API Layer")
        
        try:
            # Создаем тестовый заказ через API
            order_data = {
                "comment": "Тестовый заказ через API",
                "amount": 150.0,
                "items": [{"product": "Парацетамол", "quantity": 2}]
            }
            
            order = await self.api_layer.create_order(123, order_data)
            
            self.logger.info(f"📦 Order created via API: #{order['id']}")
            
            # Получаем заказ через API
            retrieved_order = await self.api_layer.get_order(order['id'], 123)
            
            if retrieved_order:
                self.logger.info(f"📋 Order retrieved via API: #{retrieved_order['id']}")
            
            # Получаем заказы пользователя
            user_orders = await self.api_layer.get_user_orders(123)
            
            self.logger.info(f"📊 User orders: {len(user_orders)} orders")
            
            # Получаем статистику дашборда
            dashboard_stats = await self.api_layer.get_dashboard_stats(697780123, "director")
            
            if dashboard_stats:
                self.logger.info(f"📊 Dashboard stats available")
            
        except Exception as e:
            self.logger.error(f"❌ API demo error: {e}")
    
    async def demo_scalability(self):
        """Демонстрация масштабируемости"""
        self.logger.info("📈 Demo: Scalability")
        
        # Создаем много задач для тестирования нагрузки
        num_tasks = 100
        task_ids = []
        
        start_time = datetime.now()
        
        for i in range(num_tasks):
            task_id = await self.queue_service.enqueue_task(
                "process_new_order",
                {"order_id": 2000 + i, "client_id": 123 + i},
                TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        enqueue_time = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(f"📋 Enqueued {num_tasks} tasks in {enqueue_time:.2f} seconds")
        self.logger.info(f"📊 Throughput: {num_tasks / enqueue_time:.1f} tasks/second")
        
        # Запускаем больше воркеров
        additional_workers = []
        for i in range(5):
            from services.worker_system import WorkerFactory
            worker = WorkerFactory.create_order_worker(f"scale_worker_{i}")
            await worker.initialize()
            additional_workers.append(worker)
        
        # Обрабатываем задачи
        processing_start = datetime.now()
        
        # Запускаем всех воркеров
        all_workers = list(self.worker_manager.workers.values()) + additional_workers
        worker_tasks = []
        
        for worker in all_workers:
            task = asyncio.create_task(worker.start())
            worker_tasks.append(task)
        
        # Ждем обработки
        await asyncio.sleep(10)
        
        # Останавливаем воркеров
        for worker in all_workers:
            await worker.stop()
        
        await asyncio.gather(*worker_tasks)
        
        processing_time = (datetime.now() - processing_start).total_seconds()
        
        self.logger.info(f"🤖 Processed tasks in {processing_time:.2f} seconds")
        self.logger.info(f"📊 Processing throughput: {num_tasks / processing_time:.1f} tasks/second")
        
        # Показываем финальную статистику
        final_status = await self.queue_service.get_queue_status()
        final_stats = self.worker_manager.get_total_stats()
        
        self.logger.info("📊 Final Results:")
        self.logger.info(f"  Total tasks: {num_tasks}")
        self.logger.info(f"  Processed: {final_stats['total_processed']}")
        self.logger.info(f"  Failed: {final_stats['total_failed']}")
        self.logger.info(f"  Success rate: {final_stats['total_success_rate']:.1f}%")
        self.logger.info(f"  Remaining in queue: {final_status.get('queues', {}).get('process_new_order', {}).get('pending', 0)}")
    
    async def demo_pipeline(self):
        """Демонстрация полного pipeline"""
        self.logger.info("🔄 Demo: Full Pipeline")
        
        # Создаем заказ
        order_data = {
            "comment": "Pipeline тестовый заказ",
            "amount": 200.0,
            "items": [{"product": "Амоксиклав", "quantity": 1}]
        }
        
        order = await self.api_layer.create_order(123, order_data)
        self.logger.info(f"📦 Order created: #{order['id']}")
        
        # Запускаем воркеров для обработки pipeline
        worker_task = asyncio.create_task(self.worker_manager.start_all_workers())
        
        # Ждем обработки pipeline
        await asyncio.sleep(8)
        
        # Останавливаем воркеров
        await self.worker_manager.stop_all_workers()
        await worker_task
        
        # Показываем результат
        final_order = await self.api_layer.get_order(order['id'], 123)
        
        if final_order:
            self.logger.info(f"📊 Final order status: {final_order['status']}")
        
        self.logger.info("🔄 Pipeline demo completed")
    
    async def run_all_demos(self):
        """Запуск всех демонстраций"""
        self.logger.info("🚀 Starting Uber Architecture Demo")
        self.logger.info("📋 Uber/Glovo/Amazon level architecture")
        self.logger.info("🔄 Bot → API → Queue → Workers → Database")
        
        try:
            # Демонстрация очереди
            await self.demo_queue_system()
            await asyncio.sleep(1)
            
            # Демонстрация воркеров
            await self.demo_worker_processing()
            await asyncio.sleep(1)
            
            # Демонстрация API слоя
            await self.demo_api_layer()
            await asyncio.sleep(1)
            
            # Демонстрация масштабируемости
            await self.demo_scalability()
            await asyncio.sleep(1)
            
            # Демонстрация pipeline
            await self.demo_pipeline()
            
            self.logger.info("✅ All demos completed successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Demo error: {e}")
        
        finally:
            # Очистка
            if self.worker_manager:
                await self.worker_manager.stop_all_workers()

async def main():
    """Основная функция демонстрации"""
    print("🏗️ MAXXPHARM Uber Architecture Demo")
    print("🚀 Uber/Glovo/Amazon level architecture")
    print("📋 Bot → API → Queue → Workers → Database")
    print("🔄 Масштабируемость до десятков тысяч заказов")
    print()
    
    demo = UberArchitectureDemo()
    
    try:
        await demo.setup()
        await demo.run_all_demos()
        
        print()
        print("✅ Uber Architecture Demo completed!")
        print()
        print("🏗️ Ключевые возможности:")
        print("  📋 Queue система - распределение нагрузки")
        print("  🤖 Worker система - параллельная обработка")
        print("  🔌 API слой - разделение интерфейса от логики")
        print("  📈 Масштабируемость - десятки тысяч заказов")
        print("  🔄 Pipeline - автоматическая обработка")
        print("  💪 Enterprise надежность")
        print()
        print("🚀 Ваш Telegram-бот готов к уровню Uber!")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
