#!/usr/bin/env python3
"""
📱 Uber-like CRM Bot - Идеальный интерфейс как приложение
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

# Импортируем UX
from uber_ux import (
    UberLikeUX, OrderStatus, UserRole, Order, User,
    create_order_from_text, update_order_status_callback,
    get_user_orders, get_orders_by_status,
    get_dashboard_stats, get_user_by_telegram_id,
    formatter, keyboard_builder
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('uber_crm.log')
    ]
)

logger = logging.getLogger("uber_crm_bot")

class UberCRMBot:
    """Uber-like CRM Bot с идеальным UX"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.ux = UberLikeUX()
        self.start_time = datetime.now()
        self.logger = logging.getLogger("uber_crm_bot")
    
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
            
            self.logger.info("✅ Uber CRM Bot initialized")
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
                "📦 <b>Новая заявка</b>\n\n"
                "Отправьте список препаратов, фото рецепта или голосовое сообщение:",
                reply_markup=keyboard_builder.get_cancel_keyboard()
            )
        
        @self.dp.message(F.text == "📍 Мои заказы")
        async def cmd_my_orders(message: types.Message):
            """Мои заказы клиента"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CLIENT:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет заказов")
                return
            
            orders_text = formatter.format_client_orders_list(orders)
            await message.answer(orders_text)
        
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
                    f"💰 Сумма: {last_order.amount:.0f} сомони\n\n"
                    "Отправьте фото чека или подтверждение оплаты:",
                    reply_markup=keyboard_builder.get_client_main_keyboard()
                )
            else:
                await message.answer("💳 Заказ уже оплачен или находится в обработке")
        
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
        
        @self.dp.message(F.text == "ℹ️ Информация")
        async def cmd_info(message: types.Message):
            """Информация о сервисе"""
            await message.answer(
                "ℹ️ <b>О MAXXPHARM</b>\n\n"
                "🏥 <b>Система заказов фармпрепаратов</b>\n\n"
                "📱 <b>Наши преимущества:</b>\n"
                "• Быстрая доставка по городу\n"
                "• Только качественные препараты\n"
                "• Удобная оплата\n"
                "• Отслеживание заказа\n\n"
                "🚚 <b>Доставка:</b>\n"
                "• По Душанбе: 1-2 часа\n"
                "• По району: 3-4 часа\n"
                "• Бесплатно при заказе от 100 сомони\n\n"
                "💳 <b>Оплата:</b>\n"
                "• Наличными курьеру\n"
                "• Банковской картой\n"
                "• Через платежные системы\n\n"
                "📞 <b>Контакты:</b>\n"
                "• Телефон: +998 90 123 45 67\n"
                "• Email: info@maxxpharm.com\n"
                "• Сайт: www.maxxpharm.com\n\n"
                "🕐 <b>Время работы:</b>\n"
                "• Пн-Пт: 9:00 - 18:00\n"
                "• Сб: 9:00 - 15:00\n"
                "• Вс: выходной\n\n"
                "Спасибо, что выбрали нас! 🙏"
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
            
            orders_text = formatter.format_new_orders_list(new_orders)
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
            
            orders_text = formatter.format_new_orders_list(payment_orders)
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "📦 Все заказы")
        async def cmd_all_orders(message: types.Message):
            """Все заказы оператора"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет активных заказов")
                return
            
            orders_text = f"📊 <b>Мои заказы ({len(orders)})</b>\n\n"
            for order in orders:
                orders_text += f"{order.status.emoji} <b>#{order.id}</b> {order.client_name}\n"
                orders_text += f"📊 {order.status.title}\n\n"
            
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "🔎 Найти заказ")
        async def cmd_find_order(message: types.Message):
            """Поиск заказа"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.OPERATOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer(
                "🔎 <b>Поиск заказа</b>\n\n"
                "Введите номер заказа (например: 245):",
                reply_markup=keyboard_builder.get_operator_main_keyboard()
            )
        
        # 📦 Обработчики для сборщика
        @self.dp.message(F.text == "📦 Заказы на сборку")
        async def cmd_picker_orders(message: types.Message):
            """Заказы для сборщика"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.PICKER:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 У вас нет заказов для сборки")
                return
            
            orders_text = formatter.format_picker_orders_list(orders)
            await message.answer(orders_text)
        
        @self.dp.message(F.text == "🔄 В сборке")
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
            
            orders_text = f"🔄 <b>Заказы в сборке ({len(processing_orders)})</b>\n\n"
            for order in processing_orders:
                orders_text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
                orders_text += f"⏰ Начата: {order.updated_at.strftime('%H:%M')}\n\n"
            
            await message.answer(orders_text)
        
        # 🔍 Обработчики для проверщика
        @self.dp.message(F.text == "🔍 Заказы на проверке")
        async def cmd_checker_orders(message: types.Message):
            """Заказы на проверке"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.CHECKER:
                await message.answer("❌ Доступ запрещен")
                return
            
            orders = get_user_orders(user.telegram_id)
            if not orders:
                await message.answer("📭 Нет заказов на проверке")
                return
            
            orders_text = formatter.format_checker_orders_list(orders)
            await message.answer(orders_text)
        
        # 🚚 Обработчики для курьера
        @self.dp.message(F.text == "🚚 Заказы к доставке")
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
            
            orders_text = formatter.format_courier_orders_list(orders)
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
                orders_text += f"📦 <b>#{order.id}</b> {order.client_name}\n"
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
        
        @self.dp.message(F.text == "📈 Продажи")
        async def cmd_sales(message: types.Message):
            """Продажи"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            # Анализ продаж
            all_orders = list(self.ux.orders.values())
            
            # Топ товаров
            product_sales = {}
            for order in all_orders:
                for item in order.items:
                    product = item.get('product', 'Товар')
                    if product not in product_sales:
                        product_sales[product] = 0
                    product_sales[product] += item.get('quantity', 1)
            
            # Сортируем и берем топ
            top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            
            sales_text = "📈 <b>Продажи</b>\n\n"
            sales_text += f"📦 <b>Всего заказов:</b> {len(all_orders)}\n\n"
            
            if top_products:
                sales_text += "🏆 <b>Топ препараты:</b>\n"
                for i, (product, count) in enumerate(top_products, 1):
                    sales_text += f"{i}. {product} - {count} шт.\n"
            
            await message.answer(sales_text)
        
        @self.dp.message(F.text == "👥 Сотрудники")
        async def cmd_staff(message: types.Message):
            """Сотрудники"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            # Собираем статистику по сотрудникам
            staff_stats = {}
            for u in self.ux.users.values():
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
        @self.dp.message(Command("test_uber"))
        async def cmd_test_uber(message: types.Message):
            """Тест Uber-like UX"""
            user = get_user_by_telegram_id(message.from_user.id)
            if not user or user.role != UserRole.DIRECTOR:
                await message.answer("❌ Доступ запрещен")
                return
            
            await message.answer("🧱 <b>Тест Uber-like UX</b>\n\nНачинаю тест...")
            
            # Запускаем тест
            from uber_ux import test_uber_ux
            order = await test_uber_ux()
            
            await message.answer(f"✅ <b>Тест завершен!</b>\n\n📦 Заказ #{order.id} прошел полный цикл:")
            
            chain_text = """
