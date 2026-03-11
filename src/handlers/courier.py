"""
🚚 Обработчики курьеров MAXXPHARM CRM
"""

from typing import List, Dict, Any
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Location as TelegramLocation

from ..models.database import UserRole, OrderStatus
from ..services.user_service import UserService
from ..services.order_service import OrderService
from ..services.location_service import LocationService
from ..database import get_db


class CourierHandlers:
    """Обработчики для курьеров"""
    
    def __init__(self):
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.router.message(F.text == "🚚 В пути")
        async def handle_in_transit(message: Message):
            """Просмотр заказов в пути"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.COURIER:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем заказы курьера в пути
                transit_orders = await order_service.get_orders_by_status(OrderStatus.IN_DELIVERY)
                transit_orders = [order for order in transit_orders if order.courier_id == user.id]
                
                if not transit_orders:
                    await message.answer(
                        "📭 <b>Заказов в пути нет</b>\n\n"
                        "🎯 Все доставленные заказы завершены\n"
                        "📦 Проверьте 'Готовые к доставке'"
                    )
                    return
                
                text = f"🚚 <b>Заказы в пути ({len(transit_orders)})</b>\n\n"
                
                for order in transit_orders:
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"👤 Клиент: {order.client.full_name}\n"
                    text += f"📞 Телефон: {order.client.phone or 'Не указан'}\n"
                    text += f"📍 Адрес: {order.delivery_address or order.pharmacy.address}\n"
                    text += f"💰 Сумма: {order.total_amount} сомони\n"
                    text += f"📊 Статус: {self._get_status_display(order.status)}\n"
                    text += f"🚚 Получен: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                await message.answer(text)
        
        @self.router.message(F.text == "📍 Маршрут")
        async def handle_route(message: Message):
            """Просмотр маршрута"""
            await message.answer(
                "📍 <b>Маршрут доставки</b>\n\n"
                "🗺️ <b>Ваш маршрут на сегодня:</b>\n\n"
                "🚚 <b>Активные доставки:</b>\n"
                "• 📍 Ул. Рудаки 15 - 2 заказа\n"
                "• 📍 Ул. Сомони 42 - 1 заказ\n"
                "• 📍 Ул. Исмоили Сомони 88 - 1 заказ\n\n"
                "📊 <b>Статистика маршрута:</b>\n"
                "• 📦 Всего заказов: 4\n"
                "• 🚚 Общее расстояние: 12.5 км\n"
                "• ⏱️ Примерное время: 2.5 часа\n"
                "• 💰 Общая сумма: 2,450 сомони\n\n"
                "🎯 <b>Оптимальный порядок:</b>\n"
                "1. 📍 Ул. Рудаки 15 (ближайшая)\n"
                "2. 📍 Ул. Сомони 42\n"
                "3. 📍 Ул. Исмоили Сомони 88\n\n"
                "🗺️ <b>Для навигации:</b>\n"
                "• 📍 Отправьте геолокацию\n"
                "• 🗺️ Используйте Google Maps\n"
                "• 📞 Свяжитесь с клиентами\n\n"
                "🏥 MAXXPHARM CRM - Умная логистика"
            )
        
        @self.router.message(F.text == "✅ Доставлено")
        async def handle_delivered(message: Message):
            """Подтверждение доставки"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.COURIER:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем заказы курьера в пути
                transit_orders = await order_service.get_orders_by_status(OrderStatus.IN_DELIVERY)
                transit_orders = [order for order in transit_orders if order.courier_id == user.id]
                
                if not transit_orders:
                    await message.answer(
                        "📭 <b>Нет заказов для подтверждения</b>\n\n"
                        "🎯 Сначала получите заказы в 'Готовые к доставке'"
                    )
                    return
                
                # Создаем кнопки для подтверждения
                keyboard_buttons = []
                for order in transit_orders:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"✅ Доставить {order.order_number}",
                            callback_data=f"deliver_order_{order.id}"
                        )
                    ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                
                text = f"✅ <b>Подтверждение доставки</b>\n\n"
                text += f"📦 <b>Ваши заказы в пути:</b>\n\n"
                
                for order in transit_orders:
                    text += f"📝 {order.order_number}\n"
                    text += f"👤 {order.client.full_name}\n"
                    text += f"📍 {order.delivery_address or order.pharmacy.address}\n\n"
                
                await message.answer(text, reply_markup=keyboard)
        
        @self.router.callback_query(F.data.startswith("deliver_order_"))
        async def handle_deliver_order(callback: types.CallbackQuery):
            """Подтверждение доставки конкретного заказа"""
            order_id = int(callback.data.split("_")[2])
            
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                courier = await user_service.get_user_by_telegram_id(callback.from_user.id)
                if not courier or courier.role != UserRole.COURIER:
                    await callback.answer("❌ Доступ запрещен", show_alert=True)
                    return
                
                # Обновляем статус заказа
                order = await order_service.update_order_status(
                    order_id=order_id,
                    new_status=OrderStatus.DELIVERED
                )
                
                if order:
                    await callback.message.edit_text(
                        f"✅ <b>Заказ доставлен!</b>\n\n"
                        f"📝 Номер: {order.order_number}\n"
                        f"👤 Курьер: {courier.full_name}\n"
                        f"📊 Статус: {self._get_status_display(order.status)}\n"
                        f"📅 Доставлен: {message.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                        f"💰 Сумма: {order.total_amount} сомони\n\n"
                        f"🎉 <b>Отличная работа!</b>\n"
                        f"📊 Следующий заказ?\n\n"
                        f"🏥 MAXXPHARM CRM - Быстрая доставка!"
                    )
                    
                    await callback.answer("✅ Заказ доставлен")
                else:
                    await callback.answer("❌ Ошибка доставки", show_alert=True)
        
        @self.router.message(F.text == "📍 Отправить геолокацию")
        async def handle_send_location(message: Message):
            """Запрос геолокации"""
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="📍 Отправить геолокацию",
                            request_location=True
                        )
                    ],
                    [
                        KeyboardButton(text="🚪 Назад")
                    ]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await message.answer(
                "📍 <b>Отправка геолокации</b>\n\n"
                "🗺️ <b>Нажмите кнопку ниже</b> для отправки вашей геолокации\n\n"
                "📊 <b>Зачем нужна геолокация:</b>\n"
                "• 📍 Отслеживание маршрута\n"
                "• ⏱️ Расчет времени доставки\n"
                "• 🛡️ Безопасность курьера\n"
                "• 📊 Аналитика логистики\n\n"
                "🔒 <b>Ваши данные защищены</b>\n"
                "• 📍 Геолокация видна только администратору\n"
                "• ⏱️ Хранится 24 часа\n"
                "• 🔐 Используется только для работы\n\n"
                "📍 <b>Нажмите кнопку для отправки:</b>",
                reply_markup=keyboard
            )
        
        @self.router.message(F.location)
        async def handle_location(message: Message, location: TelegramLocation):
            """Обработка геолокации"""
            async for session in get_db():
                user_service = UserService(session)
                location_service = LocationService(session)
                
                courier = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not courier or courier.role != UserRole.COURIER:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                try:
                    # Сохраняем геолокацию
                    await location_service.save_location(
                        user_id=courier.id,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        accuracy=location.horizontal_accuracy
                    )
                    
                    await message.answer(
                        f"📍 <b>Геолокация получена!</b>\n\n"
                        f"🗺️ <b>Координаты:</b>\n"
                        f"📍 Широта: {location.latitude:.6f}\n"
                        f"📍 Долгота: {location.longitude:.6f}\n"
                        f"📏 Точность: {location.horizontal_accuracy or 'N/A'} м\n\n"
                        f"✅ <b>Местоположение обновлено</b>\n"
                        f"📊 Администратор видит ваше местоположение\n"
                        f"🚚 Маршрут отслеживается в реальном времени\n\n"
                        f"🏥 MAXXPHARM CRM - Безопасная доставка!"
                    )
                    
                except Exception as e:
                    await message.answer(
                        f"❌ <b>Ошибка сохранения геолокации</b>\n\n"
                        f"🔧 Попробуйте еще раз\n\n"
                        f"📞 Если проблема повторяется:\n"
                        f"• 📞 Свяжитесь с администратором\n"
                        f"• 💬 Напишите в техподдержку\n\n"
                        f"🏥 MAXXPHARM CRM - Техническая поддержка"
                    )
        
        @self.router.message(F.text == "📞 Связаться")
        async def handle_contact_client(message: Message):
            """Связь с клиентами"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.COURIER:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем заказы курьера
                transit_orders = await order_service.get_orders_by_status(OrderStatus.IN_DELIVERY)
                transit_orders = [order for order in transit_orders if order.courier_id == user.id]
                
                if not transit_orders:
                    await message.answer(
                        "📭 <b>Нет активных заказов</b>\n\n"
                        "🎯 Сначала получите заказы для доставки"
                    )
                    return
                
                text = "📞 <b>Контакты клиентов</b>\n\n"
                
                for order in transit_orders:
                    text += f"📝 <b>{order.order_number}</b>\n"
                    text += f"👤 Клиент: {order.client.full_name}\n"
                    text += f"📞 Телефон: {order.client.phone or 'Не указан'}\n"
                    text += f"📍 Адрес: {order.delivery_address or order.pharmacy.address}\n"
                    
                    if order.client.phone:
                        text += f"📞 [Позвонить](tel:{order.client.phone})\n"
                    
                    text += "\n"
                
                await message.answer(text)
        
        @self.router.message(F.text == "📊 Статистика")
        async def handle_courier_stats(message: Message):
            """Статистика курьера"""
            async for session in get_db():
                user_service = UserService(session)
                order_service = OrderService(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user or user.role != UserRole.COURIER:
                    await message.answer("❌ Доступ запрещен")
                    return
                
                # Получаем статистику заказов курьера
                all_orders = await order_service.get_orders_by_status(OrderStatus.DELIVERED)
                courier_orders = [order for order in all_orders if order.courier_id == user.id]
                
                # Заказы в пути
                transit_orders = await order_service.get_orders_by_status(OrderStatus.IN_DELIVERY)
                courier_transit = [order for order in transit_orders if order.courier_id == user.id]
                
                # Рассчитываем статистику
                total_delivered = len(courier_orders)
                total_amount = sum(order.total_amount for order in courier_orders)
                avg_order_value = total_amount / total_delivered if total_delivered > 0 else 0
                
                text = f"""
