from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.keyboards.common_keyboards import CommonKeyboards
from src.database import get_session


class CommonHandlers:
    """Common handlers for all users"""
    
    def __init__(self, router: Router):
        self.router = router
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all common handlers"""
        self.router.message(CommandStart(), self.handle_start)
        self.router.message(Command("help"), self.handle_help)
        self.router.message(Command("cancel"), self.handle_cancel)
        self.router.message(F.text == "🔙 Назад", self.handle_back)
        self.router.message(F.text == "❌ Отмена", self.handle_cancel)
        self.router.callback_query(F.data == "back", self.handle_back_callback)
        self.router.callback_query(F.data == "cancel", self.handle_cancel_callback)
    
    async def handle_start(self, message: types.Message, state: FSMContext):
        """Handle /start command"""
        async for session in get_session():
            auth_service = AuthService(session)
            user_service = UserService(session)
            
            try:
                # Authenticate or register user
                user = await auth_service.authenticate_user(
                    telegram_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    username=message.from_user.username
                )
                
                # Clear any existing state
                await state.clear()
                
                # Welcome message based on role
                if user.role == "CLIENT":
                    welcome_text = (
                        f"👋 Добро пожаловать, {user.full_name}!\n\n"
                        "🛍️ Добро пожаловать в Maxxpharm!\n"
                        "Ваш надежный партнер в мире фармацевтики.\n\n"
                        "📱 Используйте меню ниже для навигации:"
                    )
                    keyboard = CommonKeyboards.main_menu()
                elif user.role == "ADMIN":
                    welcome_text = (
                        f"👑 Добро пожаловать, {user.full_name}!\n\n"
                        "🔧 Панель администратора Maxxpharm\n"
                        "Полный контроль системой управления.\n\n"
                        "📊 Используйте меню для управления:"
                    )
                    keyboard = CommonKeyboards.admin_menu()
                elif user.role == "MANAGER":
                    welcome_text = (
                        f"👋 Добро пожаловать, {user.full_name}!\n\n"
                        "📦 Панель менеджера Maxxpharm\n"
                        "Управление заказами и клиентами.\n\n"
                        "📋 Используйте меню для работы:"
                    )
                    keyboard = CommonKeyboards.manager_menu()
                elif user.role == "COURIER":
                    welcome_text = (
                        f"🚚 Добро пожаловать, {user.full_name}!\n\n"
                        "📦 Панель курьера Maxxpharm\n"
                        "Управление доставками.\n\n"
                        "📍 Используйте меню для работы:"
                    )
                    keyboard = CommonKeyboards.courier_menu()
                else:
                    welcome_text = (
                        f"👋 Добро пожаловать, {user.full_name}!\n\n"
                        "🛍️ Добро пожаловать в Maxxpharm!\n"
                        "Ваша роль: {user.role}\n\n"
                        "📱 Используйте меню для навигации:"
                    )
                    keyboard = CommonKeyboards.main_menu()
                
                await message.answer(welcome_text, reply_markup=keyboard)
                
            except ValueError as e:
                await message.answer("🚫 Доступ запрещен. Ваш аккаунт заблокирован.")
    
    async def handle_help(self, message: types.Message):
        """Handle /help command"""
        help_text = (
            "🆘 *Помощь по боту Maxxpharm*\n\n"
            "📱 *Основные команды:*\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/cancel - Отменить текущее действие\n\n"
            "🛍️ *Для клиентов:*\n"
            "• 🛍 Каталог - Просмотр товаров\n"
            "• 🔍 Поиск - Поиск по названию\n"
            "• 🛒 Корзина - Управление корзиной\n"
            "• 📦 Мои заказы - История заказов\n"
            "• 📞 Поддержка - Связь с поддержкой\n\n"
            "👑 *Для администраторов:*\n"
            "• 📊 Статистика - Просмотр статистики\n"
            "• 📦 Заказы - Управление заказами\n"
            "• 👥 Пользователи - Управление пользователями\n"
            "• 🧾 Товары - Управление товарами\n"
            "• 🏷 Категории - Управление категориями\n"
            "• 🏪 Склад - Управление складом\n"
            "• ⚙ Настройки - Настройки системы\n"
            "• 📝 Логи - Просмотр логов\n\n"
            "❓ *Нужна помощь?*\n"
            "Свяжитесь с поддержкой: @maxxpharm_support"
        )
        
        await message.answer(help_text, parse_mode="Markdown")
    
    async def handle_cancel(self, message: types.Message, state: FSMContext):
        """Handle cancel action"""
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=CommonKeyboards.main_menu())
    
    async def handle_back(self, message: types.Message, state: FSMContext):
        """Handle back navigation"""
        current_state = await state.get_state()
        
        if current_state:
            await state.clear()
        
        # Get user info and return to appropriate menu
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if user:
                if user.role == "ADMIN":
                    keyboard = CommonKeyboards.admin_menu()
                elif user.role == "MANAGER":
                    keyboard = CommonKeyboards.manager_menu()
                elif user.role == "COURIER":
                    keyboard = CommonKeyboards.courier_menu()
                else:
                    keyboard = CommonKeyboards.main_menu()
                
                await message.answer("🔙 Вернулись в главное меню", reply_markup=keyboard)
                break
    
    async def handle_back_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle back callback"""
        await self.handle_back(callback.message, state)
        await callback.answer()
    
    async def handle_cancel_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle cancel callback"""
        await self.handle_cancel(callback.message, state)
        await callback.answer()
