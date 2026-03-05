"""
🏗️ Database Connection - Подключение к базе данных
"""

import asyncpg
import logging
from typing import Optional

from bot.config import DATABASE_URL, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

# Глобальная переменная для подключения
_db_pool: Optional[asyncpg.Pool] = None

async def create_db_pool() -> asyncpg.Pool:
    """Создание пула подключений к базе данных"""
    
    try:
        # Используем DATABASE_URL если доступен, иначе собираем из параметров
        if DATABASE_URL:
            pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        else:
            pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                min_size=2,
                max_size=10
            )
        
        logger.info("✅ Database pool created successfully")
        return pool
        
    except Exception as e:
        logger.error(f"❌ Failed to create database pool: {e}")
        raise

async def get_db_connection() -> asyncpg.Connection:
    """Получение подключения из пула"""
    
    global _db_pool
    
    if _db_pool is None:
        _db_pool = await create_db_pool()
    
    return await _db_pool.acquire()

async def release_db_connection(connection: asyncpg.Connection):
    """Возвращение подключения в пул"""
    
    global _db_pool
    
    if _db_pool:
        await _db_pool.release(connection)

async def close_db_pool():
    """Закрытие пула подключений"""
    
    global _db_pool
    
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("✅ Database pool closed")

async def get_user_role(user_id: int) -> str:
    """Получение роли пользователя"""
    
    try:
        conn = await get_db_connection()
        
        user = await conn.fetchrow("""
            SELECT role FROM users 
            WHERE telegram_id = $1 AND is_active = true
        """, user_id)
        
        await conn.close()
        
        if user:
            return user["role"]
        else:
            # Если пользователя нет, создаем его как клиента
            await create_user_if_not_exists(user_id)
            return "client"
            
    except Exception as e:
        logger.error(f"❌ Error getting user role: {e}")
        return "unknown"

async def create_user_if_not_exists(user_id: int):
    """Создание пользователя если не существует"""
    
    try:
        conn = await get_db_connection()
        
        # Проверяем, существует ли пользователь
        existing = await conn.fetchrow("""
            SELECT id FROM users WHERE telegram_id = $1
        """, user_id)
        
        if not existing:
            # Создаем нового пользователя с ролью клиента
            await conn.execute("""
                INSERT INTO users (telegram_id, name, role, is_active, created_at, updated_at)
                VALUES ($1, 'Пользователь', 'client', true, NOW(), NOW())
            """, user_id)
            
            logger.info(f"👤 Created new user {user_id} with role 'client'")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error creating user: {e}")

# Удобные функции для использования
async def init_database():
    """Инициализация базы данных"""
    await create_db_pool()

async def shutdown_database():
    """Завершение работы с базой данных"""
    await close_db_pool()
