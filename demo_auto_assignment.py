"""
🧠 Auto-Assignment Demo - Демонстрация умной системы распределения
Уровень Uber/Glovo/Amazon
"""

import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Импортируем наши компоненты
from services.assignment_service import AssignmentService
from services.ai_assignment_optimizer import AIAssignmentOptimizer
from database.assignment_schemas import ALL_SQL_SCHEMAS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoAssignmentDemo:
    """Демонстрация системы Auto-Assignment"""
    
    def __init__(self):
        self.bot = None
        self.assignment_service = None
        self.ai_optimizer = None
        self.logger = logging.getLogger("auto_assignment_demo")
    
    async def setup(self):
        """Настройка демонстрации"""
        # Создаем бота (используйте ваш токен)
        self.bot = Bot(token="YOUR_BOT_TOKEN_HERE")
        self.assignment_service = AssignmentService(self.bot)
        self.ai_optimizer = AIAssignmentOptimizer(self.bot)
        
        # Инициализируем тестовые данные
        await self._setup_test_data()
        
        self.logger.info("🧠 Auto-Assignment Demo initialized")
    
    async def _setup_test_data(self):
        """Настройка тестовых данных"""
        try:
            from database.db import get_db_connection
            
            conn = await get_db_connection()
            
            # Создаем таблицы если их нет
            for schema in ALL_SQL_SCHEMAS:
                await conn.execute(schema)
            
            # Создаем тестовых работников
            test_workers = [
                (697780124, "Оператор Али", "operator", "центр", True),
                (697780125, "Сборщик Рустам", "picker", "центр", True),
                (697780130, "Сборщик Бобур", "picker", "север", True),
                (697780131, "Сборщик Карим", "picker", "юг", True),
                (697780126, "Проверщик Камол", "checker", None, True),
                (697780132, "Проверщик Сардор", "checker", None, True),
                (697780127, "Курьер Бекзод", "courier", "центр", True),
                (697780133, "Курьер Фарход", "courier", "север", True),
                (697780134, "Курьер Умид", "courier", "юг", True),
                (697780135, "Курьер Джамшед", "courier", "запад", True),
            ]
            
            for telegram_id, name, role, zone, is_online in test_workers:
                await conn.execute("""
                    INSERT INTO users (telegram_id, name, role, zone, is_online, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, true, NOW(), NOW())
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        name = $2, role = $3, zone = $4, is_online = $5, updated_at = NOW()
                """, telegram_id, name, role, zone, is_online)
            
            # Создаем тестовые заказы
            test_orders = [
                (1, 697780128, "Ахмад", "created", "центр", "Парацетамол и Амоксиклав", 145.0),
                (2, 697780129, "Карим", "accepted", "север", "Витамины для детей", 89.0),
                (3, 697780130, "Фарход", "ready", "юг", "Лекарства от давления", 234.0),
            ]
            
            for order_id, client_id, client_name, status, zone, comment, amount in test_orders:
                await conn.execute("""
                    INSERT INTO orders (id, client_id, comment, amount, status, zone, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        status = $5, updated_at = NOW()
                """, order_id, client_id, f"{client_name} - {comment}", amount, status, zone)
            
            await conn.close()
            
            self.logger.info("✅ Test data setup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up test data: {e}")
    
    async def demo_basic_assignment(self):
        """Демонстрация базового распределения"""
        self.logger.info("🧠 Demo: Basic Assignment")
        
        # Создаем тестовый заказ
        test_order = {
            "id": 999,
            "client_name": "Тестовый клиент",
            "zone": "центр",
            "amount": 150.0,
            "status": "accepted"
        }
        
        # Назначаем сборщика
        picker = await self.assignment_service.assign_picker(999, "центр")
        
        if picker:
            self.logger.info(f"✅ Picker assigned: {picker['name']} (ID: {picker['id']})")
        else:
            self.logger.warning("⚠️ No picker available")
        
        # Назначаем проверщика
        checker = await self.assignment_service.assign_checker(999)
        
        if checker:
            self.logger.info(f"✅ Checker assigned: {checker['name']} (ID: {checker['id']})")
        else:
            self.logger.warning("⚠️ No checker available")
        
        # Назначаем курьера
        courier = await self.assignment_service.assign_courier(999, "центр")
        
        if courier:
            self.logger.info(f"✅ Courier assigned: {courier['name']} (ID: {courier['id']})")
        else:
            self.logger.warning("⚠️ No courier available")
    
    async def demo_ai_optimization(self):
        """Демонстрация AI оптимизации"""
        self.logger.info("🧠 Demo: AI Optimization")
        
        from database.models import UserRole
        
        test_order = {
            "id": 888,
            "client_name": "AI Тест клиент",
            "zone": "центр",
            "amount": 200.0,
            "status": "accepted"
        }
        
        # Получаем оптимального сборщика с AI
        optimal_picker = await self.ai_optimizer.get_optimal_worker_advanced(
            UserRole.PICKER, test_order
        )
        
        if optimal_picker:
            self.logger.info(f"🧠 AI Picker selected: {optimal_picker['name']}")
        else:
            self.logger.warning("⚠️ No optimal picker found")
        
        # Предсказываем время выполнения
        time_prediction = await self.ai_optimizer.predict_order_completion_time(test_order)
        self.logger.info(f"⏰ Time prediction: {time_prediction}")
        
        # Оптимизация распределения
        optimization = await self.ai_optimizer.optimize_worker_distribution()
        self.logger.info(f"📊 Distribution optimization: {optimization}")
    
    async def demo_auto_pipeline(self):
        """Демонстрация автоматического pipeline"""
        self.logger.info("🧠 Demo: Auto Pipeline")
        
        # Обновляем статус заказа для триггера авто-распределения
        from database.db import get_db_connection
        
        conn = await get_db_connection()
        
        # Создаем новый заказ
        await conn.execute("""
            INSERT INTO orders (id, client_id, comment, amount, status, zone, created_at, updated_at)
            VALUES (777, 697780128, 'Pipeline тест заказ', 175.0, 'created', 'центр', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """)
        
        await conn.close()
        
        # Запускаем авто-распределение
        success = await self.assignment_service.auto_assign_pipeline(777)
        
        if success:
            self.logger.info("✅ Auto pipeline completed successfully")
        else:
            self.logger.warning("⚠️ Auto pipeline failed")
    
    async def demo_demand_forecast(self):
        """Демонстрация прогноза спроса"""
        self.logger.info("🧠 Demo: Demand Forecast")
        
        # Прогноз на 24 часа
        forecast = await self.ai_optimizer.get_demand_forecast(24)
        
        self.logger.info("📈 24-hour demand forecast:")
        
        for hour_offset in range(0, 24, 4):  # Показываем каждые 4 часа
            key = f"+{hour_offset}h"
            if key in forecast:
                data = forecast[key]
                self.logger.info(f"  {key}: {data['predicted_orders']} orders, "
                               f"{data['required_workers']} workers needed")
    
    async def demo_rebalancing(self):
        """Демонстрация ребалансировки"""
        self.logger.info("🧠 Demo: Rebalancing")
        
        # Создаем неравномерную нагрузку
        from database.db import get_db_connection
        
        conn = await get_db_connection()
        
        # Увеличиваем нагрузку на одного сборщика
        await conn.execute("""
            UPDATE users
            SET active_orders = 8
            WHERE role = 'picker' AND id = 697780125
        """)
        
        await conn.close()
        
        # Запускаем ребалансировку
        rebalanced_count = await self.assignment_service.rebalance_orders()
        
        self.logger.info(f"🔄 Rebalanced {rebalanced_count} orders")
    
    async def demo_worker_performance(self):
        """Демонстрация производительности работников"""
        self.logger.info("🧠 Demo: Worker Performance")
        
        # Получаем статистику распределения
        stats = await self.assignment_service.get_assignment_stats()
        
        self.logger.info("📊 Assignment Statistics:")
        
        for role, data in stats.items():
            self.logger.info(f"  {role.title()}:")
            self.logger.info(f"    Total: {data['total']}")
            self.logger.info(f"    Online: {data['online']}")
            self.logger.info(f"    Total Load: {data['total_load']}")
            self.logger.info(f"    Avg Load: {data['avg_load']:.1f}")

