"""
🏗️ Main Bot File - Главный файл для MAXXPHARM CRM
Интеграция с существующим aiogram 3.4.1 ботом
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем конфигурацию
from bot.config import BOT_TOKEN, ADMIN_ID
from bot.dispatcher import setup_dispatcher

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Основная функция бота"""
    
    # Создаем бот с настройками для aiogram 3.4.1
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            protect_content=True
        )
    )
    
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Настраиваем диспетчер с обработчиками
    await setup_dispatcher(dp)
    
    # Удаляем webhook и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🚀 MAXXPHARM CRM Bot starting...")
    logger.info(f"🤖 Bot: @{(await bot.get_me()).username}")
    logger.info("🏗️ Production structure loaded")
    
    try:
        # Запускаем polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot runtime error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