👤 Клиент → ✅ Оператор → 🔄 Сборщик → 📦 Готово → 🔍 Проверщик → 🚚 Курьер → ✅ Доставлено
"""
            
            await message.answer(chain_text)
        
        @self.dp.message(Command("demo_uber"))
        async def cmd_demo_uber(message: types.Message):
            """Демонстрация Uber-like UX"""
            demo_text = """
📱 <b>Uber-like CRM Interface</b>

🎯 <b>Полная цепочка заказа:</b>

👤 <b>Клиент</b>
📦 Сделать заявку
📍 Мои заказы
💳 Оплата
📞 Менеджер

👨‍💻 <b>Оператор</b>
📥 Новые заявки
💳 Подтверждение оплаты
📦 Все заказы
🔎 Найти заказ

📦 <b>Сборщик</b>
📦 Заказы на сборку
🔄 В сборке

🔍 <b>Проверщик</b>
🔍 Заказы на проверке

🚚 <b>Курьер</b>
🚚 Заказы к доставке
📍 В пути

👑 <b>Директор</b>
📊 Дашборд
📈 Продажи
👥 Сотрудники

🎨 <b>UX особенности:</b>
• 📱 Интерфейс как мобильное приложение
• 📦 Универсальные карточки заказов
• 🎯 Inline кнопки действий
• 🔄 Автоматическое распределение
• 📊 Real-time статус
• 🔔 Уведомления на каждом этапе

