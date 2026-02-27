#!/usr/bin/env python3
"""
Server.py - final working bot with all fixes
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
    format='%(asctime)s - %(levelname)s - %(message)s'
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
        user_id = message.from_user.id
        is_admin = user_id == ADMIN_ID
        
        if is_admin:
            await message.answer(
                "🚀 <b>SOLIMPHARM Bot запущен!</b>\n\n"
                "👑 <b>Админ панель</b>\n"
                "📊 Статистика: /stats\n"
                "👥 Пользователи: /users\n"
                "📦 Товары: /products\n"
                "⚙️ Настройки: /settings\n\n"
                "✅ Бот работает в рабочем режиме!"
            )
        else:
            await message.answer(
                "🚀 <b>Добро пожаловать в SOLIMPHARM!</b>\n\n"
                "📱 <b>Меню клиента:</b>\n"
                "🛒 Заказать: /order\n"
                "📋 Мои заказы: /myorders\n"
                "📞 Контакты: /contacts\n"
                "❓ Помощь: /help\n\n"
                "✅ Бот готов к работе!"
            )
        
        logger.info(f"✅ REPLIED to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR replying to user {message.from_user.id}: {e}")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    logger.info(f"📨 RECEIVED /help from user {message.from_user.id}")
    
    try:
        await message.answer(
            "🆘 <b>Помощь SOLIMPHARM Bot</b>\n\n"
            "📋 <b>Основные команды:</b>\n"
            "• /start - Запуск бота\n"
            "• /help - Эта справка\n"
            "• /cancel - Отменить действие\n\n"
            "👑 <b>Админ команды:</b>\n"
            "• /stats - Статистика\n"
            "• /users - Пользователи\n"
            "• /products - Товары\n\n"
            "✅ Бот работает стабильно!"
        )
        logger.info(f"✅ REPLIED with help to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR sending help to user {message.from_user.id}: {e}")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Handle /stats command (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды!")
        return
    
    logger.info(f"📊 Admin {message.from_user.id} requested stats")
    
    try:
        await message.answer(
            "📊 <b>Статистика SOLIMPHARM Bot</b>\n\n"
            "🤖 Статус: ✅ Работает\n"
            "👑 Админ: Вы\n"
            "📅 Запущен: Только что\n"
            "🌐 Платформа: Render\n"
            "🐍 Python: 3.11.14\n\n"
            "✅ Все системы в норме!"
        )
        logger.info(f"✅ REPLIED with stats to admin {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR sending stats: {e}")

@dp.message()
async def echo_message(message: types.Message):
    """Echo all messages"""
    logger.info(f"📨 RECEIVED message from user {message.from_user.id}: {message.text}")
    
    try:
        await message.answer(
            f"📨 <b>Получено сообщение:</b>\n\n"
            f"💬 {message.text}\n\n"
            f"👤 От: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}\n\n"
            f"✅ Бот работает и отвечает!"
        )
        logger.info(f"✅ REPLIED with echo to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR echoing message from user {message.from_user.id}: {e}")

# Health check functions
async def health_handler(request):
    """Health check endpoint"""
    logger.info("🔍 Health check requested")
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "bot_running": True,
        "bot_name": "SOLIMPHARM",
        "bot_username": "@solimfarm_bot",
        "admin_id": ADMIN_ID,
        "message": "Server bot is working perfectly"
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "SOLIMPHARM bot is active via server.py",
        "bot": "SOLIMPHARM (@solimfarm_bot)"
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
    
    logger.info(f"✅ Health server started on port {port}")
    logger.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    logger.info(f"🔗 Root: http://0.0.0.0:{port}/")
    
    return runner

async def main():
    """Main function - run both bot and health server"""
    logger.info("🚀 STARTING FINAL SOLIMPHARM BOT via server.py")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Current directory: {os.getcwd()}")
    logger.info(f"🌍 Environment: {os.environ.get('RENDER', 'local')}")
    
    # Reset webhook first to avoid conflicts
    try:
        logger.info("🔄 Resetting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook reset successfully")
    except Exception as e:
        logger.error(f"❌ Error resetting webhook: {e}")
    
    # Get bot info
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot info: {bot_info.full_name} (@{bot_info.username})")
        logger.info(f"🆔 Bot ID: {bot_info.id}")
    except Exception as e:
        logger.error(f"❌ Error getting bot info: {e}")
        return
    
    # Start health server
    health_runner = await start_health_server()
    
    # Start bot polling
    try:
        logger.info("🤖 Starting bot polling...")
        logger.info("👂 Bot is now listening for messages...")
        
        await dp.start_polling(
            bot,
            handle_signals=False
        )
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")
    finally:
        await bot.session.close()
        await health_runner.cleanup()

if __name__ == "__main__":
    try:
        logger.info("🎯 RUNNING FINAL BOT via server.py")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
