#!/usr/bin/env python3
"""
Simple health check for Render
"""

import os
from aiohttp import web

async def health_handler(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Service is running"
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "maxxpharm-telegram-bot",
        "message": "Bot service is active"
    })

async def create_app():
    """Create web application"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_handler)
    return app

if __name__ == "__main__":
    import asyncio
    from aiohttp import web
    
    async def start_server():
        app = await create_app()
        port = int(os.environ.get('PORT', 8000))
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        print(f"🌐 Health server started on port {port}")
        print(f"🔗 Health check: http://0.0.0.0:{port}/health")
        
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            print("🛑 Health server stopped")
        finally:
            await runner.cleanup()
    
    asyncio.run(start_server())
