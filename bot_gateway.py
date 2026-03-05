#!/usr/bin/env python3
"""
🤖 Bot Gateway Layer - Входная точка Enterprise системы
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.middlewares.base import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

# Импортируем Enterprise модули
from crm.role_manager import RoleManager
from crm.user_manager import UserManager
from services.notification_service import NotificationService
from monitor.health_check import HealthChecker
from cache.session_manager import SessionManager
from utils.decorators import rate_limit, log_activity
from utils.constants import UserRole

class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации"""
    
    def __init__(self, role_manager: RoleManager, session_manager: SessionManager):
        self.role_manager = role_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger("auth_middleware")
    
    async def __call__(self, handler, event: Update, data: Dict[str, Any]) -> Any:
        """Проверка аутентификации"""
        
        # Получаем пользователя
        if isinstance(event, Message):
            user_id = event.from_user.id
            user_data = event.from_user
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            user_data = event.from_user
        else:
            return await handler(event, data)
        
        # Проверяем роль пользователя
        user_role = await self.role_manager.get_user_role(user_id)
        
        if not user_role:
            # Создаем нового пользователя с ролью CLIENT
            await self.role_manager.create_user(
                telegram_id=user_id,
                name=user_data.full_name,
                username=user_data.username,
                role=UserRole.CLIENT
            )
            user_role = UserRole.CLIENT
        
        # Добавляем данные в контекст
        data['user_id'] = user_id
        data['user_role'] = user_role
        data['user_data'] = user_data
        
        # Обновляем сессию
        await self.session_manager.update_session(user_id, {
            'last_activity': asyncio.get_event_loop().time(),
            'role': user_role.value
        })
        
        return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования"""
    
    def __init__(self):
        self.logger = logging.getLogger("logging_middleware")
    
    async def __call__(self, handler, event: Update, data: Dict[str, Any]) -> Any:
        """Логирование всех запросов"""
        
        # Логируем запрос
        if isinstance(event, Message):
            self.logger.info(f"Message from {event.from_user.id}: {event.text[:50]}")
        elif isinstance(event, CallbackQuery):
            self.logger.info(f"Callback from {event.from_user.id}: {event.data[:50]}")
        
        try:
            result = await handler(event, data)
            self.logger.info(f"Handler completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Handler error: {e}")
            raise

class RateLimitMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger("rate_limit_middleware")
        self.rate_limits = {
            UserRole.CLIENT: 10,  # 10 запросов в минуту
            UserRole.OPERATOR: 30,
            UserRole.PICKER: 20,
            UserRole.CHECKER: 20,
            UserRole.COURIER: 25,
            UserRole.ADMIN: 50,
            UserRole.DIRECTOR: 100
        }
    
    async def __call__(self, handler, event: Update, data: Dict[str, Any]) -> Any:
        """Проверка ограничения частоты"""
        
        user_id = data.get('user_id')
        user_role = data.get('user_role')
        
        if not user_id or not user_role:
            return await handler(event, data)
        
        # Проверяем лимит
        can_proceed = await self.session_manager.check_rate_limit(
            user_id, 
            self.rate_limits.get(user_role, 10)
        )
        
        if not can_proceed:
            if isinstance(event, Message):
                await event.answer("⏰ Слишком много запросов. Попробуйте позже.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏰ Слишком много запросов. Попробуйте позже.", show_alert=True)
            return
        
        return await handler(event, data)

class BotGateway:
    """Bot Gateway - входная точка системы"""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.logger = logging.getLogger("bot_gateway")
        
        # Инициализируем компоненты
        self.role_manager = RoleManager()
        self.user_manager = UserManager()
        self.session_manager = SessionManager()
        self.notification_service = NotificationService(self.bot)
        self.health_checker = HealthChecker()
        
        # Настраиваем middleware
        self._setup_middlewares()
        
        # Регистрируем обработчики
        self._register_handlers()
    
    def _setup_middlewares(self):
        """Настройка middleware"""
        self.dp.message.middleware(AuthMiddleware(self.role_manager, self.session_manager))
        self.dp.message.middleware(LoggingMiddleware())
        self.dp.message.middleware(RateLimitMiddleware(self.session_manager))
        
        self.dp.callback_query.middleware(AuthMiddleware(self.role_manager, self.session_manager))
        self.dp.callback_query.middleware(LoggingMiddleware())
        self.dp.callback_query.middleware(RateLimitMiddleware(self.session_manager))
    
    def _register_handlers(self):
        """Регистрация базовых обработчиков"""
        
        @self.dp.message(Command("start"))
        @log_activity("start_command")
        async def cmd_start(message: types.Message, user_role: UserRole, user_data: types.User):
            """Обработчик /start"""
            
            # Получаем или создаем пользователя
            user = await self.user_manager.get_or_create_user(
                telegram_id=message.from_user.id,
                name=message.from_user.full_name,
                username=message.from_user.username,
                role=user_role
            )
            
            # Отправляем приветствие
            welcome_text = f"""
