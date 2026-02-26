from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.order_service import OrderService
from src.services.user_service import UserService
from src.keyboards.manager_keyboards import ManagerKeyboards
from src.database import get_session


class ManagerHandlers:
    """Handlers for manager users"""
    
    def __init__(self, router: Router):
        self.router = router
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all manager handlers"""
        # Main menu handlers
        self.router.message(F.text == "📦 Новые заказы", self.handle_new_orders)
        self.router.message(F.text == "⏳ В работе", self.handle_processing_orders)
        self.router.message(F.text == "✔ Завершенные", self.handle_completed_orders)
        self.router.message(F.text == "❌ Отмененные", self.handle_cancelled_orders)
    
    async def handle_new_orders(self, message: types.Message):
        """Handle new orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("NEW")
            
            if not orders:
                await message.answer("📭 Новых заказов暂时 нет")
                return
            
            text = "🆕 *Новые заказы:*\n\n"
            for order in orders:
                text += f"🆕 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   📞 Телефон: {order.phone or 'N/A'}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                text += "\n"
            
            text += "💡 *Действия:*\n"
            text += "• ✅ Подтвердить заказ\n"
            text += "• ❌ Отменить заказ\n"
            text += "• 💬 Связаться с клиентом"
            
            await message.answer(text, reply_markup=ManagerKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_processing_orders(self, message: types.Message):
        """Handle processing orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("CONFIRMED")
            
            if not orders:
                await message.answer("📭 Заказов в обработке暂时 нет")
                return
            
            text = "⏳ *Заказы в обработке:*\n\n"
            for order in orders:
                text += f"⏳ Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                text += "\n"
            
            text += "💡 *Действия:*\n"
            text += "• 🚚 Передать в доставку\n"
            text += "• 💬 Связаться с клиентом"
            
            await message.answer(text, reply_markup=ManagerKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_completed_orders(self, message: types.Message):
        """Handle completed orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("COMPLETED")
            
            if not orders:
                await message.answer("📭 Завершенных заказов暂时 нет")
                return
            
            text = "✔️ *Завершенные заказы:*\n\n"
            for order in orders[:20]:  # Show last 20
                text += f"✔️ Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                if order.delivery_address:
                    text += f"   📍 Адрес: {order.delivery_address}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=ManagerKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_cancelled_orders(self, message: types.Message):
        """Handle cancelled orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("CANCELLED")
            
            if not orders:
                await message.answer("📭 Отмененных заказов暂时 нет")
                return
            
            text = "❌ *Отмененные заказы:*\n\n"
            for order in orders[:20]:  # Show last 20
                text += f"❌ Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                if order.notes:
                    text += f"   📝 Причина: {order.notes}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=ManagerKeyboards.main_menu(), parse_mode="Markdown")