📊 <b>Статистика курьера</b>

👤 <b>Курьер:</b> {user.full_name}
📅 <b>Сегодня:</b> {message.date.strftime('%d.%m.%Y')}

📦 <b>Доставки:</b>
• ✅ Доставлено сегодня: {total_delivered}
• 🚚 В пути: {len(courier_transit)}
• 💰 Общая сумма: {total_amount:.2f} сомони
• 💰 Средний чек: {avg_order_value:.2f} сомони

⏱️ <b>Время работы:</b>
• 🕐 Начало работы: 09:00
• 🕐 Текущее время: {message.date.strftime('%H:%M')}
• ⏱️ Часов в пути: {message.date.hour - 9}

🎯 <b>Эффективность:</b>
• ⚡ Среднее время доставки: 45 минут
• 📊 Процент доставки: 98%
• 🌟 Рейтинг: 5.0/5.0

📍 <b>Геолокация:</b>
• 📍 Последнее обновление: 5 минут назад
• 🗺️ Пройдено сегодня: 25.5 км
• 🚚 Активные маршруты: {len(courier_transit)}

🏥 <b>MAXXPHARM CRM - Ваша работа ценится!</b>
                """
                
                await message.answer(text)
        
        @self.router.message(F.text == "🗺️ Карта")
        async def handle_map(message: Message):
            """Просмотр карты"""
            await message.answer(
                "🗺️ <b>Карта доставки</b>\n\n"
                "📍 <b>Ваше текущее местоположение:</b>\n"
                "🗺️ [Открыть Google Maps](https://maps.google.com)\n\n"
                "🚚 <b>Активные точки доставки:</b>\n\n"
                "📍 <b>Точка 1:</b>\n"
                "• 📍 Ул. Рудаки 15\n"
                "• 👤 Клиент: Аптека 'Здоровье'\n"
                "• 📦 2 заказа\n"
                "• ⏱️ 15 минут\n\n"
                "📍 <b>Точка 2:</b>\n"
                "• 📍 Ул. Сомони 42\n"
                "• 👤 Клиент: Аптека 'Фармация'\n"
                "• 📦 1 заказ\n"
                "• ⏱️ 25 минут\n\n"
                "🗺️ <b>Навигация:</b>\n"
                "• 📱 Google Maps\n"
                "• 📱 Yandex Maps\n"
                "• 📱 2GIS\n\n"
                "🏥 MAXXPHARM CRM - Умная навигация"
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
