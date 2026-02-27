#!/usr/bin/env python3
"""
Debug startup - check what's happening
"""

import asyncio
import logging
import os
import sys
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def health_handler(request):
    """Health check endpoint"""
    logger.info("🔍 Health check requested")
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Debug mode - service is running",
        "python_version": sys.version,
        "environment": os.environ.get('RENDER', 'unknown')
    })

async def root_handler(request):
    """Root endpoint"""
    logger.info("🔍 Root endpoint requested")
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Debug mode - bot service active"
    })

async def create_app():
    """Create web application"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    return app

async def start_health_server():
    """Start health check server"""
    logger.info("🚀 Starting debug health server...")
    
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

async def test_telegram_bot():
    """Test if we can connect to Telegram"""
    logger.info("🤖 Testing Telegram bot connection...")
    
    try:
        from aiogram import Bot
        BOT_TOKEN = "8357898408:AAEA5TBDYO9cf9tjbCu6ZcrvPQxy9j28KGI"
        
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        
        logger.info(f"✅ Bot info: {bot_info.full_name} (@{bot_info.username})")
        logger.info(f"🆔 Bot ID: {bot_info.id}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Telegram bot test failed: {e}")
        return False

async def main():
    """Main debug function"""
    logger.info("🐛 Starting debug mode...")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Current directory: {os.getcwd()}")
    logger.info(f"🌍 Environment: {os.environ.get('RENDER', 'local')}")
    
    # Test Telegram connection
    telegram_ok = await test_telegram_bot()
    
    # Start health server
    health_runner = await start_health_server()
    
    # Keep running
    try:
        while True:
            logger.info("💤 Debug server is running... (checking every 30s)")
            await asyncio.sleep(30)
            
            # Test Telegram connection periodically
            if telegram_ok:
                logger.info("✅ Telegram connection OK")
            else:
                logger.warning("⚠️ Telegram connection failed")
                
    except asyncio.CancelledError:
        logger.info("🛑 Debug server stopped")
    finally:
        await health_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Debug stopped by user")
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
