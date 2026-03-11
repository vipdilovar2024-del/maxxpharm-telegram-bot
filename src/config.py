"""
🔧 Конфигурация MAXXPHARM CRM
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # 🤖 Telegram Settings
    bot_token: str = Field(..., env="BOT_TOKEN")
    admin_telegram_id: int = Field(..., env="ADMIN_TELEGRAM_ID")
    
    # 🗄️ Database Settings
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # 🤖 AI Settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # 📍 Geolocation Settings
    google_maps_api_key: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")
    
    # 🔐 Security Settings
    secret_key: str = Field("your-secret-key-here", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 🌐 Web Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = Field(False, env="DEBUG")
    
    # 📊 Business Settings
    max_orders_per_day: int = 2000
    order_timeout_minutes: int = 60
    delivery_radius_km: int = 50
    
    # 🏥 1C Integration
    onec_api_url: Optional[str] = Field(None, env="ONEC_API_URL")
    onec_api_key: Optional[str] = Field(None, env="ONEC_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()