🧪 <b>Тестирование:</b>
/test_uber - полный тест цепочки
/demo_uber - эта демонстрация

💡 <b>Ключевое преимущество:</b>
Сотрудник работает как в приложении, а не в чате!
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
                try:
                    order = await create_order_from_text(user.telegram_id, message.text)
                    
                    # Отправляем карточку заказа
                    order_card = formatter.format_order_card(order)
                    
                    await message.answer(
                        f"✅ <b>Заявка создана!</b>\n\n"
                        f"{order_card}"
                        f"Мы скоро проверим ваш заказ",
                        reply_markup=keyboard_builder.get_client_main_keyboard()
                    )
                    
                    self.logger.info(f"📦 Order #{order.id} created from message by {user.name}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error creating order: {e}")
                    await message.answer("❌ Ошибка создания заявки")
        
        # 🎯 Callback обработчики
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery):
            """Обработка inline кнопок"""
            try:
                data = callback.data
                user = get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("❌ Пользователь не найден")
                    return
                
                # Разбираем callback
                if data.startswith("accept_order_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_accept_order(callback, order_id, user)
                
                elif data.startswith("reject_order_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_reject_order(callback, order_id, user)
                
                elif data.startswith("start_picking_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_start_picking(callback, order_id, user)
                
                elif data.startswith("finish_picking_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_finish_picking(callback, order_id, user)
                
                elif data.startswith("check_passed_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_check_passed(callback, order_id, user)
                
                elif data.startswith("check_error_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_check_error(callback, order_id, user)
                
                elif data.startswith("take_delivery_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_take_delivery(callback, order_id, user)
                
                elif data.startswith("on_way_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_on_way(callback, order_id, user)
                
                elif data.startswith("delivered_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_delivered(callback, order_id, user)
                
                elif data.startswith("call_client_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_call_client(callback, order_id, user)
                
                elif data.startswith("order_details_"):
                    order_id = int(data.split("_")[2])
                    await self._handle_order_details(callback, order_id, user)
                
                else:
                    await callback.answer("❌ Неизвестное действие")
                    
            except Exception as e:
                self.logger.error(f"❌ Callback error: {e}")
                await callback.answer("❌ Ошибка обработки")
    
    async def _handle_accept_order(self, callback: CallbackQuery, order_id: int, user: User):
        """Принятие заказа оператором"""
        if user.role != UserRole.OPERATOR:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.ACCEPTED, user.id)
        if success:
            await callback.answer("✅ Заказ принят")
            await callback.message.edit_text("✅ <b>Заказ принят в обработку</b>")
        else:
            await callback.answer("❌ Не удалось принять заказ")
    
    async def _handle_reject_order(self, callback: CallbackQuery, order_id: int, user: User):
        """Отклонение заказа оператором"""
        if user.role != UserRole.OPERATOR:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.CANCELLED, user.id)
        if success:
            await callback.answer("❌ Заказ отклонен")
            await callback.message.edit_text("❌ <b>Заказ отклонен</b>")
        else:
            await callback.answer("❌ Не удалось отклонить заказ")
    
    async def _handle_start_picking(self, callback: CallbackQuery, order_id: int, user: User):
        """Начало сборки"""
        if user.role != UserRole.PICKER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.PROCESSING, user.id)
        if success:
            await callback.answer("🔄 Сборка начата")
            await callback.message.edit_text("🔄 <b>Сборка начата</b>")
        else:
            await callback.answer("❌ Не удалось начать сборку")
    
    async def _handle_finish_picking(self, callback: CallbackQuery, order_id: int, user: User):
        """Завершение сборки"""
        if user.role != UserRole.PICKER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.READY, user.id)
        if success:
            await callback.answer("📦 Собрано")
            await callback.message.edit_text("📦 <b>Заказ собран</b>")
        else:
            await callback.answer("❌ Не удалось завершить сборку")
    
    async def _handle_check_passed(self, callback: CallbackQuery, order_id: int, user: User):
        """Проверка пройдена"""
        if user.role != UserRole.CHECKER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.WAITING_COURIER, user.id)
        if success:
            await callback.answer("✅ Проверено")
            await callback.message.edit_text("✅ <b>Проверка пройдена</b>")
        else:
            await callback.answer("❌ Не удалось подтвердить проверку")
    
    async def _handle_check_error(self, callback: CallbackQuery, order_id: int, user: User):
        """Ошибка проверки"""
        if user.role != UserRole.CHECKER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        await callback.answer("❌ Обнаружена ошибка")
        await callback.message.edit_text("❌ <b>Обнаружена ошибка</b>")
    
    async def _handle_take_delivery(self, callback: CallbackQuery, order_id: int, user: User):
        """Взятие заказа на доставку"""
        if user.role != UserRole.COURIER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.ON_WAY, user.id)
        if success:
            await callback.answer("🚚 Заказ взят")
            await callback.message.edit_text("🚚 <b>Заказ взят на доставку</b>")
        else:
            await callback.answer("❌ Не удалось взять заказ")
    
    async def _handle_on_way(self, callback: CallbackQuery, order_id: int, user: User):
        """В пути"""
        if user.role != UserRole.COURIER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        await callback.answer("📍 В пути")
        await callback.message.edit_text("📍 <b>Курьер в пути</b>")
    
    async def _handle_delivered(self, callback: CallbackQuery, order_id: int, user: User):
        """Доставка завершена"""
        if user.role != UserRole.COURIER:
            await callback.answer("❌ Доступ запрещен")
            return
        
        success = await update_order_status_callback(order_id, OrderStatus.DELIVERED, user.id)
        if success:
            await callback.answer("✅ Доставлено")
            await callback.message.edit_text("✅ <b>Заказ доставлен</b>")
        else:
            await callback.answer("❌ Не удалось подтвердить доставку")
    
    async def _handle_call_client(self, callback: CallbackQuery, order_id: int, user: User):
        """Позвонить клиенту"""
        if user.role != UserRole.OPERATOR:
            await callback.answer("❌ Доступ запрещен")
            return
        
        order = self.ux.orders.get(order_id)
        if order:
            await callback.answer(f"📞 Телефон клиента: {order.client_phone}")
        else:
            await callback.answer("❌ Заказ не найден")
    
    async def _handle_order_details(self, callback: CallbackQuery, order_id: int, user: User):
        """Детали заказа"""
        order = self.ux.orders.get(order_id)
        if order:
            order_card = formatter.format_order_card(order)
            await callback.message.answer(order_card)
            await callback.answer("📋 Детали заказа")
        else:
            await callback.answer("❌ Заказ не найден")
    
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
            return keyboard_builder.get_client_main_keyboard()
        elif role == UserRole.OPERATOR:
            return keyboard_builder.get_operator_main_keyboard()
        elif role == UserRole.PICKER:
            return keyboard_builder.get_picker_main_keyboard()
        elif role == UserRole.CHECKER:
            return keyboard_builder.get_checker_main_keyboard()
        elif role == UserRole.COURIER:
            return keyboard_builder.get_courier_main_keyboard()
        elif role == UserRole.DIRECTOR:
            return keyboard_builder.get_director_main_keyboard()
        else:
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="/start")]
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
            
            logger.info("📱 Uber CRM Bot starting...")
            logger.info(f"🤖 Bot: @{bot_info.username}")
            logger.info(f"👥 Users: {len(self.ux.users)}")
            logger.info("📱 Uber-like UX ready!")
            
            print("📱 MAXXPHARM Uber-like CRM Bot")
            print("🎯 Interface like mobile app")
            print(f"🤖 Bot: @{bot_info.username}")
            print("👥 Test users ready!")
            
            # Запускаем polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Bot runtime error: {e}")
            raise

async def main():
    """Основная функция"""
    print("📱 MAXXPHARM Uber-like CRM Bot starting...")
    print("🎯 Interface like mobile app: Client → Operator → Picker → Checker → Courier → Delivered")
    
    try:
        # Создаем и запускаем бот
        bot = UberCRMBot()
        
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
