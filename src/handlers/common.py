"""
🤖 Общие обработчики MAXXPHARM CRM
"""

from typing import Dict, Any
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from ..models.database import UserRole
from ..services.user_service import UserService
from ..database import get_db


class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    full_name = State()
    pharmacy_name = State()
    pharmacy_address = State()
    phone = State()


class CommonHandlers:
    """Общие обработчики для всех ролей"""
    
    def __init__(self):
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.router.message(Command("start"))
        async def cmd_start(message: Message, state: FSMContext):
            """Обработчик команды /start"""
            await state.clear()
            
            # Получаем или создаем пользователя
            async for session in get_db():
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                
                if not user:
                    # Создаем нового пользователя
                    user = await user_service.create_user(
                        telegram_id=message.from_user.id,
                        full_name=message.from_user.full_name,
                        username=message.from_user.username
                    )
                    
                    # Если это клиент, начинаем регистрацию аптеки
                    if user.role == UserRole.CLIENT:
                        await self._start_pharmacy_registration(message, state, user_service, user)
                        return
                
                # Отправляем соответствующее меню
                await self._send_main_menu(message, user)
        
        @self.router.message(Command("help"))
        async def cmd_help(message: Message):
            """Обработчик команды /help"""
            help_text = """
🏥 <b>MAXXPHARM CRM - Справка</b>

📋 <b>Основные команды:</b>
/start - Главное меню
/help - Эта справка

🎯 <b>Роли в системе:</b>
👑 Администратор - Полное управление
📊 Директор - Аналитика и отчеты
🔹 Оператор - Обработка заявок
🔹 Сборщик - Комплектация заказов
🔹 Проверщик - Контроль качества
🔹 Курьер - Доставка заказов
💼 Торговый представитель - Сбор долгов
🔹 Клиент - Создание заявок

📞 <b>Поддержка:</b>
• 📞 Телефон: +992 900 000 001
• 💬 Telegram: @maxxpharm_support
• 🌐 Сайт: www.maxxpharm.tj

🏥 <b>MAXXPHARM - Ваша надежная аптека!</b>
            """
            await message.answer(help_text)
        
        @self.router.message(F.text == "🚪 Выход")
        async def cmd_logout(message: Message, state: FSMContext):
            """Выход из текущего состояния"""
            await state.clear()
            
            async for session in get_db():
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                await self._send_main_menu(message, user)
    
    async def _start_pharmacy_registration(
        self, 
        message: Message, 
        state: FSMContext, 
        user_service: UserService, 
        user
    ):
        """Начало регистрации аптеки"""
        await state.set_state(RegistrationStates.full_name)
        
        await message.answer(
            "🏥 <b>Регистрация аптеки</b>\n\n"
            "📋 <b>Шаг 1/4: ФИО контактного лица</b>\n\n"
            "👤 Пожалуйста, введите ваше полное ФИО:\n\n"
            "📝 <b>Пример:</b> Иванов Иван Иванович"
        )
    
    async def _send_main_menu(self, message: Message, user):
        """Отправка главного меню в зависимости от роли"""
        
        if user.role == UserRole.ADMIN:
            await self._send_admin_menu(message, user)
        elif user.role == UserRole.DIRECTOR:
            await self._send_director_menu(message, user)
        elif user.role == UserRole.OPERATOR:
            await self._send_operator_menu(message, user)
        elif user.role == UserRole.COLLECTOR:
            await self._send_collector_menu(message, user)
        elif user.role == UserRole.CHECKER:
            await self._send_checker_menu(message, user)
        elif user.role == UserRole.COURIER:
            await self._send_courier_menu(message, user)
        elif user.role == UserRole.SALES_REP:
            await self._send_sales_rep_menu(message, user)
        else:  # CLIENT
            await self._send_client_menu(message, user)
    
    async def _send_admin_menu(self, message: Message, user):
        """Меню администратора"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Все заявки"),
                    KeyboardButton(text="📈 Аналитика")
                ],
                [
                    KeyboardButton(text="👥 Пользователи и роли"),
                    KeyboardButton(text="📜 История действий")
                ],
                [
                    KeyboardButton(text="⚙️ Настройки системы"),
                    KeyboardButton(text="🔗 Интеграция 1С")
                ],
                [
                    KeyboardButton(text="📦 Управление статусами"),
                    KeyboardButton(text="📢 Рассылки")
                ],
                [
                    KeyboardButton(text="🗄 Архив"),
                    KeyboardButton(text="🔐 Управление админами")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
👑 <b>MAXXPHARM CRM - Панель администратора</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: АДМИНИСТРАТОР</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Система готова к работе!</b>

📊 <b>Статистика системы:</b>
• 📦 Всего заказов: 0
• 👥 Пользователей: 0
• 💰 Оборот: 0 сомони

🏥 <b>MAXXPHARM CRM - Профессиональное управление</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_director_menu(self, message: Message, user):
        """Меню директора"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Дашборд"),
                    KeyboardButton(text="📈 Статистика")
                ],
                [
                    KeyboardButton(text="💰 Финансы"),
                    KeyboardButton(text="📋 Отчеты")
                ],
                [
                    KeyboardButton(text="🔄 Эффективность"),
                    KeyboardButton(text="⏰ Время работы")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
📊 <b>MAXXPHARM CRM - Панель директора</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: ДИРЕКТОР</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Доступ к аналитике открыт</b>

📈 <b>Ключевые показатели:</b>
• 📦 Заказов сегодня: 0
• 💰 Выручка: 0 сомони
• 👥 Активных сотрудников: 0

🏥 <b>MAXXPHARM CRM - Стратегическое управление</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_operator_menu(self, message: Message, user):
        """Меню оператора"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📥 Новые заявки"),
                    KeyboardButton(text="📦 В работе")
                ],
                [
                    KeyboardButton(text="💳 Оплата"),
                    KeyboardButton(text="✅ Принять")
                ],
                [
                    KeyboardButton(text="❌ Отказать"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
🔹 <b>MAXXPHARM CRM - Панель оператора</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: ОПЕРАТОР</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Обработка заявок</b>

📋 <b>Ваши задачи:</b>
• 📥 Рассмотрение новых заявок
• ✅ Подтверждение заказов
• 💳 Проверка оплаты
• 📦 Передача в сборку

🏥 <b>MAXXPHARM CRM - Эффективная обработка</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_collector_menu(self, message: Message, user):
        """Меню сборщика"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📦 В сборке"),
                    KeyboardButton(text="🔄 В обработке")
                ],
                [
                    KeyboardButton(text="✅ Готово"),
                    KeyboardButton(text="❌ Проблема")
                ],
                [
                    KeyboardButton(text="📋 Список"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
🔹 <b>MAXXPHARM CRM - Панель сборщика</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: СБОРЩИК</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Комплектация заказов</b>

📋 <b>Ваши задачи:</b>
• 📦 Получение подтвержденных заказов
• 🔄 Сборка лекарств
• ✅ Подтверждение комплектации
• 📤 Передача на проверку

🏥 <b>MAXXPHARM CRM - Точная сборка</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_checker_menu(self, message: Message, user):
        """Меню проверщика"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🔍 На проверке"),
                    KeyboardButton(text="✅ Подтвердить")
                ],
                [
                    KeyboardButton(text="❌ Вернуть"),
                    KeyboardButton(text="📋 История")
                ],
                [
                    KeyboardButton(text="📊 Статистика"),
                    KeyboardButton(text="🔄 В обработке")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
🔹 <b>MAXXPHARM CRM - Панель проверщика</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: ПРОВЕРЩИК</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Контроль качества</b>

📋 <b>Ваши задачи:</b>
• 🔍 Проверка собранных заказов
• ✅ Подтверждение правильности
• ❌ Возврат при ошибках
• 📤 Передача курьеру

🏥 <b>MAXXPHARM CRM - Гарантия качества</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_courier_menu(self, message: Message, user):
        """Меню курьера"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🚚 В пути"),
                    KeyboardButton(text="📍 Маршрут")
                ],
                [
                    KeyboardButton(text="✅ Доставлено"),
                    KeyboardButton(text="📍 Отправить геолокацию")
                ],
                [
                    KeyboardButton(text="📞 Связаться"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🗺️ Карта"),
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
🔹 <b>MAXXPHARM CRM - Панель курьера</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: КУРЬЕР</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Доставка заказов</b>

📋 <b>Ваши задачи:</b>
• 🚚 Получение готовых заказов
• 📍 Отслеживание маршрута
• ✅ Доставка клиентам
• 📞 Связь с получателями

🏥 <b>MAXXPHARM CRM - Быстрая доставка</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_sales_rep_menu(self, message: Message, user):
        """Меню торгового представителя"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="💰 Долги"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="💸 Фиксировать оплату"),
                    KeyboardButton(text="📋 История")
                ],
                [
                    KeyboardButton(text="🗺️ Маршрут"),
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
💼 <b>MAXXPHARM CRM - Панель торгового представителя</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: ТОРГОВЫЙ ПРЕДСТАВИТЕЛЬ</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Сбор долгов</b>

📋 <b>Ваши задачи:</b>
• 💰 Посмотр клиентов с долгами
• 💸 Фиксация оплат
• 📊 Ведение статистики
• 🗺️ Планирование маршрутов

🏥 <b>MAXXPHARM CRM - Финансовый контроль</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def _send_client_menu(self, message: Message, user):
        """Меню клиента"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📦 Создать заявку"),
                    KeyboardButton(text="📋 Мои заявки")
                ],
                [
                    KeyboardButton(text="📊 Статус заявки"),
                    KeyboardButton(text="💳 Оплатить заказ")
                ],
                [
                    KeyboardButton(text="💬 Связаться с оператором"),
                    KeyboardButton(text="📚 Каталог")
                ],
                [
                    KeyboardButton(text="🚪 Выход")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_text = f"""
🔹 <b>MAXXPHARM CRM - Панель клиента</b>

👋 Добро пожаловать, <b>{user.full_name}</b>!

🎯 <b>Ваша роль: КЛИЕНТ</b>
📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}

🚀 <b>Управление заказами</b>

📋 <b>Ваши возможности:</b>
• 📦 Создание заявок
• 📊 Отслеживание статусов
• 💳 Оплата заказов
• 💬 Связь с оператором

🏥 <b>MAXXPHARM CRM - Удобный сервис</b>
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
