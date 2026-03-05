#!/usr/bin/env python3
"""
🚀 Complete CRM Bot - Полная цепочка заказа от клиента до доставки
Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Импортируем aiogram
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем CRM цепочку
from crm_chain import (
    CRMChain, OrderStatus, UserRole, Order, User,
    create_client_order, update_order_status,
    get_user_orders, get_orders_by_status,
    get_dashboard_stats, get_user_by_telegram_id,
    formatter
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('complete_crm.log')
    ]
)

logger = logging.getLogger("complete_crm_bot")

class CompleteCRMBot:
    """Complete CRM Bot с полной цепочкой заказа"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.crm = CRMChain()
        self.start_time = datetime.now()
        self.logger = logging.getLogger("complete_crm_bot")
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            # Получаем токен
            bot_token = os.getenv("BOT_TOKEN")
            if not bot_token:
                raise ValueError("BOT_TOKEN environment variable is required")
            
            # Создаем бота
            self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
            self.dp = Dispatcher()
            
            # Настраиваем обработчики
            await self._setup_handlers()
            
            self.logger.info("✅ Complete CRM Bot initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def _setup_handlers(self):
        """Настройка обработчиков для всех ролей"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            """Обработчик /start - определение роли и показ меню"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Пользователь не найден")
                return
            
            # Показываем приветствие и меню в зависимости от роли
            welcome_text = self._get_welcome_text(user)
            keyboard = self._get_role_keyboard(user.role)
            
            await message.answer(welcome_text, reply_markup=keyboard)
        
        # 📱 Обработчики для клиента
        @self.dp.message(F.text == "📦 Сделать заявку")
        async def cmd_create_order(message: types.Message):
            """Создание заявки клиентом"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "📦 <b>Создание заявки</b>\n\n"
                "Отправьте список препаратов или фото рецепта:",
                reply_markup=self._get_cancel_keyboard()
            )
        
        @self.dp.message(F.text == "💳 Оплата")
        async def cmd_payment(message: types.Message):
            """Оплата заказа"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет активных заказов")
                return
            
            # Показываем последний заказ
            last_order = orders[-1]
            if last_order.status == OrderStatus.CREATED:
                await message.answer(
                    f"💳 <b>Оплата заказа #{last_order.id}</b>\n\n"
                    f"💰 Сумма: ${last_order.amount:.2f}\n\n"
                    "Отправьте фото чека или подтверждение оплаты:",
                    reply_markup=self._get_main_keyboard(UserRole.CLIENT)
                )
            else:
                await message.answer("💳 Заказ уже оплачен или находится в обработке")
        
        @self.dp.message(F.text == "📍 Статус заявки")
        async def cmd_order_status(message: types.Message):
            """Статус заявки клиента"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет заказов")
                return
            
            # Показываем последний заказ
            last_order = orders[-1]
            order_card = formatter.format_order_card(last_order)
            await message.answer(order_card)
        
        @self.dp.message(F.text == "📞 Менеджер")
        async def cmd_manager(message: types.Message):
            """Связь с менеджером"""
            await message.answer(
                "📞 <b>Связь с менеджером</b>\n\n"
                "📱 Телефон: +998 90 123 45 67\n"
                "💬 WhatsApp: +998 90 123 45 67\n"
                "📧 Email: manager@maxxpharm.com\n\n"
                "⏰ Время работы: 9:00 - 18:00"
            )
        
        # 👨‍💻 Обработчики для оператора
        @self.dp.message(F.text == "📥 Новые заявки")
        async def cmd_new_orders(message: types.Message):
            """Новые заявки для оператора"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            new_orders = get_orders_by_status(OrderStatus.CREATED)
            if not new_orders:
                await message.answer("📭 Новых заявок нет")
                return
            
            # Показываем список новых заявок
            orders_text = "📥 <b>Новые заявки</b>\n\n"
            for order in new_orders[:5]:  # Показываем первые 5
                orders_text += f"📦 Заявка #{order.id} - {order.client_name}\n"
                orders_text += f"💰 ${order.amount:.2f} - {order.created_at.strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "💳 Подтверждение оплаты")
        async def cmd_confirm_payment(message: types.Message):
            """Подтверждение оплаты"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            payment_orders = get_orders_by_status(OrderStatus.WAITING_PAYMENT)
            if not payment_orders:
                await message.answer("📭 Заказов ожидающих оплату нет")
                return
            
            orders_text = "💳 <b>Заказы ожидающие оплату</b>\n\n"
            for order in payment_orders[:5]:
                orders_text += f"📦 Заявка #{order.id} - {order.client_name}\n"
                orders_text += f"💰 ${order.amount:.2f}\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "📊 Мои заявки")
        async def cmd_my_orders_operator(message: types.Message):
            """Мои заявки оператора"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет активных заказов")
                return
            
            orders_text = f"📊 <b>Мои заявки ({len(orders)})</b>\n\n"
            for order in orders:
                status_emoji = {
                    OrderStatus.ACCEPTED: "✅",
                    OrderStatus.PROCESSING: "🔄",
                    OrderStatus.READY: "📦",
                    OrderStatus.CHECKING: "🔍",
                    OrderStatus.WAITING_COURIER: "🚚",
                    OrderStatus.ON_WAY: "📍",
                    OrderStatus.DELIVERED: "✅"
                }
                emoji = status_emoji.get(order.status, "📋")
                orders_text += f"{emoji} Заявка #{order.id} - {order.client_name}\n"
                orders_text += f"📊 {order.status.value.replace('_', ' ').title()}\n\n"
            
            await message.answer(orders_text)
        
        # 📦 Обработчики для сборщика
        @self.dp.message(F.text == "📦 Заявки в сборке")
        async def cmd_picker_orders(message: types.Message):
            """Заявки для сборщика"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.PICKER:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет заказов для сборки")
                return
            
            orders_text = f"📦 <b>Заказы в сборке ({len(orders)})</b>\n\n"
            for order in orders:
                orders_text += f"📦 Заявка #{order.id}\n"
                orders_text += f"👤 {order.client_name}\n"
                orders_text += f"📝 {order.text[:50]}...\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "🔄 В обработке")
        async def cmd_processing_orders(message: types.Message):
            """Заказы в обработке"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.PICKER:
                await message.answer("❌ Доступ запрещен")
                return
            
            processing_orders = [o for o in get_user_orders(user.telegram_id) if o.status == OrderStatus.PROCESSING]
            if not processing_orders:
                await message.answer("📭 Нет заказов в обработке")
                return
            
            orders_text = f"🔄 <b>Заказы в обработке ({len(processing_orders)})</b>\n\n"
            for order in processing_orders:
                orders_text += f"📦 Заявка #{order.id}\n"
                orders_text += f"👤 {order.client_name}\n"
                orders_text += f"⏰ Начата: {order.updated_at.strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        # 🔍 Обработчики для проверщика
        @self.dp.message(F.text == "🔍 На проверке")
        async def cmd_checking_orders(message: types.Message):
            """Заказы на проверке"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CHECKER:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 Нет заказов на проверке")
                return
            
            orders_text = f"🔍 <b>Заказы на проверке ({len(orders)})</b>\n\n"
            for order in orders:
                orders_text += f"📦 Заявка #{order.id}\n"
                orders_text += f"👤 {order.client_name}\n"
                orders_text += f"📦 Собрано: {order.updated_at.strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        # 🚚 Обработчики для курьера
        @self.dp.message(F.text == "🚚 Заявки к доставке")
        async def cmd_delivery_orders(message: types.Message):
            """Заказы для доставки"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.COURIER:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 Нет заказов для доставки")
                return
            
            orders_text = f"🚚 <b>Заказы к доставке ({len(orders)})</b>\n\n"
            for order in orders:
                orders_text += f"📦 Заявка #{order.id}\n"
                orders_text += f"👤 {order.client_name}\n"
                orders_text += f"📍 Адрес: ул. Айни 45 (пример)\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "📍 В пути")
        async def cmd_on_way_orders(message: types.Message):
            """Заказы в пути"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.COURIER:
                await message.answer("❌ Доступ запрещен")
                return
            
            on_way_orders = [o for o in get_user_orders(user.telegram_id) if o.status == OrderStatus.ON_WAY]
            if not on_way_orders:
                await message.answer("📭 Нет заказов в пути")
                return
            
            orders_text = f"📍 <b>Заказы в пути ({len(on_way_orders)})</b>\n\n"
            for order in on_way_orders:
                orders_text += f"📦 Заявка #{order.id}\n"
                orders_text += f"👤 {order.client_name}\n"
                orders_text += f"⏰ Выехал: {order.updated_at.strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        # 👑 Обработчики для директора
        @self.dp.message(F.text == "📊 Дашборд")
        async def cmd_dashboard(message: types.Message):
            """Дашборд директора"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            stats = get_dashboard_stats()
            dashboard_text = formatter.format_dashboard(stats)
            await message.answer(dashboard_text)
        
        @self.dp.message(F.text == "👥 Сотрудники")
        async def cmd_staff(message: types.Message):
            """Информация о сотрудниках"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            # Собираем статистику по сотрудникам
            staff_stats = {}
            for u in self.crm.users.values():
                if u.role != UserRole.CLIENT:
                    role_name = u.role.value.title()
                    if role_name not in staff_stats:
                        staff_stats[role_name] = []
                    staff_stats[role_name].append(u)
            
            staff_text = "👥 <b>Сотрудники MAXXPHARM</b>\n\n"
            for role, users in staff_stats.items():
                active_users = [u for u in users if u.is_active]
                staff_text += f"👤 <b>{role}:</b> {len(active_users)}/{len(users)} активных\n"
                
                for u in active_users[:3]:  # Показываем первых 3
                    staff_text += f"  • {u.name} ({u.active_orders} заказов)\n"
                
                if len(active_users) > 3:
                    staff_text += f"  • ... и еще {len(active_users) - 3}\n"
                
                staff_text += "\n"
            
            await message.answer(staff_text)
        
        # 🧪 Тестовые команды
        @self.dp.message(Command("test_chain"))
        async def cmd_test_chain(message: types.Message):
            """Тест полной цепочки заказа"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer("🧪 <b>Тест полной цепочки заказа</b>\n\nНачинаю тест...")
            
            # Запускаем тест
            from crm_chain import test_complete_chain
            order = await test_complete_chain()
            
            await message.answer(f"✅ <b>Тест завершен!</b>\n\n📦 Заказ #{order.id} прошел полный цикл:")
            
            chain_text = """
👤 Клиент → ✅ Принято оператором → 🔄 В сборке → 📦 Собрано → 🔍 Проверено → 🚚 В пути → ✅ Доставлено
"""
            
            await message.answer(chain_text)
        
        @self.dp.message(Command("demo_chain"))
        async def cmd_demo_chain(message: types.Message):
            """Демонстрация цепочки"""
            demo_text = """
🚀 <b>Complete CRM Chain</b>

📦 <b>Полная цепочка заказа:</b>

👤 <b>Клиент</b>
📦 Сделать заявку
💳 Оплата
📍 Статус заявки

👨‍💻 <b>Оператор</b>
📥 Новые заявки
💳 Подтверждение оплаты
📊 Мои заявки

📦 <b>Сборщик</b>
📦 Заявки в сборке
🔄 В обработке

🔍 <b>Проверщик</b>
🔍 На проверке

🚚 <b>Курьер</b>
🚚 Заявки к доставке
📍 В пути

👑 <b>Директор</b>
📊 Дашборд
👥 Сотрудники

🔄 <b>Статусы заказа:</b>
1. created → 2. waiting_payment → 3. accepted → 4. processing → 5. ready → 6. checking → 7. waiting_courier → 8. on_way → 9. delivered

🎯 <b>Автоматическое распределение:</b>
• Оператор → Сборщик (меньшая нагрузка)
• Сборщик → Проверщик (меньшая нагрузка)
• Проверщик → Курьер (меньшая нагрузка)

🧪 <b>Тестирование:</b>
/test_chain - полный тест цепочки
"""
            
            await message.answer(demo_text)
        
        # Обработка текстовых сообщений для создания заявок
        @self.dp.message()
        async def handle_text_message(message: types.Message):
            """Обработка текстовых сообщений"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            # Если клиент отправляет текст, создаем заявку
            if user.role == UserRole.CLIENT and len(message.text) > 10:
                # Создаем тестовые товары
                items = [
                    {"product": "Препарат из сообщения", "quantity": 1, "price": 50.0}
                ]
                
                order = await create_client_order(user.telegram_id, message.text, items)
                
                await message.answer(
                    f"✅ <b>Заявка создана!</b>\n\n"
                    f"📦 Номер: #{order.id}\n"
                    f"💰 Сумма: ${order.amount:.2f}\n"
                    f"📊 Статус: {order.status.value.replace('_', ' ').title()}\n\n"
                    f"⏳ Заявка передана оператору...",
                    reply_markup=self._get_main_keyboard(UserRole.CLIENT)
                )
                
                self.logger.info(f"📦 Order #{order.id} created from message by {user.name}")
    
    def _get_welcome_text(self, user: User) -> str:
        """Получение приветствия в зависимости от роли"""
        if user.role == UserRole.CLIENT:
            return formatter.format_client_welcome(user)
        elif user.role == UserRole.OPERATOR:
            return formatter.format_operator_welcome(user)
        elif user.role == UserRole.PICKER:
            return formatter.format_picker_welcome(user)
        elif user.role == UserRole.CHECKER:
            return formatter.format_checker_welcome(user)
        elif user.role == UserRole.COURIER:
            return formatter.format_courier_welcome(user)
        elif user.role == UserRole.DIRECTOR:
            return formatter.format_director_welcome(user)
        else:
            return f"👋 <b>Здравствуйте, {user.name}!</b>"
    
    def _get_role_keyboard(self, role: UserRole) -> ReplyKeyboardMarkup:
        """Получение клавиатуры в зависимости от роли"""
        if role == UserRole.CLIENT:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📦 Сделать заявку")],
                    [KeyboardButton(text="💳 Оплата"), KeyboardButton(text="📍 Статус заявки")],
                    [KeyboardButton(text="📞 Менеджер")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        elif role == UserRole.OPERATOR:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📥 Новые заявки")],
                    [KeyboardButton(text="💳 Подтверждение оплаты"), KeyboardButton(text="📊 Мои заявки")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        elif role == UserRole.PICKER:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📦 Заявки в сборке")],
                    [KeyboardButton(text="🔄 В обработке")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        elif role == UserRole.CHECKER:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔍 На проверке")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        elif role == UserRole.COURIER:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🚚 Заявки к доставке")],
                    [KeyboardButton(text="📍 В пути")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        elif role == UserRole.DIRECTOR:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📊 Дашборд")],
                    [KeyboardButton(text="👥 Сотрудники")]
                ],
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        else:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="/start")]
                ],
                resize_keyboard=True
            )
    
    def _get_main_keyboard(self, role: UserRole) -> ReplyKeyboardMarkup:
        """Получение главного меню для роли"""
        return self._get_role_keyboard(role)
    
    def _get_cancel_keyboard(self) -> ReplyKeyboardMarkup:
        """Клавиатура с отменой"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True
        )
    
    async def start(self):
        """Запуск бота"""
        try:
            # Удаляем webhook
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            
            logger.info("🚀 Complete CRM Bot starting...")
            logger.info(f"🤖 Bot: @{bot_info.username}")
            logger.info(f"👥 Users: {len(self.crm.users)}")
            logger.info("🔗 Complete CRM Chain ready!")
            
            print("🚀 MAXXPHARM Complete CRM Bot")
            print("🔗 Full order chain: Client → Operator → Picker → Checker → Courier → Delivered")
            print(f"🤖 Bot: @{bot_info.username}")
            print("👥 Test users ready!")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Bot runtime error: {e}")
            raise

async def main():
    """Основная функция"""
    print("🚀 MAXXPHARM Complete CRM Bot starting...")
    print("🔗 Full order chain: Client → Operator → Picker → Checker → Courier → Delivered")
    
    try:
        # Создаем и запускаем бот
        bot = CompleteCRMBot()
        
        if await bot.initialize():
            await bot.start()
        else:
            logger.error("❌ Failed to initialize bot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
