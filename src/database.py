"""
🗄️ Управление базой данных MAXXPHARM CRM
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from .config import settings
from .models.database import Base

# Создание двигателя базы данных
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)
        
        # Создание индексов
        await create_indexes(conn)


async def create_indexes(conn) -> None:
    """Создание дополнительных индексов"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_locations_user_id ON locations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at)",
    ]
    
    for index_sql in indexes:
        await conn.execute(text(index_sql))


async def close_db() -> None:
    """Закрытие соединений с базой данных"""
    await engine.dispose()


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def create_session(self) -> AsyncSession:
        """Создание новой сессии"""
        return self.session_factory()
    
    async def health_check(self) -> bool:
        """Проверка здоровья базы данных"""
        try:
            async with self.create_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
    
    async def get_stats(self) -> dict:
        """Получение статистики базы данных"""
        try:
            async with self.create_session() as session:
                # Статистика пользователей
                users_result = await session.execute(text("SELECT COUNT(*) FROM users"))
                users_count = users_result.scalar()
                
                # Статистика заказов
                orders_result = await session.execute(text("SELECT COUNT(*) FROM orders"))
                orders_count = orders_result.scalar()
                
                # Статистика платежей
                payments_result = await session.execute(text("SELECT COUNT(*) FROM payments"))
                payments_count = payments_result.scalar()
                
                return {
                    "users": users_count,
                    "orders": orders_count,
                    "payments": payments_count,
                    "database_healthy": await self.health_check()
                }
        except Exception as e:
            return {
                "error": str(e),
                "database_healthy": False
            }


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()
