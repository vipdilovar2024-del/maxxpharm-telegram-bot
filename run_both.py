#!/usr/bin/env python3
"""
Run both simple bot and health server
"""

import asyncio
import logging
import os
from aiohttp import web

# Import simple bot
from simple_test_bot import main as bot_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health server functions
async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "bot_running": True,
        "message": "Simple test bot is running"
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Simple test bot is active"
    })

async def create_health_app():
    """Create web application"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    return app

async def start_health_server():
    """Start health check server"""
    app = await create_health_app()
    port = int(os.environ.get('PORT', 8000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Health server started on port {port}")
    logger.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    
    return runner

async def main():
    """Run both bot and health server"""
    logger.info("🚀 Starting simple test bot with health check...")
    
    # Start health server
    health_runner = await start_health_server()
    
    try:
        # Start bot
        await bot_main()
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        await health_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
