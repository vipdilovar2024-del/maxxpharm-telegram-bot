from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings configuration"""
    
    # Telegram Bot Settings
    BOT_TOKEN: str
    ADMIN_TELEGRAM_ID: int
    
    # Database Settings
    DATABASE_URL: str
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Render Settings
    RENDER: bool = False
    PORT: Optional[int] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