async def main():
    """Основная функция демонстрации"""
    
    print("🧠 MAXXPHARM Auto-Assignment Demo")
    print("🚀 Умная система распределения уровня Uber/Glovo/Amazon")
    print("🔄 Полный цикл: Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено")
    print()
    
    demo = AutoAssignmentDemo()
    await demo.setup()
    
    print("🧠 Запуск демонстрации...")
    print()
    
    try:
        # Демонстрация базового распределения
        print("1️⃣ Базовое распределение:")
        await demo.demo_basic_assignment()
        print()
        
        # Демонстрация AI оптимизации
        print("2️⃣ AI оптимизация:")
        await demo.demo_ai_optimization()
        print()
        
        # Демонстрация автоматического pipeline
        print("3️⃣ Автоматический pipeline:")
        await demo.demo_auto_pipeline()
        print()
        
        # Демонстрация прогноза спроса
        print("4️⃣ Прогноз спроса:")
        await demo.demo_demand_forecast()
        print()
        
        # Демонстрация ребалансировки
        print("5️⃣ Ребалансировка:")
        await demo.demo_rebalancing()
        print()
        
        # Демонстрация производительности
        print("6️⃣ Производительность работников:")
        await demo.demo_worker_performance()
        print()
        
        print("✅ Демонстрация завершена!")
        print()
        print("🧠 Ключевые возможности:")
        print("  • Умное распределение по минимальной нагрузке")
        print("  • AI оптимизация с учетом множества факторов")
        print("  • Автоматический pipeline распределения")
        print("  • Прогнозирование спроса")
        print("  • Автоматическая ребалансировка")
        print("  • Аналитика производительности")
        print()
        print("🚀 Ваш Telegram-бот может обрабатывать 10K-100K заказов в день!")
        
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
        print(f"❌ Ошибка демонстрации: {e}")
    
    finally:
        if demo.bot:
            await demo.bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
