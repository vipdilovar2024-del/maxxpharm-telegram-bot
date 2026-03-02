#!/usr/bin/env python3
"""
Run.py - final working bot
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

async def main():
    try:
        # Create bot
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()
        
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted")
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: {bot_info.full_name} (@{bot_info.username})")
        
        @dp.message(Command("start"))
        async def start_handler(message):
            logger.info(f"📨 Got /start from {message.from_user.id}")
            await message.answer("🚀 SOLIMPHARM Bot работает!")
            logger.info("✅ Replied to /start")
        
        @dp.message()
        async def echo_handler(message):
            logger.info(f"📨 Got message: {message.text}")
            await message.answer(f"Echo: {message.text}")
            logger.info("✅ Replied with echo")
        
        # Start polling
        logger.info("🤖 Starting polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
