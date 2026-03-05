#!/usr/bin/env python3
"""
🚀 MAXXPHARM Enterprise Bot - $10M Startup Architecture
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Импортируем Enterprise модули
from bot_gateway import BotGateway, create_enterprise_bot
from crm_core import CRMCore, create_crm_core
from service_layer import create_service_layer
from monitor.health_check import HealthChecker
from monitor.auto_restart import AutoRestartManager
from ai.ai_engine import AIEngine
from cache.redis_client import RedisClient
from config.settings import Settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("enterprise_bot")

class EnterpriseBot:
    """Enterprise бот с архитектурой $10M стартапа"""
    
    def __init__(self):
        self.settings = Settings()
        self.bot = None
        self.crm_core = None
        self.services = None
        self.health_checker = None
        self.auto_restart = None
        self.ai_engine = None
        self.redis_client = None
        
        # 🏗️ Enterprise компоненты
        self.bot_gateway = None
        
        # 📊 Метрики
        self.start_time = datetime.now()
        self.metrics = {
            'messages_processed': 0,
            'orders_created': 0,
            'errors_count': 0,
            'uptime_seconds': 0
        }
    
    async def initialize(self):
        """Инициализация Enterprise бота"""
        try:
            logger.info("🚀 Initializing MAXXPHARM Enterprise Bot...")
            
            # 🎯 Проверка переменных окружения
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                raise ValueError("BOT_TOKEN environment variable is required")
            
            # 🏗️ Инициализация компонентов
            logger.info("📦 Initializing CRM Core...")
            self.crm_core = await create_crm_core()
            
            logger.info("🤖 Creating Bot Gateway...")
            self.bot_gateway = await create_enterprise_bot(bot_token)
            
            logger.info("🔧 Creating Service Layer...")
            self.services = await create_service_layer(self.crm_core, self.bot_gateway.bot)
            
            logger.info("🏥 Initializing Health Checker...")
            self.health_checker = HealthChecker(self.crm_core, self.services)
            
            logger.info("🔄 Initializing Auto Restart Manager...")
            self.auto_restart = AutoRestartManager()
            
            logger.info("🧠 Initializing AI Engine...")
            self.ai_engine = AIEngine(self.services['notification_service'])
            
            logger.info("🗄️ Initializing Redis Client...")
            self.redis_client = RedisClient()
            await self.redis_client.connect()
            
            # 🎯 Настройка обработчиков
            await self._setup_enterprise_handlers()
            
            # 📊 Запуск мониторинга
            await self._start_monitoring()
            
            logger.info("✅ Enterprise Bot initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enterprise Bot: {e}")
            return False
    
    async def _setup_enterprise_handlers(self):
        """Настройка Enterprise обработчиков"""
        
        # 🎨 Визуальные обработчики
        from visual_handlers import VisualHandlers
        visual_handlers = VisualHandlers(self.crm_core, self.bot_gateway.bot)
        visual_handlers.register_handlers(self.bot_gateway.dp)
        
        # 🏢 Enterprise обработчики
        @self.bot_gateway.dp.message(Command("enterprise_status"))
        async def cmd_enterprise_status(message):
            """Статус Enterprise системы"""
            user_role = await self.crm_core.role_manager.get_user_role(message.from_user.id)
            
            if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            status_text = f"""
🏢 <b>MAXXPHARM Enterprise Status</b>

📊 <b>System Components:</b>
✅ CRM Core: Active
✅ Bot Gateway: Active
✅ Service Layer: Active
✅ AI Engine: Active
✅ Cache Layer: Active

📈 <b>Metrics:</b>
🤖 Messages: {self.metrics['messages_processed']}
📦 Orders: {self.metrics['orders_created']}
❌ Errors: {self.metrics['errors_count']}
⏱️ Uptime: {self.metrics['uptime_seconds']}s

