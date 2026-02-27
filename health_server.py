#!/usr/bin/env python3
"""
Simple HTTP server for health check
"""

import asyncio
import logging
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "bot_running": True
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Bot is running"
    })

async def create_app():
    """Create web application"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    return app

async def start_health_server():
    """Start health server"""
    app = await create_app()
    
    # Render provides port via environment variable
    port = int(os.environ.get('PORT', 8000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 Health server started on port {port}")
    logger.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    
    # Keep server running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except asyncio.CancelledError:
        logger.info("🛑 Health server stopped")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    import os
    try:
        asyncio.run(start_health_server())
    except KeyboardInterrupt:
        logger.info("🛑 Health server stopped by user")
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")
