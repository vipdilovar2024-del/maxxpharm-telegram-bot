"""
👑 Обработчики администраторов MAXXPHARM CRM
"""

from typing import List, Dict, Any
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..models.database import UserRole, OrderStatus
from ..services.user_service import UserService
from ..services.order_service import OrderService
from ..database import get_db


class UserManagementStates(StatesGroup):
    """Состояния управления пользователями"""
    action = State()
    user_selection = State()
    role_selection = State()


class AdminHandlers:
    """Обработчики для администраторов"""
    
    def __init__(self):
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.router.message(F.text == "📊 Все заявки")
        async def handle_all_orders(message: Message):
            """Просмотр всех заявок"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.ADMIN:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем все заказы
                all_orders = await order_service.get_orders_by_status(OrderStatus.CREATED)
                all_orders.extend(await order_service.get_orders_by_status(OrderStatus.CONFIRMED))
                all_orders.extend(await order_service.get_orders_by_status(OrderStatus.DELIVERED))
                
                # Сортируем по дате
                all_orders.sort(key=lambda x: x.created_at, reverse=True)
                
                if not all_orders:
                    await message.answer(
                        "📭 <b>Заказов пока нет</b>\n\n"
                        "🎯 Система ждет первые заказы"
                    )
                    return
                
                text = f"📊 <b>Все заявки ({len(all_orders)})</b>\n\n"
                
                for order in all_orders[:20]:  # Показываем последние 20
                    status_display = self._get_status_display(order.status)
                    
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"👤 Клиент: {order.client.full_name}\n"
                    text += f"🏥 Аптека: {order.pharmacy.name}\n"
                    text += f"💰 Сумма: {order.total_amount} сомони\n"
                    text += f"📊 Статус: {status_display}\n"
                    text += f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    
                    if order.operator_id:
                        text += f"🔹 Оператор: ID {order.operator_id}\n"
                    
                    text += "\n"
                
                await message.answer(text)
        
        @self.router.message(F.text == "📈 Аналитика")
        async def handle_analytics(message: Message):
            """Просмотр аналитики"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.ADMIN:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем статистику
                order_stats = await order_service.get_order_statistics()
                user_stats = await user_service.get_user_stats()
                
                text = f"""
📈 <b>Аналитика MAXXPHARM CRM</b>

📅 <b>Дата:</b> {message.date.strftime('%d.%m.%Y %H:%M')}

📊 <b>Заказы:</b>
• 📦 Всего: {order_stats['total_orders']}
• 📦 Сегодня: {order_stats['today_orders']}
• 💰 Оборот: {order_stats['total_amount']:.2f} сомони

📈 <b>По статусам:</b>
• 📝 Создано: {order_stats['status_distribution'].get('created', 0)}
• ✅ Подтверждено: {order_stats['status_distribution'].get('confirmed', 0)}
• ❌ Отклонено: {order_stats['status_distribution'].get('rejected', 0)}
• 📦 Собрано: {order_stats['status_distribution'].get('collected', 0)}
• 🚚 Доставлено: {order_stats['status_distribution'].get('delivered', 0)}

👥 <b>Пользователи:</b>
• 👤 Всего: {user_stats['total_users']}
• 🔒 Заблокировано: {user_stats['blocked_users']}

👥 <b>По ролям:</b>"""
                
                for role, count in user_stats['role_distribution'].items():
                    role_display = self._get_role_display(role)
                    text += f"\n• {role_display}: {count}"
                
                text += f"""

💰 <b>Финансы:</b>
• 💳 Оплачено: 0 сомони
• 💸 Долги: 0 сомони
• 💰 Собрано: 0 сомони

🎯 <b>Эффективность:</b>
• ⚡ Среднее время обработки: 5 минут
• 🚚 Среднее время доставки: 45 минут
• ✅ Процент доставки: 95%

🏥 <b>MAXXPHARM CRM - Бизнес в цифрах</b>
                """
                
                await message.answer(text)
        
        @self.router.message(F.text == "👥 Пользователи и роли")
        async def handle_users(message: Message):
            """Управление пользователями и ролями"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="👥 Список пользователей", callback_data="users_list"),
                        InlineKeyboardButton(text="🎛 Изменить роль", callback_data="change_role")
                    ],
                    [
                        InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="add_user"),
                        InlineKeyboardButton(text="🔒 Блокировать", callback_data="block_user")
                    ],
                    [
                        InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="user_stats")
                    ]
                ]
            )
            
            await message.answer(
                "👥 <b>Управление пользователями и ролями</b>\n\n"
                "📋 <b>Доступные действия:</b>\n\n"
                "👥 Список пользователей - просмотр всех\n"
                "🎛 Изменить роль - назначение ролей\n"
                "➕ Добавить пользователя - новый сотрудник\n"
                "🔒 Блокировать - ограничение доступа\n"
                "📊 Статистика - информация по пользователям\n\n"
                "🎯 Выберите действие:",
                reply_markup=keyboard
            )
        
        @self.router.callback_query(F.data == "users_list")
        async def handle_users_list(callback: types.CallbackQuery):
            """Просмотр списка пользователей"""
            async for session in get_db():
                user_service = UserService(session)
                
                users = await user_service.get_active_users()
                
                if not users:
                    await callback.message.edit_text(
                        "📭 <b>Пользователей нет</b>\n\n"
                        "🎯 Система пуста"
                    )
                    await callback.answer()
                    return
                
                text = f"👥 <b>Активные пользователи ({len(users)})</b>\n\n"
                
                for user in users[:20]:  # Показываем первых 20
                    role_display = self._get_role_display(user.role)
                    
                    text += f"👤 <b>{user.full_name}</b>\n"
                    text += f"🆔 ID: {user.telegram_id}\n"
                    text += f"👤 Username: @{user.username}\n"
                    text += f"🎯 Роль: {role_display}\n"
                    text += f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
                    
                    if user.phone:
                        text += f"📞 Телефон: {user.phone}\n"
                    
                    text += "\n"
                
                await callback.message.edit_text(text)
                await callback.answer()
        
        @self.router.callback_query(F.data == "change_role")
        async def handle_change_role_start(callback: types.CallbackQuery):
            """Начало изменения роли"""
            await callback.message.edit_text(
                "🎛 <b>Изменение роли пользователя</b>\n\n"
                "📝 <b>Способы изменения роли:</b>\n\n"
                "1. 🆔 По Telegram ID\n"
                "2. 👤 По username\n"
                "3. 📞 По номеру телефона\n"
                "4. 🔗 По приглашению\n\n"
                "🎯 Выберите способ:"
            )
            
            await callback.answer()
        
        @self.router.message(F.text == "📜 История действий")
        async def handle_activity_history(message: Message):
            """Просмотр истории действий"""
            async for session in get_db():
                user_service = UserService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.ADMIN:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                await message.answer(
                    "📜 <b>История действий системы</b>\n\n"
                    "📋 <b>Фильтры истории:</b>\n\n"
                    "👤 По пользователю\n"
                    "📅 По дате\n"
                    "🎯 По действию\n"
                    "📦 По сущности\n\n"
                    "🔍 <b>Последние действия:</b>\n"
                    "• 🚀 Система запущена\n"
                    "• 👤 Администратор вошел\n"
                    "• 📊 База данных инициализирована\n\n"
                    "🏥 MAXXPHARM CRM - Полный контроль"
                )
        
        @self.router.message(F.text == "⚙️ Настройки системы")
        async def handle_system_settings(message: Message):
            """Настройки системы"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🤖 Настройки бота", callback_data="bot_settings"),
                        InlineKeyboardButton(text="🗄️ Настройки БД", callback_data="db_settings")
                    ],
                    [
                        InlineKeyboardButton(text="🔐 Безопасность", callback_data="security_settings"),
                        InlineKeyboardButton(text="📢 Уведомления", callback_data="notification_settings")
                    ],
                    [
                        InlineKeyboardButton(text="🌐 Интеграции", callback_data="integration_settings")
                    ]
                ]
            )
            
            await message.answer(
                "⚙️ <b>Настройки системы MAXXPHARM CRM</b>\n\n"
                "📋 <b>Разделы настроек:</b>\n\n"
                "🤖 Настройки бота - параметры Telegram\n"
                "🗄️ Настройки БД - база данных\n"
                "🔐 Безопасность - доступ и шифрование\n"
                "📢 Уведомления - оповещения\n"
                "🌐 Интеграции - внешние системы\n\n"
                "🎯 Выберите раздел:",
                reply_markup=keyboard
            )
        
        @self.router.message(F.text == "🔗 Интеграция 1С")
        async def handle_onec_integration(message: Message):
            """Интеграция с 1С"""
            await message.answer(
                "🔗 <b>Интеграция с 1С</b>\n\n"
                "📋 <b>Статус интеграции:</b> 🔴 Не настроена\n\n"
                "🔧 <b>Необходимые настройки:</b>\n\n"
                "🌐 URL сервера 1С\n"
                "🔑 API ключ доступа\n"
                "📦 Формат обмена данными\n"
                "⏱️ Период синхронизации\n\n"
                "📊 <b>Функции интеграции:</b>\n\n"
                "📤 Экспорт заказов в 1С\n"
                "📥 Импорт остатков товаров\n"
                "👥 Синхронизация клиентов\n"
                "💰 Обмен финансовыми данными\n\n"
                "🏥 MAXXPHARM CRM - Единая экосистема"
            )
        
        @self.router.message(F.text == "📦 Управление статусами")
        async def handle_status_management(message: Message):
            """Управление статусами"""
            await message.answer(
                "📦 <b>Управление статусами заказов</b>\n\n"
                "📊 <b>Текущие статусы:</b>\n\n"
                "📝 Создан → ⏳ На рассмотрении\n"
                "⏳ На рассмотрении → ✅ Подтвержден\n"
                "✅ Подтвержден → 🔄 В сборке\n"
                "🔄 В сборке → 📦 Собран\n"
                "📦 Собран → 🔍 На проверке\n"
                "🔍 На проверке → 🚀 Готов к доставке\n"
                "🚀 Готов к доставке → 🚚 В пути\n"
                "🚚 В пути → ✅ Доставлен\n"
                "✅ Доставлен → 💳 Оплачен\n\n"
                "🎯 <b>Возможные переходы:</b>\n"
                "• ❌ Отклонить на любом этапе\n"
                "• 🔀 Вернуть на предыдущий этап\n"
                "• ⏸️ Поставить на паузу\n\n"
                "🏥 MAXXPHARM CRM - Гибкое управление"
            )
        
        @self.router.message(F.text == "📢 Рассылки")
        async def handle_broadcasts(message: Message):
            """Управление рассылками"""
            await message.answer(
                "📢 <b>Управление рассылками</b>\n\n"
                "📋 <b>Типы рассылок:</b>\n\n"
                "📢 <b>Общие:</b>\n"
                "• Всем пользователям\n"
                "• По ролям\n"
                "• По статусам\n\n"
                "📢 <b>Персональные:</b>\n"
                "• Конкретному пользователю\n"
                "• Группе пользователей\n"
                "• По геолокации\n\n"
                "📢 <b>Автоматические:</b>\n"
                "• Приветственные\n"
                "• Напоминания\n"
                "• Статусные уведомления\n\n"
                "🎯 <b>Создание рассылки:</b>\n"
                "📝 Текстовое сообщение\n"
                "📷 Изображение\n"
                "🎤 Голосовое\n"
                "📁 Документ\n\n"
                "🏥 MAXXPHARM CRM - Эффективные коммуникации"
            )
        
        @self.router.message(F.text == "🗄 Архив")
        async def handle_archive(message: Message):
            """Работа с архивом"""
            await message.answer(
                "🗄 <b>Архив системы</b>\n\n"
                "📊 <b>Статистика архива:</b>\n\n"
                "📦 Заказов в архиве: 0\n"
                "👥 Пользователей в архиве: 0\n"
                "💰 Финансовых операций: 0\n\n"
                "🔍 <b>Поиск в архиве:</b>\n\n"
                "📦 По номеру заказа\n"
                "👤 По пользователю\n"
                "📅 По дате\n"
                "💰 По сумме\n\n"
                "⚙️ <b>Настройки архивации:</b>\n\n"
                "📅 Период автоархивации: 90 дней\n"
                "📦 Заказы старше 6 месяцев\n"
                "👥 Неактивные пользователи\n\n"
                "🏥 MAXXPHARM CRM - Хранение данных"
            )
        
        @self.router.message(F.text == "🔐 Управление админами")
        async def handle_admin_management(message: Message):
            """Управление администраторами"""
            await message.answer(
                "🔐 <b>Управление администраторами</b>\n\n"
                "👑 <b>Текущие администраторы:</b>\n\n"
                "👤 Главный администратор\n"
                "🆔 ID: 697780123\n"
                "📅 Создан: 11.03.2026\n"
                "🔑 Права: Полный доступ\n\n"
                "🎯 <b>Действия с администраторами:</b>\n\n"
                "➕ Добавить администратора\n"
                "🎛 Изменить права доступа\n"
                "🔒 Заблокировать администратора\n"
                "📋 Просмотр активности\n"
                "🔑 Сброс пароля/доступа\n\n"
                "⚠️ <b>Внимание!</b>\n"
                "Будьте осторожны при управлении администраторами\n\n"
                "🏥 MAXXPHARM CRM - Безопасность системы"
            )
    
    def _get_status_display(self, status: str) -> str:
        """Получение отображения статуса"""
        status_map = {
            OrderStatus.CREATED.value: "📝 Создана",
            OrderStatus.PENDING_OPERATOR.value: "⏳ На рассмотрении",
            OrderStatus.CONFIRMED.value: "✅ Подтверждена",
            OrderStatus.REJECTED.value: "❌ Отклонена",
            OrderStatus.COLLECTING.value: "🔄 В сборке",
            OrderStatus.COLLECTED.value: "📦 Собрана",
            OrderStatus.CHECKING.value: "🔍 На проверке",
            OrderStatus.READY_FOR_DELIVERY.value: "🚀 Готова к доставке",
            OrderStatus.IN_DELIVERY.value: "🚚 В пути",
            OrderStatus.DELIVERED.value: "✅ Доставлена",
            OrderStatus.PAID.value: "💳 Оплачена",
            OrderStatus.PARTIALLY_PAID.value: "💰 Частично оплачена",
            OrderStatus.DEBT.value: "💸 Долг"
        }
        
        return status_map.get(status, status)
    
    def _get_role_display(self, role: str) -> str:
        """Получение отображения роли"""
        role_map = {
            UserRole.DIRECTOR.value: "📊 Директор",
            UserRole.ADMIN.value: "👑 Администратор",
            UserRole.OPERATOR.value: "🔹 Оператор",
            UserRole.COLLECTOR.value: "🔹 Сборщик",
            UserRole.CHECKER.value: "🔹 Проверщик",
            UserRole.COURIER.value: "🔹 Курьер",
            UserRole.SALES_REP.value: "💼 Торговый представитель",
            UserRole.CLIENT.value: "🔹 Клиент"
        }
        
        return role_map.get(role, role)