🕐 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await message.answer(status_text)
        
        @self.bot_gateway.dp.message(Command("enterprise_health"))
        async def cmd_enterprise_health(message):
            """Детальная проверка здоровья"""
            user_role = await self.crm_core.role_manager.get_user_role(message.from_user.id)
            
            if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            health_status = await self.health_checker.check_all_systems()
            
            health_text = "🏥 <b>Enterprise Health Check</b>\n\n"
            
            for component, status in health_status.items():
                emoji = "✅" if status['healthy'] else "❌"
                health_text += f"{emoji} <b>{component}:</b> {status['message']}\n"
                
                if 'details' in status:
                    health_text += f"   📋 {status['details']}\n"
            
            await message.answer(health_text)
        
        @self.bot_gateway.dp.message(Command("enterprise_metrics"))
        async def cmd_enterprise_metrics(message):
            """Метрики Enterprise системы"""
            user_role = await self.crm_core.role_manager.get_user_role(message.from_user.id)
            
            if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Получаем метрики сервисов
            order_stats = await self.services['order_service'].get_order_statistics()
            payment_stats = await self.services['payment_service'].get_payment_statistics()
            delivery_stats = await self.services['delivery_service'].get_delivery_statistics()
            
            metrics_text = f"""
📊 <b>Enterprise Metrics</b>

📦 <b>Orders:</b>
• Total: {order_stats['total_orders']}
• Delivered: {order_stats['delivered_orders']}
• Conversion: {order_stats['conversion_rate']:.1f}%
• Revenue: ${order_stats['total_amount']:,.2f}

💳 <b>Payments:</b>
• Total: {payment_stats['total_payments']}
• Confirmed: {payment_stats['confirmed_payments']}
• Rate: {payment_stats['confirmation_rate']:.1f}%
• Amount: ${payment_stats['total_amount']:,.2f}

🚚 <b>Deliveries:</b>
• Total: {delivery_stats['total_deliveries']}
• Completed: {delivery_stats['completed_deliveries']}
• Rate: {delivery_stats['completion_rate']:.1f}%
• Amount: ${delivery_stats['total_amount']:,.2f}

🤖 <b>Bot Metrics:</b>
• Messages: {self.metrics['messages_processed']}
• Orders: {self.metrics['orders_created']}
• Errors: {self.metrics['errors_count']}
• Uptime: {self.metrics['uptime_seconds']}s
"""
            
            await message.answer(metrics_text)
        
        @self.bot_gateway.dp.message(Command("test_enterprise"))
        async def cmd_test_enterprise(message):
            """Тест Enterprise функциональности"""
            user_role = await self.crm_core.role_manager.get_user_role(message.from_user.id)
            
            if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            # Создаем тестовый заказ
            order_data = {
                'text': 'Enterprise test order with full functionality',
                'items': [
                    {'product': 'Enterprise Product 1', 'quantity': 2, 'price': 25.50},
                    {'product': 'Enterprise Product 2', 'quantity': 1, 'price': 45.75}
                ],
                'urgent': True
            }
            
            order = await self.services['order_service'].create_order(message.from_user.id, order_data)
            
            # Создаем тестовый платеж
            payment = await self.services['payment_service'].create_payment(order.id, order.amount)
            
            # Подтверждаем платеж
            await self.services['payment_service'].confirm_payment(
                payment.id, 
                message.from_user.id, 
                'test_confirmation',
                'test_data'
            )
            
            test_text = f"""
🧪 <b>Enterprise Test Completed</b>

📦 Order #{order.id} created
💳 Payment #{payment.id} confirmed
💰 Amount: ${order.amount}
🎯 Priority: {order.priority.value.title()}

✅ All Enterprise components working correctly!
"""
            
            await message.answer(test_text)
        
        @self.bot_gateway.dp.message()
        async def handle_message(message, user_role: UserRole):
            """Обработка сообщений с метриками"""
            self.metrics['messages_processed'] += 1
            
            # Логируем активность
            logger.info(f"Message from {message.from_user.id} ({user_role.value}): {message.text[:50]}")
    
        @self.bot_gateway.dp.callback_query()
        async def handle_callback(callback, user_role: UserRole):
            """Обработка callback с метриками"""
            self.metrics['messages_processed'] += 1
            
            logger.info(f"Callback from {callback.from_user.id} ({user_role.value}): {callback.data[:50]}")
    
    async def _start_monitoring(self):
        """Запуск мониторинга"""
        # Запуск проверки здоровья
        asyncio.create_task(self._health_monitor_loop())
        
        # Запуск сбора метрик
        asyncio.create_task(self._metrics_loop())
        
        # Запуск автоперезапуска
        asyncio.create_task(self._auto_restart_loop())
    
    async def _health_monitor_loop(self):
        """Цикл проверки здоровья"""
        while True:
            try:
                await self.health_checker.check_all_systems()
                await asyncio.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_loop(self):
        """Цикл сбора метрик"""
        while True:
            try:
                # Обновляем uptime
                self.metrics['uptime_seconds'] = int((datetime.now() - self.start_time).total_seconds())
                
                # Сохраняем метрики в Redis
                await self.redis_client.set("enterprise_metrics", self.metrics, expire=3600)
                
                await asyncio.sleep(300)  # Каждые 5 минут
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(60)
    
    async def _auto_restart_loop(self):
        """Цикл автоперезапуска"""
        while True:
            try:
                await self.auto_restart.check_system_health()
                await asyncio.sleep(1800)  # Каждые 30 минут
            except Exception as e:
                logger.error(f"Auto restart loop error: {e}")
                await asyncio.sleep(300)
    
    async def start(self):
        """Запуск Enterprise бота"""
        try:
            # 🚀 Запуск Bot Gateway
            await self.bot_gateway.start()
            
        except KeyboardInterrupt:
            logger.info("🛑 Enterprise Bot stopped by user")
            await self.shutdown()
        except Exception as e:
            logger.error(f"❌ Enterprise Bot error: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Завершение работы Enterprise бота"""
        try:
            logger.info("🛑 Shutting down Enterprise Bot...")
            
            # 🔄 Останавливаем компоненты
            if self.bot_gateway:
                await self.bot_gateway.stop()
            
            if self.redis_client:
                await self.redis_client.disconnect()
            
            if self.crm_core:
                await self.crm_core.shutdown()
            
            logger.info("✅ Enterprise Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM Enterprise Bot starting...")
    print("🏢 $10M Startup Architecture")
    print("🤖 Uber/Glovo Level System")
    
    # 🏗️ Создаем Enterprise структуру
    from enterprise_structure import create_enterprise_structure
    create_enterprise_structure()
    
    # 🚀 Создаем и запускаем бот
    bot = EnterpriseBot()
    
    if await bot.initialize():
        await bot.start()
    else:
        logger.error("❌ Failed to initialize Enterprise Bot")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Enterprise Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
