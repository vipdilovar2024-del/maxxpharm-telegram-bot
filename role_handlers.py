#!/usr/bin/env python3
"""
👥 Обработчики для каждой роли SaaS CRM
"""

from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from saas_crm_core import SaaSCRMCore, UserRole, OrderStatus
import asyncio
from datetime import datetime

class ClientHandlers:
    """Обработчики для клиентов"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_client_menu(self) -> ReplyKeyboardMarkup:
        """Меню клиента"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Сделать заявку")],
                [KeyboardButton(text="💳 Оплата")],
                [KeyboardButton(text="📍 Моя заявка")],
                [KeyboardButton(text="📞 Менеджер")],
                [KeyboardButton(text="ℹ️ Информация")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_start(self, message: Message):
        """Команда /start для клиента"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.CLIENT:
            await message.answer("❌ Доступ запрещен!")
            return
        
        welcome_text = f"""
👋 Добро пожаловать, {user.name}!

📦 MAXXPHARM - ваш надежный партнер

Выберите действие из меню:
"""
        
        await message.answer(welcome_text, reply_markup=self.get_client_menu())
    
    async def cmd_create_order(self, message: Message):
        """Создание заявки"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.CLIENT:
            await message.answer("❌ Доступ запрещен!")
            return
        
        await message.answer(
            "📝 <b>Создание заявки</b>\n\n"
            "Напишите текст заявки или отправьте фото/голосовое сообщение",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="❌ Отмена")],
                    [KeyboardButton(text="📷 Фото"), KeyboardButton(text="🎤 Голос")]
                ],
                resize_keyboard=True
            )
        )
    
    async def cmd_my_orders(self, message: Message):
        """Мои заявки"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.CLIENT:
            await message.answer("❌ Доступ запрещен!")
            return
        
        orders = self.crm.get_user_orders(user.id)
        
        if not orders:
            await message.answer("📭 У вас пока нет заявок")
            return
        
        orders_text = "📦 <b>Ваши заявки:</b>\n\n"
        
        for order in orders:
            status_emoji = {
                OrderStatus.CREATED: "📝",
                OrderStatus.WAITING_PAYMENT: "💳",
                OrderStatus.ACCEPTED: "✅",
                OrderStatus.PROCESSING: "🔄",
                OrderStatus.READY: "📦",
                OrderStatus.CHECKING: "🔍",
                OrderStatus.ON_WAY: "🚚",
                OrderStatus.DELIVERED: "✅",
                OrderStatus.REJECTED: "❌"
            }
            
            orders_text += f"{status_emoji.get(order.status, '📋')} <b>Заявка #{order.id}</b>\n"
            orders_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            orders_text += f"📝 {order.text[:50]}...\n"
            orders_text += f"💰 ${order.amount}\n"
            orders_text += f"📊 Статус: {order.status.value}\n\n"
        
        await message.answer(orders_text)

class OperatorHandlers:
    """Обработчики для операторов"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_operator_menu(self) -> ReplyKeyboardMarkup:
        """Меню оператора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📥 Новые заявки")],
                [KeyboardButton(text="💳 Подтверждение оплаты")],
                [KeyboardButton(text="📊 Мои заявки")],
                [KeyboardButton(text="🔎 Поиск заявки")],
                [KeyboardButton(text="📈 Статистика")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_new_orders(self, message: Message):
        """Новые заявки"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.OPERATOR:
            await message.answer("❌ Доступ запрещен!")
            return
        
        # Получаем новые заявки (статус CREATED или WAITING_PAYMENT)
        new_orders = [
            order for order in self.crm.orders.values()
            if order.status in [OrderStatus.CREATED, OrderStatus.WAITING_PAYMENT]
        ]
        
        if not new_orders:
            await message.answer("📭 Новых заявок нет")
            return
        
        orders_text = "📥 <b>Новые заявки:</b>\n\n"
        
        for order in new_orders:
            orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
            orders_text += f"👤 Клиент: {order.client_id}\n"
            orders_text += f"📝 {order.text[:50]}...\n"
            orders_text += f"💰 ${order.amount}\n"
            orders_text += f"📊 Статус: {order.status.value}\n"
            orders_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(orders_text)
    
    async def cmd_confirm_payment(self, message: Message):
        """Подтверждение оплаты"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.OPERATOR:
            await message.answer("❌ Доступ запрещен!")
            return
        
        # Получаем заявки ожидающие подтверждения оплаты
        waiting_orders = [
            order for order in self.crm.orders.values()
            if order.status == OrderStatus.WAITING_PAYMENT
        ]
        
        if not waiting_orders:
            await message.answer("📭 Заявок ожидающих оплаты нет")
            return
        
        orders_text = "💳 <b>Заявки ожидающие оплаты:</b>\n\n"
        
        for order in waiting_orders:
            orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
            orders_text += f"👤 Клиент: {order.client_id}\n"
            orders_text += f"💰 ${order.amount}\n"
            orders_text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        orders_text += "💡 Для подтверждения оплаты введите: /confirm_payment [ID заявки]"
        
        await message.answer(orders_text)
    
    async def cmd_confirm_payment_id(self, message: Message):
        """Подтверждение оплаты по ID"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.OPERATOR:
            await message.answer("❌ Доступ запрещен!")
            return
        
        try:
            order_id = int(message.text.split()[1])
        except (IndexError, ValueError):
            await message.answer("❌ Неверный формат. Используйте: /confirm_payment [ID заявки]")
            return
        
        order = self.crm.orders.get(order_id)
        if not order or order.status != OrderStatus.WAITING_PAYMENT:
            await message.answer("❌ Заявка не найдена или не ожидает оплаты")
            return
        
        # Подтверждаем оплату
        if self.crm.change_order_status(order_id, OrderStatus.ACCEPTED, user.id):
            await message.answer(f"✅ Оплата заявки #{order_id} подтверждена")
            
            # Уведомляем клиента
            await self.bot.send_message(
                order.client_id,
                f"✅ Ваша заявка #{order_id} принята в обработку!"
            )
        else:
            await message.answer("❌ Не удалось подтвердить оплату")

