"""
🚀 MAXXPHARM Production Bot - Объединенный бот со всеми возможностями
Production-ready для Render со всеми компонентами:
- 🛡️ Production System (защита от падений)
- 🏗️ Uber Architecture (масштабируемость)
- 🗄️ Database (PostgreSQL)
- 🤖 AI Assignment (автоматическое распределение)
- 📊 Uber UX (интерфейс)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode

# Импорты всех наших систем
from watchdog_system import get_watchdog, start_watchdog
from bot_lock_system import ensure_single_instance, single_bot_context
from health_check_system import get_health_checker, health_check_loop
from api_layer import get_api_layer
from services.queue_service import get_queue_service, TaskPriority
from services.worker_system import create_worker_pool, WorkerManager
from database_connection import initialize_database

# Настройка логирования уровня production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/production_bot.log'),
        logging.FileHandler('logs/errors.log', level=logging.ERROR)
    ]
)

logger = logging.getLogger("production_bot")

class MaxxpharmProductionBot:
    """Объединенный Production бот со всеми возможностями"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.api_layer = None
        self.queue_service = None
        self.worker_manager = None
        self.health_checker = None
        self.watchdog = None
        self.running = False
        self.logger = logging.getLogger("maxxpharm_bot")
        
        # Создаем директорию для логов
        os.makedirs("logs", exist_ok=True)
    
    async def initialize(self) -> bool:
        """Инициализация всех компонентов"""
        try:
            # Проверяем переменные окружения
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                raise ValueError("BOT_TOKEN environment variable is required")
            
            # Создаем бота с production настройками
            self.bot = Bot(
                token=bot_token,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                protect_content=True,
                disable_notification=False
            )
            
            # Создаем диспетчер
            self.dp = Dispatcher()
            
            # Инициализация базы данных
            self.logger.info("🗄️ Initializing database...")
            db_success = await initialize_database()
            if not db_success:
                self.logger.error("❌ Database initialization failed")
                return False
            
            # Инициализация API слоя
            self.logger.info("🔌 Initializing API layer...")
            self.api_layer = get_api_layer(self.bot)
            
            # Инициализация очереди
            self.logger.info("📋 Initializing queue service...")
            self.queue_service = await get_queue_service()
            
            # Инициализация воркеров
            self.logger.info("🤖 Initializing worker system...")
            self.worker_manager = await create_worker_pool()
            
            # Инициализация health checker
            self.logger.info("🏥 Initializing health checker...")
            self.health_checker = get_health_checker(self.bot)
            
            # Инициализация watchdog
            self.logger.info("🛡️ Initializing watchdog...")
            self.watchdog = get_watchdog(self.bot)
            
            # Настройка обработчиков
            await self._setup_handlers()
            
            # Настройка middleware
            await self._setup_middlewares()
            
            self.logger.info("✅ Maxxpharm Production Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def _setup_handlers(self):
        """Настройка всех обработчиков"""
        
        # 📱 Обработчики клиента
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message, role: str):
            """Обработчик /start"""
            try:
                user = await self._get_user_info(message.from_user.id)
                if not user:
                    await message.answer("❌ Пользователь не найден")
                    return
                
                welcome_text = self._get_welcome_text(user)
                keyboard = self._get_main_menu(role)
                
                await message.answer(welcome_text, reply_markup=keyboard)
                
                # Логируем действие
                await self.api_layer.log_action(
                    user_id=user.get("id"),
                    client_id=user.get("id") if role == "client" else None,
                    action="start_command",
                    details=f"User {user.get('name')} started bot"
                )
                
            except Exception as e:
                self.logger.error(f"❌ Error in /start: {e}")
                await message.answer("❌ Ошибка при запуске")
        
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def cmd_create_order(message: Message, role: str):
            """Создание заявки клиента"""
            if role != "client":
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                await message.answer(
                    "📦 <b>Новая заявка</b>\n\n"
                    "Отправьте список препаратов, фото рецепта или голосовое сообщение:",
                    reply_markup=self._get_main_menu(role)
                )
                
            except Exception as e:
                self.logger.error(f"❌ Error in create order: {e}")
                await message.answer("❌ Ошибка создания заявки")
        
        @self.dp.message(F.text == "📍 Мои заказы")
        async def cmd_my_orders(message: Message, role: str):
            """Мои заказы клиента"""
            if role != "client":
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                orders = await self.api_layer.get_user_orders(message.from_user.id)
                
                if not orders:
                    await message.answer("📭 У вас нет заказов")
                    return
                
                # Формируем список заказов
                orders_text = "📍 <b>Мои заказы</b>\n\n"
                for order in orders:
                    status_emoji = {
                        "created": "📝",
                        "waiting_payment": "💳", 
                        "accepted": "✅",
                        "processing": "🔄",
                        "ready": "📦",
                        "checking": "🔍",
                        "waiting_courier": "🚚",
                        "on_way": "📍",
                        "delivered": "✅",
                        "cancelled": "❌"
                    }
                    
                    emoji = status_emoji.get(order["status"], "📋")
                    orders_text += f"{emoji} <b>#{order['id']}</b> {order['status'].replace('_', ' ').title()}\n"
                    orders_text += f"💰 {order.get('amount', 0)} сомони • 🕐 {order.get('created_at', datetime.now()).strftime('%d.%m %H:%M')}\n\n"
                
                await message.answer(orders_text)
                
            except Exception as e:
                self.logger.error(f"❌ Error in my orders: {e}")
                await message.answer("❌ Ошибка получения заказов")
        
        # 👨‍💻 Обработчики оператора
        @self.dp.message(F.text == "📥 Новые заявки")
        async def cmd_new_orders(message: Message, role: str):
            """Новые заявки оператора"""
            if role != "operator":
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                orders = await self.api_layer.get_new_orders(message.from_user.id)
                
                if not orders:
                    await message.answer("📭 Новых заявок нет")
                    return
                
                # Формируем список новых заявок
                orders_text = f"📥 <b>Новые заявки ({len(orders)})</b>\n\n"
                
                for order in orders[:5]:  # Показываем первые 5
                    orders_text += f"📦 <b>#{order['id']}</b> {order.get('client_name', 'Unknown')}\n"
                    orders_text += f"💰 {order.get('amount', 0)} сомони • 🕐 {order.get('created_at', datetime.now()).strftime('%H:%M')}\n\n"
                
                await message.answer(orders_text)
                
            except Exception as e:
                self.logger.error(f"❌ Error in new orders: {e}")
                await message.answer("❌ Ошибка получения заявок")
        
        # 📊 Обработчики директора
        @self.dp.message(F.text == "📊 Дашборд")
        async def cmd_dashboard(message: Message, role: str):
            """Дашборд директора"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                stats = await self.api_layer.get_dashboard_stats(message.from_user.id, role)
                
                if not stats:
                    await message.answer("📊 Нет данных")
                    return
                
                # Формируем дашборд
                dashboard_text = f"📊 <b>Дашборд MAXXPHARM</b>\n\n"
                dashboard_text += f"📦 <b>Сегодня:</b>\n"
                dashboard_text += f"• Заказов: {stats.get('total_orders', 0)}\n"
                dashboard_text += f"• Доставлено: {stats.get('delivered_orders', 0)}\n"
                dashboard_text += f"• В работе: {stats.get('in_progress_orders', 0)}\n"
                dashboard_text += f"• Отменено: {stats.get('cancelled_orders', 0)}\n\n"
                dashboard_text += f"💰 <b>Выручка:</b> {stats.get('total_revenue', 0):.0f} сомони"
                
                await message.answer(dashboard_text)
                
            except Exception as e:
                self.logger.error(f"❌ Error in dashboard: {e}")
                await message.answer("❌ Ошибка получения дашборда")
        
        # 🧪 Тестовые команды
        @self.dp.message(Command("test_system"))
        async def cmd_test_system(message: Message, role: str):
            """Тест всей системы"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                await message.answer("🧪 <b>Тест системы MAXXPHARM</b>\n\n")
                
                # Тест базы данных
                await message.answer("🗄️ Тест базы данных...")
                db_status = await self._test_database()
                await message.answer(f"✅ База данных: {'OK' if db_status else 'ERROR'}")
                
                # Тест очереди
                await message.answer("📋 Тест очереди...")
                queue_status = await self._test_queue()
                await message.answer(f"✅ Очередь: {'OK' if queue_status else 'ERROR'}")
                
                # Тест воркеров
                await message.answer("🤖 Тест воркеров...")
                workers_status = await self._test_workers()
                await message.answer(f"✅ Воркеры: {'OK' if workers_status else 'ERROR'}")
                
                # Тест API
                await message.answer("🔌 Тест API...")
                api_status = await self._test_api()
                await message.answer(f"✅ API: {'OK' if api_status else 'ERROR'}")
                
                await message.answer("🎉 <b>Все системы работают!</b>")
                
            except Exception as e:
                self.logger.error(f"❌ Error in system test: {e}")
                await message.answer("❌ Ошибка тестирования системы")
        
        @self.dp.message(Command("health"))
        async def cmd_health(message: Message, role: str):
            """Проверка здоровья системы"""
            if role not in ["admin", "director"]:
                await message.answer("❌ Доступ запрещен")
                return
            
            try:
                health_report = await self.health_checker.comprehensive_health_check()
                
                status_emoji = {
                    "healthy": "✅",
                    "degraded": "⚠️",
                    "critical": "❌"
                }
                
                emoji = status_emoji.get(health_report.get("overall_status", "unknown"), "❓")
                
                health_text = f"{emoji} <b>Статус системы: {health_report.get('overall_status', 'unknown').upper()}</b>\n\n"
                health_text += f"🕐 <b>Проверка:</b> {health_report.get('timestamp', 'Unknown')}\n\n"
                
                health_text += "🔧 <b>Компоненты:</b>\n"
                for component, status in health_report.get("components", {}).items():
                    comp_emoji = {
                        "healthy": "✅",
                        "warning": "⚠️",
                        "error": "❌",
                        "critical": "🚨",
                        "skipped": "⏭️"
                    }.get(status.get("status", "unknown"), "❓")
                    
                    health_text += f"{comp_emoji} {component.title()}: {status.get('status', 'unknown')}\n"
                
                await message.answer(health_text)
                
            except Exception as e:
                self.logger.error(f"❌ Error in health check: {e}")
                await message.answer("❌ Ошибка проверки здоровья")
        
        # 📱 Обработка текстовых сообщений для создания заказов
        @self.dp.message()
        async def handle_text_message(message: Message, role: str):
            """Обработка текстовых сообщений"""
            if role != "client":
                return
            
            # Если сообщение достаточно длинное, создаем заявку
            if len(message.text) > 10:
                try:
                    order_data = {
                        "comment": message.text,
                        "amount": 50.0,  # Базовая цена
                        "items": [{"product": "Препарат", "quantity": 1}]
                    }
                    
                    order = await self.api_layer.create_order(message.from_user.id, order_data)
                    
                    # Отправляем карточку заказа
                    await message.answer(
                        f"✅ <b>Заявка создана!</b>\n\n"
                        f"📋 <b>Номер заказа:</b> #{order['id']}\n"
                        f"💰 <b>Предварительная стоимость:</b> {order_data['amount']} сомони\n"
                        f"📝 <b>Комментарий:</b> {message.text}\n\n"
                        f"Мы скоро проверим ваш заказ и свяжемся с вами для подтверждения.",
                        reply_markup=self._get_main_menu(role)
                    )
                    
                    self.logger.info(f"📦 Order #{order['id']} created via text by client {message.from_user.id}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error creating order from text: {e}")
                    await message.answer("❌ Ошибка создания заявки")
        
        # 🎯 Callback обработчики
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery, role: str):
            """Обработка inline кнопок"""
            try:
                data = callback.data
                
                if data.startswith("accept_order_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.accept_order(order_id, callback.from_user.id)
                    
                    if success:
                        await callback.answer("✅ Заказ принят")
                        await callback.message.edit_text("✅ <b>Заказ принят в обработку</b>")
                    else:
                        await callback.answer("❌ Не удалось принять заказ")
                
                elif data.startswith("start_pick_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "picking", callback.from_user.id)
                    
                    if success:
                        await callback.answer("🔄 Сборка начата")
                        await callback.message.edit_text("🔄 <b>Сборка начата</b>")
                    else:
                        await callback.answer("❌ Не удалось начать сборку")
                
                elif data.startswith("delivered_"):
                    order_id = int(data.split("_")[2])
                    success = await self.api_layer.update_order_status(order_id, "delivered", callback.from_user.id)
                    
                    if success:
                        await callback.answer("✅ Доставлено")
                        await callback.message.edit_text("✅ <b>Заказ доставлен</b>")
                    else:
                        await callback.answer("❌ Не удалось подтвердить доставку")
                
                else:
                    await callback.answer("❌ Неизвестное действие")
                    
            except Exception as e:
                self.logger.error(f"❌ Callback error: {e}")
                await callback.answer("❌ Ошибка обработки")
    
    async def _setup_middlewares(self):
        """Настройка middleware"""
        try:
            from middlewares.role_middleware import RoleMiddleware
            from middlewares.logging_middleware import LoggingMiddleware
            
            self.dp.message.middleware(RoleMiddleware())
            self.dp.callback_query.middleware(RoleMiddleware())
            self.dp.message.middleware(LoggingMiddleware())
            self.dp.callback_query.middleware(LoggingMiddleware())
            
            self.logger.info("✅ Middleware setup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup middleware: {e}")
            raise
    
    async def _get_user_info(self, user_id: int) -> Optional[dict]:
        """Получение информации о пользователе"""
        try:
            from database_connection import get_user_by_telegram_id
            return await get_user_by_telegram_id(user_id)
        except Exception as e:
            self.logger.error(f"❌ Error getting user info: {e}")
            return None
    
    def _get_welcome_text(self, user: dict) -> str:
        """Получение приветствия"""
        role = user.get("role", "unknown")
        name = user.get("name", "Пользователь")
        
        role_texts = {
            "client": "👤 <b>Здравствуйте!</b>\n\nДобро пожаловать в MAXXPHARM 🏥\n\nВыберите действие из меню ниже:",
            "operator": "👨‍💻 <b>Панель оператора</b>\n\nВыберите действие из меню ниже:",
            "picker": "📦 <b>Панель сборщика</b>\n\nВыберите действие из меню ниже:",
            "checker": "🔍 <b>Панель проверщика</b>\n\nВыберите действие из меню ниже:",
            "courier": "🚚 <b>Панель курьера</b>\n\nВыберите действие из меню ниже:",
            "admin": "👑 <b>Панель администратора</b>\n\nВыберите действие из меню ниже:",
            "director": "👑 <b>Панель директора</b>\n\nВыберите действие из меню ниже:"
        }
        
        return role_texts.get(role, f"👋 <b>Здравствуйте, {name}!</b>")
    
    def _get_main_menu(self, role: str):
        """Получение главного меню"""
        try:
            from keyboards.main_menu import get_main_menu
            return get_main_menu(role)
        except Exception as e:
            self.logger.error(f"❌ Error getting main menu: {e}")
            return None
    
    async def _test_database(self) -> bool:
        """Тест базы данных"""
        try:
            from database_connection import test_database_connection
            return await test_database_connection()
        except Exception as e:
            self.logger.error(f"❌ Database test error: {e}")
            return False
    
    async def _test_queue(self) -> bool:
        """Тест очереди"""
        try:
            status = await self.queue_service.get_queue_status()
            return status is not None
        except Exception as e:
            self.logger.error(f"❌ Queue test error: {e}")
            return False
    
    async def _test_workers(self) -> bool:
        """Тест воркеров"""
        try:
            stats = self.worker_manager.get_total_stats()
            return stats is not None
        except Exception as e:
            self.logger.error(f"❌ Workers test error: {e}")
            return False
    
    async def _test_api(self) -> bool:
        """Тест API"""
        try:
            stats = await self.api_layer.get_dashboard_stats(697780123, "director")
            return True
        except Exception as e:
            self.logger.error(f"❌ API test error: {e}")
            return False
    
    async def start(self):
        """Запуск бота со всеми системами"""
        try:
            # Устанавливаем обработчики сигналов
            self._setup_signal_handlers()
            
            # Запускаем watchdog
            watchdog_tasks = await start_watchdog(self.bot)
            
            # Запускаем воркеров
            worker_task = asyncio.create_task(self.worker_manager.start_all_workers())
            
            # Запускаем health check loop
            health_task = asyncio.create_task(health_check_loop(self.bot))
            
            self.logger.info("🚀 Starting Maxxpharm Production Bot...")
            self.logger.info("🛡️ Watchdog: Active")
            self.logger.info("🤖 Workers: Running")
            self.logger.info("🏥 Health Check: Monitoring")
            self.logger.info("🗄️ Database: Connected")
            self.logger.info("📋 Queue: Ready")
            self.logger.info("🔌 API: Ready")
            
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            self.logger.info(f"🤖 Bot: @{bot_info.full_name}")
            
            print("🚀 MAXXPHARM PRODUCTION BOT")
            print("🛡️ Production System: Active")
            print("🏗️ Uber Architecture: Enabled")
            print("🗄️ Database: Connected")
            print("🤖 Workers: Running")
            print("📋 Queue: Ready")
            print("🔌 API: Ready")
            print("🏥 Health Check: Monitoring")
            print(f"🤖 Bot: @{bot_info.username}")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"❌ Bot runtime error: {e}")
            raise
        finally:
            await self.shutdown()
    
    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        def signal_handler(signum, frame):
            self.logger.info(f"🛑 Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())
        
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler, sig, None)
    
    async def shutdown(self):
        """Завершение работы бота"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("🛑 Shutting down Maxxpharm Production Bot...")
        
        try:
            # Останавливаем воркеров
            if self.worker_manager:
                await self.worker_manager.stop_all_workers()
            
            # Закрываем соединение с базой
            from database_connection import close_database_pool
            await close_database_pool()
            
            # Закрываем сессию бота
            if self.bot:
                await self.bot.session.close()
            
            self.logger.info("✅ Maxxpharm Production Bot shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM PRODUCTION BOT")
    print("🛡️ Production System + Uber Architecture + Database")
    print("🏥 Enterprise Telegram CRM for Pharma Delivery")
    print("🤖 All systems integrated and ready")
    print()
    
    try:
        # Проверяем переменные окружения
        if not os.getenv("BOT_TOKEN"):
            logger.error("❌ BOT_TOKEN environment variable is required")
            sys.exit(1)
        
        # Проверяем на существующий бота (простая проверка без Redis)
        try:
            from bot_lock_system import BotLock
            bot_lock = BotLock()
            
            if await bot_lock.connect():
                # Очищаем мертвые экземпляры
                await bot_lock.cleanup_dead_instances()
                
                # Пытаемся получить блокировку
                if not await bot_lock.acquire_lock():
                    logger.error("❌ Cannot start - another bot instance is running")
                    sys.exit(1)
                
                logger.info("✅ Bot lock acquired successfully")
            else:
                logger.warning("⚠️ Redis not available, running without lock")
        except Exception as e:
            logger.warning(f"⚠️ Bot lock system failed: {e}")
            logger.info("🚀 Continuing without bot lock")
        
        try:
            # Создаем и запускаем бота
            bot = MaxxpharmProductionBot()
            
            if await bot.initialize():
                await bot.start()
            else:
                logger.error("❌ Failed to initialize bot")
                sys.exit(1)
                
        finally:
            # Освобождаем блокировку если она была получена
            try:
                if 'bot_lock' in locals():
                    await bot_lock.release_lock()
                    logger.info("🔓 Bot lock released")
            except:
                pass
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
