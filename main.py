import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import init_db, get_session
from src.handlers.common_handlers import CommonHandlers
from src.handlers.client_handlers import ClientHandlers
from src.handlers.admin_handlers import AdminHandlers
from src.handlers.manager_handlers import ManagerHandlers
from src.handlers.courier_handlers import CourierHandlers


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Maxxpharm Telegram Bot...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Set bot commands
        await set_bot_commands()
        logger.info("✅ Bot commands set successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Shutting down Maxxpharm Telegram Bot...")


async def set_bot_commands():
    """Set bot commands"""
    bot = Bot(token=settings.BOT_TOKEN)
    
    commands = [
        types.BotCommand(command="/start", description="🚀 Начать работу"),
        types.BotCommand(command="/help", description="🆘 Помощь"),
        types.BotCommand(command="/cancel", description="❌ Отменить действие"),
    ]
    
    await bot.set_my_commands(commands)
    await bot.session.close()


async def create_sample_data():
    """Create sample data for testing"""
    async for session in get_session():
        from src.services.user_service import UserService
        from src.services.product_service import ProductService
        from src.services.category_service import CategoryService
        
        user_service = UserService(session)
        product_service = ProductService(session)
        category_service = CategoryService(session)
        
        # Create sample categories
        categories_data = [
            {"name": "Лекарства от давления", "description": "Гипотензивные препараты"},
            {"name": "Витамины", "description": "Витаминные комплексы"},
            {"name": "Антибиотики", "description": "Антибактериальные препараты"},
            {"name": "Болеутоляющие", "description": "Обезболивающие средства"}
        ]
        
        for cat_data in categories_data:
            existing = await category_service.get_category_by_name(cat_data["name"])
            if not existing:
                await category_service.create_category(
                    name=cat_data["name"],
                    description=cat_data["description"]
                )
        
        # Create sample products
        products_data = [
            {"name": "Лозап 10мг", "price": 45000, "stock_quantity": 50, "category_name": "Лекарства от давления"},
            {"name": "Витамин C 500мг", "price": 12000, "stock_quantity": 100, "category_name": "Витамины"},
            {"name": "Амоксициллин 500мг", "price": 25000, "stock_quantity": 30, "category_name": "Антибиотики"},
            {"name": "Нурофен 400мг", "price": 18000, "stock_quantity": 75, "category_name": "Болеутоляющие"}
        ]
        
        for prod_data in products_data:
            category = await category_service.get_category_by_name(prod_data["category_name"])
            if category:
                existing = await product_service.get_product_by_name(prod_data["name"])
                if not existing:
                    await product_service.create_product(
                        name=prod_data["name"],
                        price=prod_data["price"],
                        category_id=category.id,
                        stock_quantity=prod_data["stock_quantity"]
                    )
        
        logger.info("✅ Sample data created successfully")


async def main():
    """Main application function"""
    async with lifespan():
        # Initialize bot and dispatcher
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        )
        
        dp = Dispatcher()
        
        # Register handlers
        common_handlers = CommonHandlers(dp)
        client_handlers = ClientHandlers(dp)
        admin_handlers = AdminHandlers(dp)
        manager_handlers = ManagerHandlers(dp)
        courier_handlers = CourierHandlers(dp)
        
        # Create sample data if needed
        await create_sample_data()
        
        # Start polling
        logger.info(f"🤖 Bot started successfully. Admin ID: {settings.ADMIN_TELEGRAM_ID}")
        
        try:
            await dp.start_polling(
                bot,
                handle_signals=False,
                on_startup=lambda dispatcher: logger.info("🚀 Bot polling started"),
                on_shutdown=lambda dispatcher: logger.info("🛑 Bot polling stopped")
            )
        except Exception as e:
            logger.error(f"❌ Polling error: {e}")
        finally:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