class PickerHandlers:
    """Обработчики для сборщиков"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_picker_menu(self) -> ReplyKeyboardMarkup:
        """Меню сборщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Заявки в сборке")],
                [KeyboardButton(text="🔄 В обработке")],
                [KeyboardButton(text="✅ Готово")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_picker_orders(self, message: Message):
        """Заявки в сборке"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.PICKER:
            await message.answer("❌ Доступ запрещен!")
            return
        
        # Получаем заявки назначенные этому сборщику
        picker_orders = [
            order for order in self.crm.orders.values()
            if order.assigned_picker == user.id and order.status in [OrderStatus.ACCEPTED, OrderStatus.PROCESSING]
        ]
        
        if not picker_orders:
            await message.answer("📭 Назначенных заявок нет")
            return
        
        orders_text = "📦 <b>Заявки в сборке:</b>\n\n"
        
        for order in picker_orders:
            orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
            orders_text += f"📝 {order.text[:50]}...\n"
            orders_text += f"💰 ${order.amount}\n"
            orders_text += f"📊 Статус: {order.status.value}\n\n"
        
        await message.answer(orders_text)

class CheckerHandlers:
    """Обработчики для проверщиков"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_checker_menu(self) -> ReplyKeyboardMarkup:
        """Меню проверщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 На проверке")],
                [KeyboardButton(text="❌ Ошибка")],
                [KeyboardButton(text="✅ Проверено")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_checker_orders(self, message: Message):
        """Заявки на проверке"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.CHECKER:
            await message.answer("❌ Доступ запрещен!")
            return
        
        # Получаем заявки назначенные этому проверщику
        checker_orders = [
            order for order in self.crm.orders.values()
            if order.assigned_checker == user.id and order.status == OrderStatus.READY
        ]
        
        if not checker_orders:
            await message.answer("📭 Заявок на проверке нет")
            return
        
        orders_text = "🔍 <b>Заявки на проверке:</b>\n\n"
        
        for order in checker_orders:
            orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
            orders_text += f"📝 {order.text[:50]}...\n"
            orders_text += f"💰 ${order.amount}\n\n"
        
        await message.answer(orders_text)

class CourierHandlers:
    """Обработчики для курьеров"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_courier_menu(self) -> ReplyKeyboardMarkup:
        """Меню курьера"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚚 Заявки к доставке")],
                [KeyboardButton(text="📍 В пути")],
                [KeyboardButton(text="✅ Доставлено")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_courier_orders(self, message: Message):
        """Заявки к доставке"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.COURIER:
            await message.answer("❌ Доступ запрещен!")
            return
        
        # Получаем заявки назначенные этому курьеру
        courier_orders = [
            order for order in self.crm.orders.values()
            if order.assigned_courier == user.id and order.status in [OrderStatus.WAITING_COURIER, OrderStatus.ON_WAY]
        ]
        
        if not courier_orders:
            await message.answer("📭 Заявок к доставке нет")
            return
        
        orders_text = "🚚 <b>Заявки к доставке:</b>\n\n"
        
        for order in courier_orders:
            orders_text += f"📋 <b>Заявка #{order.id}</b>\n"
            orders_text += f"📝 {order.text[:50]}...\n"
            orders_text += f"💰 ${order.amount}\n"
            orders_text += f"📊 Статус: {order.status.value}\n\n"
        
        await message.answer(orders_text)

class DirectorHandlers:
    """Обработчики для директора"""
    
    def __init__(self, crm: SaaSCRMCore, bot):
        self.crm = crm
        self.bot = bot
    
    def get_director_menu(self) -> ReplyKeyboardMarkup:
        """Меню директора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Дашборд")],
                [KeyboardButton(text="📈 Продажи")],
                [KeyboardButton(text="📦 Воронка заказов")],
                [KeyboardButton(text="⏱ Время обработки")],
                [KeyboardButton(text="👥 Сотрудники")],
                [KeyboardButton(text="🧠 AI Анализ")]
            ],
            resize_keyboard=True
        )
    
    async def cmd_dashboard(self, message: Message):
        """Дашборд директора"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.DIRECTOR:
            await message.answer("❌ Доступ запрещен!")
            return
        
        dashboard_data = self.crm.get_dashboard_data()
        
        report = f"""
