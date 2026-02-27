#!/usr/bin/env python3
"""
Final working bot - minimal and reliable
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
ADMIN_ID = 697780123

# Create bot and dispatcher
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    logger.info(f"📨 RECEIVED /start from user {message.from_user.id}")
    
    try:
        await message.answer(
            "🚀 <b>SOLIMPHARM Bot работает!</b>\n\n"
            f"👤 Ваш ID: <code>{message.from_user.id}</code>\n"
            f"📛 Имя: {message.from_user.full_name}\n\n"
            "✅ Бот отвечает на команды!"
        )
        logger.info(f"✅ REPLIED to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR replying: {e}")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    logger.info(f"📨 RECEIVED /help from user {message.from_user.id}")
    
    try:
        await message.answer(
            "🆘 <b>Помощь SOLIMPHARM</b>\n\n"
            "📋 Команды:\n"
            "• /start - Запуск\n"
            "• /help - Помощь\n\n"
            "✅ Бот работает!"
        )
        logger.info(f"✅ REPLIED with help to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR sending help: {e}")

@dp.message()
async def echo_message(message: types.Message):
    """Echo all messages"""
    logger.info(f"📨 RECEIVED message: {message.text}")
    
    try:
        await message.answer(
            f"📨 <b>Эхо:</b>\n\n"
            f"💬 {message.text}\n\n"
            f"👤 {message.from_user.full_name}\n"
            f"🆔 {message.from_user.id}\n\n"
            f"✅ Бот работает!"
        )
        logger.info(f"✅ REPLIED with echo to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR echoing: {e}")

# Health check
async def health_handler(request):
    """Health check endpoint"""
    logger.info("🔍 Health check requested")
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "bot_running": True,
        "message": "Final bot is working"
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "SOLIMPHARM bot is active"
    })

async def create_app():
    """Create web application"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    return app

async def start_health_server():
    """Start health check server"""
    logger.info("🌐 Starting health server...")
    
    app = await create_app()
    port = int(os.environ.get('PORT', 8000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Health server running on port {port}")
    logger.info(f"🔗 Health: http://0.0.0.0:{port}/health")
    
    return runner

async def main():
    """Main function"""
    logger.info("🚀 STARTING FINAL SOLIMPHARM BOT")
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"📁 Directory: {os.getcwd()}")
    logger.info(f"🌍 Render: {os.environ.get('RENDER', 'False')}")
    
    # Test bot connection
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ BOT INFO: {bot_info.full_name} (@{bot_info.username})")
        logger.info(f"🆔 BOT ID: {bot_info.id}")
    except Exception as e:
        logger.error(f"❌ BOT CONNECTION ERROR: {e}")
        return
    
    # Start health server
    health_runner = await start_health_server()
    
    # Start bot polling
    logger.info("🤖 STARTING BOT POLLING...")
    logger.info("👂 Bot is now listening for messages...")
    
    try:
        await dp.start_polling(
            bot,
            handle_signals=False
        )
    except Exception as e:
        logger.error(f"❌ POLLING ERROR: {e}")
    finally:
        await bot.session.close()
        await health_runner.cleanup()

if __name__ == "__main__":
    try:
        logger.info("🎯 RUNNING FINAL BOT")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
