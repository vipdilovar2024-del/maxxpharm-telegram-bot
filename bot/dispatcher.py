"""
🏗️ Dispatcher - Настройка диспетчера с обработчиками
"""

import logging
from aiogram import Dispatcher
from aiogram.filters import Command

# Импортируем обработчики
from handlers import client, operator, picker, checker, courier, admin
from middlewares.role_middleware import RoleMiddleware
from middlewares.logging_middleware import LoggingMiddleware

logger = logging.getLogger(__name__)

async def setup_dispatcher(dp: Dispatcher) -> None:
    """Настройка диспетчера с обработчиками и middleware"""
    
    # Добавляем middleware
    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Включаем роутеры обработчиков
    dp.include_router(client.router)
    dp.include_router(operator.router)
    dp.include_router(picker.router)
    dp.include_router(checker.router)
    dp.include_router(courier.router)
    dp.include_router(admin.router)
    
    # Обработчик команды /start
    @dp.message(Command("start"))
    async def cmd_start(message, role: str):
        """Обработчик команды /start"""
        from handlers.client import cmd_start as client_start
        from handlers.operator import cmd_start as operator_start
        from handlers.picker import cmd_start as picker_start
        from handlers.checker import cmd_start as checker_start
        from handlers.courier import cmd_start as courier_start
        from handlers.admin import cmd_start as admin_start
        
        # Вызываем соответствующий обработчик в зависимости от роли
        if role == "client":
            await client_start(message)
        elif role == "operator":
            await operator_start(message)
        elif role == "picker":
            await picker_start(message)
        elif role == "checker":
            await checker_start(message)
        elif role == "courier":
            await courier_start(message)
        elif role in ["admin", "director"]:
            await admin_start(message)
        else:
            await message.answer("❌ Роль не определена")
    
    logger.info("✅ Dispatcher setup completed")
    logger.info("📋 Handlers registered:")
    logger.info("  - Client handlers")
    logger.info("  - Operator handlers") 
    logger.info("  - Picker handlers")
    logger.info("  - Checker handlers")
    logger.info("  - Courier handlers")
    logger.info("  - Admin handlers")
    logger.info("🔧 Middleware configured:")
    logger.info("  - RoleMiddleware")
    logger.info("  - LoggingMiddleware")
