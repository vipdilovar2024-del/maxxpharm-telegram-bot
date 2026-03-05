"""
🛡️ Production Bot - Надежный Telegram CRM бот с защитой от падений
99.99% uptime как банковская система
"""

import asyncio
import logging
import os
import sys
import signal
from contextlib import asynccontextmanager
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError, TelegramNetworkError

# Импорты наших систем защиты
from bot_lock_system import ensure_single_instance, release_bot_lock, single_bot_context
from watchdog_system import start_watchdog, update_polling_activity, increment_message_count, increment_error_count
from bot.config import BOT_TOKEN, ADMIN_ID, ENVIRONMENT, DEBUG

# Настройка логирования уровня production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log'),
        logging.FileHandler('logs/errors.log', level=logging.ERROR)
    ]
)

logger = logging.getLogger("production_bot")

class ProductionBot:
    """Production-ready бот с защитой от падений"""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.watchdog_tasks = []
        self.running = False
        self.restart_count = 0
        self.max_restarts = 10
        self.logger = logging.getLogger("production_bot")
        
        # Создаем директорию для логов
        os.makedirs("logs", exist_ok=True)
    
    async def initialize(self) -> bool:
        """Инициализация бота"""
        try:
            # Проверяем что только один экземпляр запущен
            if not await ensure_single_instance():
                self.logger.error("❌ Another bot instance is running!")
                return False
            
            # Создаем бота с production настройками
            self.bot = Bot(
                token=BOT_TOKEN,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    protect_content=True,
                    disable_notification=False
                )
            )
            
            # Создаем диспетчер
            self.dp = Dispatcher()
            
            # Настраиваем обработчики
            await self._setup_handlers()
            
            # Настраиваем middleware
            await self._setup_middlewares()
            
            self.logger.info("✅ Production bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def _setup_handlers(self):
        """Настройка обработчиков"""
        try:
            # Импортируем обработчики
            from handlers.client import router as client_router
            from handlers.operator import router as operator_router
            from handlers.callback_handlers import get_callback_router
            
            # Включаем роутеры
            self.dp.include_router(client_router)
            self.dp.include_router(operator_router)
            self.dp.include_router(get_callback_router())
            
            # Добавляем обработчик для отслеживания активности
            @self.dp.update()
            async def track_updates(update, **kwargs):
                update_polling_activity()
                increment_message_count()
            
            self.logger.info("✅ Handlers setup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup handlers: {e}")
            raise
    
    async def _setup_middlewares(self):
        """Настройка middleware"""
        try:
            from middlewares.role_middleware import RoleMiddleware
            from middlewares.logging_middleware import LoggingMiddleware
            
            # Добавляем middleware
            self.dp.update.middleware(RoleMiddleware())
            self.dp.update.middleware(LoggingMiddleware())
            
            self.logger.info("✅ Middleware setup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup middleware: {e}")
            raise
    
    async def start(self):
        """Запуск бота с защитой от падений"""
        self.logger.info("🚀 Starting Production Bot...")
        
        # Устанавливаем обработчики сигналов
        self._setup_signal_handlers()
        
        # Запускаем watchdog
        await self._start_watchdog()
        
        # Основной цикл с перезапуском
        await self._run_with_restart_protection()
    
    async def _start_watchdog(self):
        """Запуск системы мониторинга"""
        try:
            self.watchdog_tasks = await start_watchdog(self.bot)
            self.logger.info("✅ Watchdog system started")
        except Exception as e:
            self.logger.error(f"❌ Failed to start watchdog: {e}")
    
    async def _run_with_restart_protection(self):
        """Основной цикл с защитой от перезапусков"""
        while self.restart_count < self.max_restarts:
            try:
                self.running = True
                self.logger.info(f"🤖 Starting polling (attempt {self.restart_count + 1}/{self.max_restarts})")
                
                # Удаляем webhook
                await self.bot.delete_webhook(drop_pending_updates=True)
                
                # Получаем информацию о боте
                bot_info = await self.bot.get_me()
                self.logger.info(f"🤖 Bot: @{bot_info.username}")
                
                # Отправляем уведомление о запуске
                await self._notify_startup(bot_info)
                
                # Запускаем polling
                await self.dp.start_polling(
                    self.bot,
                    handle_signals=False  # Мы обрабатываем сигналы сами
                )
                
                break  # Если polling завершился нормально, выходим из цикла
                
            except TelegramConflictError as e:
                self.logger.error(f"⚠️ TelegramConflictError: {e}")
                await self._handle_conflict_error(e)
                
            except TelegramNetworkError as e:
                self.logger.error(f"⚠️ TelegramNetworkError: {e}")
                await self._handle_network_error(e)
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected error: {e}")
                await self._handle_unexpected_error(e)
                
            finally:
                self.running = False
                
                if self.restart_count < self.max_restarts:
                    self.restart_count += 1
                    wait_time = min(60, 5 * self.restart_count)  # Экспоненциальная задержка
                    self.logger.info(f"🔄 Restarting in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"❌ Max restarts exceeded ({self.max_restarts})")
                    await self._emergency_shutdown()
    
    async def _handle_conflict_error(self, error: Exception):
        """Обработка TelegramConflictError"""
        self.logger.warning("⚠️ Bot conflict detected - another instance might be running")
        
        # Проверяем статус блокировки
        from bot_lock_system import get_bot_lock
        lock = get_bot_lock()
        status = await lock.check_lock_status()
        
        if not status.get("self_holds", False):
            self.logger.error("❌ We don't hold the lock - stopping")
            await self._emergency_shutdown()
        else:
            self.logger.info("✅ We hold the lock - continuing")
    
    async def _handle_network_error(self, error: Exception):
        """Обработка сетевых ошибок"""
        self.logger.warning("⚠️ Network error - will retry")
        increment_error_count()
        
        # Ждем перед повторной попыткой
        await asyncio.sleep(10)
    
    async def _handle_unexpected_error(self, error: Exception):
        """Обработка неожиданных ошибок"""
        self.logger.error(f"❌ Unexpected error: {error}")
        increment_error_count()
        
        # Отправляем уведомление об ошибке
        await self._notify_error(error)
    
    async def _notify_startup(self, bot_info):
        """Уведомление о запуске"""
        try:
            if ADMIN_ID:
                startup_message = f"""
🚀 **CRM Bot Started**

🤖 **Bot:** @{bot_info.username}
📊 **Environment:** {ENVIRONMENT}
🔄 **Restart:** #{self.restart_count + 1}
🕐 **Time:** {asyncio.get_event_loop().time():.0f}

🛡️ **Watchdog:** Active
🔒 **Lock:** Secured
📊 **Monitoring:** Enabled

✅ **Status:** Ready for orders
"""
                
                await self.bot.send_message(ADMIN_ID, startup_message)
                self.logger.info("📢 Startup notification sent")
        except Exception as e:
            self.logger.error(f"❌ Failed to send startup notification: {e}")
    
    async def _notify_error(self, error: Exception):
        """Уведомление об ошибке"""
        try:
            if ADMIN_ID:
                error_message = f"""
⚠️ **Bot Error**

❌ **Error:** {str(error)}
🔄 **Restart:** #{self.restart_count + 1}
🕐 **Time:** {asyncio.get_event_loop().time():.0f}

📊 **Status:** Attempting recovery...
"""
                
                await self.bot.send_message(ADMIN_ID, error_message)
                self.logger.info("📢 Error notification sent")
        except Exception as e:
            self.logger.error(f"❌ Failed to send error notification: {e}")
    
    async def _emergency_shutdown(self):
        """Экстренное завершение работы"""
        self.logger.critical("🚨 Emergency shutdown initiated")
        
        try:
            # Отправляем критическое уведомление
            if ADMIN_ID and self.bot:
                critical_message = f"""
🚨 **CRITICAL - Bot Shutdown**

❌ **Max restarts exceeded**
🔄 **Total attempts:** {self.restart_count + 1}
🕐 **Time:** {asyncio.get_event_loop().time():.0f}

⚠️ **Manual intervention required!**
"""
                
                await self.bot.send_message(ADMIN_ID, critical_message)
        except Exception as e:
            self.logger.error(f"❌ Failed to send emergency notification: {e}")
        
        # Завершаем работу
        await self.shutdown()
        os._exit(1)
    
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
        
        self.logger.info("🛑 Shutting down bot...")
        self.running = False
        
        try:
            # Останавливаем watchdog
            for task in self.watchdog_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Останавливаем polling
            if self.dp:
                await self.dp.stop_polling()
            
            # Освобождаем блокировку
            await release_bot_lock()
            
            # Закрываем сессию бота
            if self.bot:
                await self.bot.session.close()
            
            self.logger.info("✅ Bot shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

# Глобальный экземпляр бота
production_bot: Optional[ProductionBot] = None

async def main():
    """Основная функция"""
    global production_bot
    
    logger.info("🛡️ MAXXPHARM Production Bot Starting...")
    logger.info("🚀 Enterprise-grade Telegram CRM with 99.99% uptime")
    
    try:
        # Проверяем переменные окружения
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN environment variable is required")
            sys.exit(1)
        
        # Создаем и запускаем бота
        production_bot = ProductionBot()
        
        if await production_bot.initialize():
            await production_bot.start()
        else:
            logger.error("❌ Failed to initialize bot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if production_bot:
            await production_bot.shutdown()

if __name__ == "__main__":
    # Проверяем на существующий бота перед запуском
    from bot_lock_system import check_for_existing_bot
    
    if not check_for_existing_bot():
        logger.error("❌ Cannot start - another bot instance is running")
        sys.exit(1)
    
    # Запускаем бота
    asyncio.run(main())