📊 <b>Дашборд MAXXPHARM</b>
📅 {datetime.now().strftime('%d %B %Y')}

📈 <b>Сегодня:</b>
• Заказов: {dashboard_data['today_orders']}
• Доставлено: {dashboard_data['delivered_today']}
• Отказ: {dashboard_data['rejected_today']}
• Выручка: ${dashboard_data['total_revenue']}

📊 <b>Общая статистика:</b>
• Всего пользователей: {dashboard_data['total_users']}
• Активных заказов: {dashboard_data['active_orders']}

📋 <b>Статусы заказов:</b>
"""
        
        for status, count in dashboard_data['status_counts'].items():
            if count > 0:
                report += f"• {status}: {count}\n"
        
        await message.answer(report)
    
    async def cmd_analytics(self, message: Message):
        """Аналитика"""
        user = self.crm.users.get(message.from_user.id)
        if not user or user.role != UserRole.DIRECTOR:
            await message.answer("❌ Доступ запрещен!")
            return
        
        analytics = self.crm.get_analytics(days=7)
        
        report = f"""
📈 <b>Аналитика за {analytics['period_days']} дней</b>

📊 <b>Заказы:</b>
• Всего: {analytics['total_orders']}
• Доставлено: {analytics['delivered_orders']}
• Конверсия: {analytics['conversion_rate']}%

💰 <b>Финансы:</b>
• Общая выручка: ${analytics['total_revenue']}
• Выручка в день: ${analytics['revenue_per_day']}

⏱️ <b>Время обработки:</b>
• Среднее время: {analytics['avg_processing_time']} часов
"""
        
        await message.answer(report)
