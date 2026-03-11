"""
🏥 MAXXPHARM CRM - Основной файл приложения
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from .config import settings
from .database import init_db, close_db, db_manager
from .handlers.common import CommonHandlers
from .handlers.client import ClientHandlers
from .handlers.operator import OperatorHandlers
from .handlers.admin import AdminHandlers
from .handlers.courier import CourierHandlers


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Глобальные переменные
bot = None
dp = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("🚀 Starting MAXXPHARM CRM...")
    
    # Инициализация бота
    global bot, dp
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Инициализация диспетчера
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    await init_db()
    logger.info("✅ Database initialized")
    
    # Регистрация обработчиков
    await register_handlers()
    logger.info("✅ Handlers registered")
    
    # Запуск бота в фоновом режиме
    asyncio.create_task(start_bot_polling())
    
    logger.info("🚀 MAXXPHARM CRM started successfully!")
    
    yield
    
    # Остановка
    logger.info("🛑 Shutting down MAXXPHARM CRM...")
    await close_db()
    logger.info("✅ Database closed")


# Создание FastAPI приложения
app = FastAPI(
    title="MAXXPHARM CRM API",
    description="Professional Pharmacy Management System",
    version="1.0.0",
    lifespan=lifespan
)


async def register_handlers():
    """Регистрация всех обработчиков"""
    # Общие обработчики
    common_handlers = CommonHandlers()
    dp.include_router(common_handlers.router)
    
    # Обработчики клиентов
    client_handlers = ClientHandlers()
    dp.include_router(client_handlers.router)
    
    # Обработчики операторов
    operator_handlers = OperatorHandlers()
    dp.include_router(operator_handlers.router)
    
    # Обработчики администраторов
    admin_handlers = AdminHandlers()
    dp.include_router(admin_handlers.router)
    
    # Обработчики курьеров
    courier_handlers = CourierHandlers()
    dp.include_router(courier_handlers.router)
    
    logger.info("✅ All handlers registered")


async def start_bot_polling():
    """Запуск поллинга бота"""
    try:
        await dp.start_polling(
            bot,
            handle_signals=False,
            allowed_updates=["message", "callback_query"]
        )
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")


@app.post("/webhook")
async def webhook(request: Request):
    """Webhook для Telegram"""
    try:
        update_data = await request.json()
        update = Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    try:
        # Проверка базы данных
        db_healthy = await db_manager.health_check()
        
        # Проверка бота
        bot_healthy = False
        if bot:
            try:
                await bot.get_me()
                bot_healthy = True
            except:
                pass
        
        # Статистика
        stats = await db_manager.get_stats()
        
        return JSONResponse({
            "status": "healthy" if db_healthy and bot_healthy else "unhealthy",
            "database": db_healthy,
            "bot": bot_healthy,
            "stats": stats,
            "timestamp": asyncio.get_event_loop().time()
        })
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return JSONResponse({
        "service": "MAXXPHARM CRM",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "docs": "/docs"
        }
    })


@app.get("/stats")
async def get_stats():
    """Получение статистики системы"""
    try:
        stats = await db_manager.get_stats()
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
