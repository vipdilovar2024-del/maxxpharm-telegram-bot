from functools import wraps
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.services.auth_service import AuthService
from src.database import get_session


def admin_required(func):
    """Decorator to require admin access"""
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        # Get user info
        user_id = message_or_callback.from_user.id
        
        async for session in get_session():
            from src.services.user_service import UserService
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                await message_or_callback.answer("❌ Доступ запрещен. Пользователь не найден.")
                return
            
            auth_service = AuthService(session)
            if not await auth_service.is_admin(user):
                await message_or_callback.answer("❌ Доступ запрещен. Требуются права администратора.")
                return
            
            # Add user to kwargs
            kwargs['user'] = user
            kwargs['session'] = session
            
            return await func(message_or_callback, *args, **kwargs)
    
    return wrapper


def manager_required(func):
    """Decorator to require manager access"""
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        # Get user info
        user_id = message_or_callback.from_user.id
        
        async for session in get_session():
            from src.services.user_service import UserService
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                await message_or_callback.answer("❌ Доступ запрещен. Пользователь не найден.")
                return
            
            auth_service = AuthService(session)
            if not await auth_service.is_manager(user):
                await message_or_callback.answer("❌ Доступ запрещен. Требуются права менеджера.")
                return
            
            # Add user to kwargs
            kwargs['user'] = user
            kwargs['session'] = session
            
            return await func(message_or_callback, *args, **kwargs)
    
    return wrapper


def courier_required(func):
    """Decorator to require courier access"""
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        # Get user info
        user_id = message_or_callback.from_user.id
        
        async for session in get_session():
            from src.services.user_service import UserService
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                await message_or_callback.answer("❌ Доступ запрещен. Пользователь не найден.")
                return
            
            auth_service = AuthService(session)
            if not await auth_service.is_courier(user):
                await message_or_callback.answer("❌ Доступ запрещен. Требуются права курьера.")
                return
            
            # Add user to kwargs
            kwargs['user'] = user
            kwargs['session'] = session
            
            return await func(message_or_callback, *args, **kwargs)
    
    return wrapper