👋 <b>Добро пожаловать в MAXXPHARM!</b>

🏥 <b>Система заказов фармпрепаратов</b>

🎭 <b>Ваша роль:</b> {user_role.value.title()}

📱 <b>Выберите действие из меню:</b>
"""
            
            # Получаем меню для роли
            from ux_interface import ClientUX, OperatorUX, PickerUX, CheckerUX, CourierUX, DirectorUX, AdminUX
            
            keyboard = None
            if user_role == UserRole.CLIENT:
                keyboard = ClientUX.get_welcome_keyboard()
            elif user_role == UserRole.OPERATOR:
                keyboard = OperatorUX.get_main_keyboard()
            elif user_role == UserRole.PICKER:
                keyboard = PickerUX.get_main_keyboard()
            elif user_role == UserRole.CHECKER:
                keyboard = CheckerUX.get_main_keyboard()
            elif user_role == UserRole.COURIER:
                keyboard = CourierUX.get_main_keyboard()
            elif user_role == UserRole.DIRECTOR:
                keyboard = DirectorUX.get_main_keyboard()
            elif user_role == UserRole.ADMIN:
                keyboard = AdminUX.get_main_keyboard()
            
            await message.answer(welcome_text, reply_markup=keyboard)
        
        @self.dp.message(Command("health"))
        async def cmd_health(message: types.Message, user_role: UserRole):
            """Проверка здоровья системы"""
            if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
                await message.answer("❌ Доступ запрещен!")
                return
            
            health_status = await self.health_checker.check_all_systems()
            
            health_text = """
🏥 <b>Статус системы MAXXPHARM</b>

📊 <b>Компоненты:</b>
"""
            
            for component, status in health_status.items():
                emoji = "✅" if status['healthy'] else "❌"
                health_text += f"{emoji} {component}: {status['message']}\n"
            
            health_text += f"\n🕐 {asyncio.get_event_loop().time()}"
            
            await message.answer(health_text)
        
        @self.dp.message(Command("status"))
        async def cmd_status(message: types.Message, user_role: UserRole, user_id: int):
            """Статус пользователя"""
            user = await self.user_manager.get_user(user_id)
            
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            status_text = f"""
👤 <b>Статус пользователя</b>

🆔 <b>ID:</b> {user.id}
👤 <b>Имя:</b> {user.name}
🎭 <b>Роль:</b> {user.role.value}
📱 <b>Telegram ID:</b> {user.telegram_id}
📅 <b>Создан:</b> {user.created_at}
🔄 <b>Активен:</b> {'Да' if user.is_active else 'Нет'}
"""
            
            await message.answer(status_text)
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: types.Message, user_role: UserRole):
            """Справка"""
            help_text = f"""
📖 <b>Справка MAXXPHARM</b>

🎭 <b>Ваша роль:</b> {user_role.value.title()}

📋 <b>Доступные команды:</b>
/start - Главное меню
/health - Статус системы (Admin/Director)
/status - Ваш статус
/help - Эта справка

💡 <b>Поддержка:</b>
📞 +998 90 123 45 67
📧 support@maxxpharm.com
"""
            
            await message.answer(help_text)
        
        @self.dp.message()
        async def handle_unknown_message(message: types.Message, user_role: UserRole):
            """Обработка неизвестных сообщений"""
            await message.answer(
                "❓ <b>Команда не найдена</b>\n\n"
                "Используйте /help для справки",
                reply_markup=None
            )
    
    async def start(self):
        """Запуск Bot Gateway"""
        try:
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Проверяем здоровье системы
            await self.health_checker.check_all_systems()
            
            # Запускаем polling
            self.logger.info("🤖 Bot Gateway starting...")
            print("🚀 MAXXPHARM Enterprise Bot Gateway starting...")
            print(f"🤖 Bot: @{(await self.bot.get_me()).username}")
            print("🏥 Enterprise Architecture Ready!")
            
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            self.logger.error(f"❌ Bot Gateway error: {e}")
            raise
    
    async def stop(self):
        """Остановка Bot Gateway"""
        await self.bot.session.close()
        self.logger.info("🤖 Bot Gateway stopped")

# 🎨 Enterprise декораторы
def enterprise_required(role: UserRole):
    """Декоратор для проверки Enterprise доступа"""
    def decorator(func):
        async def wrapper(message: types.Message, user_role: UserRole, **kwargs):
            if user_role != role:
                await message.answer("❌ Доступ запрещен! Требуется роль: " + role.value.title())
                return
            return await func(message, user_role=user_role, **kwargs)
        return wrapper
    return decorator

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message: types.Message, user_role: UserRole, **kwargs):
        if user_role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
            await message.answer("❌ Доступ запрещен! Требуются права администратора.")
            return
        return await func(message, user_role=user_role, **kwargs)
    return wrapper

# 🎯 Enterprise функции
async def create_enterprise_bot(bot_token: str) -> BotGateway:
    """Создание Enterprise бота"""
    return BotGateway(bot_token)
