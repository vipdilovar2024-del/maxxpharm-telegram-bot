from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.order_service import OrderService
from src.services.user_service import UserService
from src.keyboards.courier_keyboards import CourierKeyboards
from src.database import get_session


class CourierHandlers:
    """Handlers for courier users"""
    
    def __init__(self, router: Router):
        self.router = router
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all courier handlers"""
        # Main menu handlers
        self.router.message(F.text == "🚚 Мои доставки", self.handle_my_deliveries)
        self.router.message(F.text == "📍 Адреса", self.handle_addresses)
        self.router.message(F.text == "📞 Связь с клиентом", self.handle_contact_client)
        self.router.message(F.text == "✅ Доставлено", self.handle_delivered)
    
    async def handle_my_deliveries(self, message: types.Message):
        """Handle courier deliveries"""
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                await message.answer("❌ Ошибка: пользователь не найден")
                return
            
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_DELIVERY")
            
            if not orders:
                await message.answer("📭 У вас暂时 нет доставок")
                return
            
            text = "🚚 *Мои доставки:*\n\n"
            for order in orders:
                text += f"🚚 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   📞 Телефон: {order.phone or 'N/A'}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            text += "💡 *Действия:*\n"
            text += "• 📍 Показать адреса\n"
            text += "• 📞 Связаться с клиентом\n"
            text += "• ✅ Отметить доставленным"
            
            await message.answer(text, reply_markup=CourierKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_addresses(self, message: types.Message):
        """Handle delivery addresses"""
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                await message.answer("❌ Ошибка: пользователь не найден")
                return
            
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_DELIVERY")
            
            if not orders:
                await message.answer("📭 У вас暂时 нет доставок")
                return
            
            text = "📍 *Адреса доставок:*\n\n"
            for order in orders:
                text += f"🚚 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   📞 Телефон: {order.phone or 'N/A'}\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                else:
                    text += f"   📍 Адрес: не указан\n"
                text += "\n"
            
            await message.answer(text, reply_markup=CourierKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_contact_client(self, message: types.Message):
        """Handle contact client"""
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                await message.answer("❌ Ошибка: пользователь не найден")
                return
            
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_DELIVERY")
            
            if not orders:
                await message.answer("📭 У вас暂时 нет доставок")
                return
            
            text = "📞 *Контакты клиентов:*\n\n"
            for order in orders:
                text += f"🚚 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   📞 Телефон: {order.phone or 'N/A'}\n"
                text += f"   🆔 Telegram ID: {order.user.telegram_id}\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                text += "\n"
            
            text += "💡 *Как связаться:*\n"
            text += "• 📞 Позвонить по номеру телефона\n"
            text += "• 💬 Написать в Telegram (если доступно)\n"
            text += "• 📍 Использовать адрес для навигации"
            
            await message.answer(text, reply_markup=CourierKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_delivered(self, message: types.Message):
        """Handle delivered order"""
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                await message.answer("❌ Ошибка: пользователь не найден")
                return
            
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_DELIVERY")
            
            if not orders:
                await message.answer("📭 У вас暂时 нет доставок")
                return
            
            text = "✅ *Отметить доставку:*\n\n"
            text += "Выберите заказ для отметки доставки:\n\n"
            
            for order in orders:
                text += f"🚚 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📍 {order.delivery_address or 'Адрес не указан'}\n\n"
            
            text += "💡 *Для отметки доставки:*\n"
            text += "Введите номер заказа (например: 123)"
            
            await message.answer(text, reply_markup=CourierKeyboards.main_menu(), parse_mode="Markdown")
