"""
🏗️ Role Middleware - Определение роли пользователя
"""

import logging
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware, types
from aiogram.types import Message, CallbackQuery

from database.db import get_user_role

logger = logging.getLogger(__name__)

class RoleMiddleware(BaseMiddleware):
    """Middleware для определения роли пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        try:
            # Получаем ID пользователя
            user_id = event.from_user.id
            
            # Определяем роль пользователя
            role = await get_user_role(user_id)
            
            # Добавляем роль в данные
            data["role"] = role
            
            logger.debug(f"👤 User {user_id} role: {role}")
            
            # Вызываем следующий обработчик
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"❌ RoleMiddleware error: {e}")
            # В случае ошибки, устанавливаем роль по умолчанию
            data["role"] = "unknown"
            return await handler(event, data)
