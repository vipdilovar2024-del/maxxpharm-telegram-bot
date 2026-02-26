from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import logging

from src.config import settings
from src.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maxxpharm Bot Health Check")


@asynccontextmanager
async def lifespan(app):
    # Startup
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Health check service shutting down...")


@app.get("/")
async def root():
    return {"status": "healthy", "service": "maxxpharm-telegram-bot"}


@app.get("/health")
async def health():
    try:
        # Test database connection
        from src.database import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "bot_token": "configured" if settings.BOT_TOKEN else "missing",
            "admin_id": settings.ADMIN_TELEGRAM_ID
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected"
        }


if __name__ == "__main__":
    uvicorn.run(
        "health_check:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
