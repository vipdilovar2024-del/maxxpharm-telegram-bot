"""
🏗️ Config - Конфигурация MAXXPHARM CRM
"""

import os
from typing import Optional

# 🤖 Bot Configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

# 🗄️ Database Configuration
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost/crm"
)

DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
DB_NAME: str = os.getenv("DB_NAME", "crm")

# 🧠 AI Configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

# 🔄 Redis Configuration
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 📊 Environment
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

# 🏗️ Production settings
PRODUCTION_MODE: bool = ENVIRONMENT == "production"

# 📊 Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# 🎯 CRM Configuration
MAX_ORDERS_PER_WORKER: int = int(os.getenv("MAX_ORDERS_PER_WORKER", "5"))
ORDER_TIMEOUT_MINUTES: int = int(os.getenv("ORDER_TIMEOUT_MINUTES", "30"))

# 🔔 Notification settings
ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "True").lower() == "true"

# 🧠 AI Configuration
AI_ENABLED: bool = bool(OPENAI_API_KEY)
DAILY_REPORT_TIME: str = os.getenv("DAILY_REPORT_TIME", "09:00")
