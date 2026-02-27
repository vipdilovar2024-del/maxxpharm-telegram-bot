#!/usr/bin/env python3
"""
Index.py - final working bot
"""

import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"

async def main():
    # Reset webhook first
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    
    # Create new bot instance
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    @dp.message(Command("start"))
    async def start_cmd(msg):
        await msg.answer("🚀 SOLIMPHARM Bot работает!")
        logger.info(f"Start from {msg.from_user.id}")
    
    @dp.message()
    async def echo(msg):
        await msg.answer(f"Echo: {msg.text}")
        logger.info(f"Message from {msg.from_user.id}")
    
    # Health server
    async def health(request):
        return web.json_response({"status": "ok"})
    
    app = web.Application()
    app.router.add_get('/health', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    logger.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
