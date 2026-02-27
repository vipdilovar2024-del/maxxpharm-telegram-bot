#!/usr/bin/env python3
"""
Simple start - just to test if file runs
"""

import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Got /start from {message.from_user.id}")
    await message.answer("🚀 Bot is working!")

@dp.message()
async def echo(message: types.Message):
    logger.info(f"Got message: {message.text}")
    await message.answer(f"Echo: {message.text}")

async def health_handler(request):
    return web.json_response({"status": "healthy", "bot": "running"})

async def main():
    logger.info("🚀 SIMPLE START - Bot is starting...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Directory: {os.getcwd()}")
    
    # Test bot
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot: {bot_info.full_name}")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        return
    
    # Health server
    app = web.Application()
    app.router.add_get('/health', health_handler)
    port = int(os.environ.get('PORT', 8000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Health server on port {port}")
    logger.info("🤖 Starting polling...")
    
    # Start bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
