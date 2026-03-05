"""
🔔 Notifications - Уведомления для MAXXPHARM CRM
aiogram 3.4.1 compatible
"""

import logging
from typing import Dict, Any, Optional
from aiogram import Bot

from keyboards.order_cards_new import get_order_status_emoji

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def notify_client_status_change(self, client_id: int, order_id: int, new_status: str, additional_info: str = ""):
        """Уведомление клиента об изменении статуса"""
        
        status_emoji = get_order_status_emoji(new_status)
        status_title = new_status.replace("_", " ").title()
        
        message = f"📦 <b>Статус заказа #{order_id} изменен</b>\n\n"
        message += f"{status_emoji} <b>Новый статус:</b> {status_title}"
        
        if additional_info:
            message += f"\n\n{additional_info}"
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Notification sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending notification to client {client_id}: {e}")
    
    async def notify_new_order(self, operator_ids: list, order: Dict[str, Any]):
        """Уведомление операторов о новом заказе"""
        
        message = f"📥 <b>Новая заявка #{order['id']}</b>\n\n"
        message += f"👤 <b>Клиент:</b> {order.get('client_name', 'Не указано')}\n"
        message += f"💰 <b>Сумма:</b> {order.get('amount', 0):.0f} сомони\n"
        message += f"📝 <b>Комментарий:</b> {order.get('comment', 'Нет комментария')[:100]}..."
        
        for operator_id in operator_ids:
            try:
                await self.bot.send_message(operator_id, message)
                logger.info(f"🔔 Notification sent to operator {operator_id} for new order {order['id']}")
            except Exception as e:
                logger.error(f"❌ Error sending notification to operator {operator_id}: {e}")
    
    async def notify_picker_assigned(self, picker_id: int, order: Dict[str, Any]):
        """Уведомление сборщика о назначении"""
        
        message = f"📦 <b>Новый заказ для сборки #{order['id']}</b>\n\n"
        message += f"👤 <b>Клиент:</b> {order.get('client_name', 'Не указано')}\n"
        message += f"💰 <b>Сумма:</b> {order.get('amount', 0):.0f} сомони\n"
        message += f"📝 <b>Комментарий:</b> {order.get('comment', 'Нет комментария')[:100]}..."
        
        try:
            await self.bot.send_message(picker_id, message)
            logger.info(f"🔔 Notification sent to picker {picker_id} for order {order['id']}")
        except Exception as e:
            logger.error(f"❌ Error sending notification to picker {picker_id}: {e}")
    
    async def notify_checker_assigned(self, checker_id: int, order: Dict[str, Any]):
        """Уведомление проверщика о назначении"""
        
        message = f"🔍 <b>Заказ для проверки #{order['id']}</b>\n\n"
        message += f"👤 <b>Клиент:</b> {order.get('client_name', 'Не указано')}\n"
        message += f"💰 <b>Сумма:</b> {order.get('amount', 0):.0f} сомони\n"
        message += f"📦 <b>Сборщик:</b> {order.get('picker_name', 'Не указано')}"
        
        try:
            await self.bot.send_message(checker_id, message)
            logger.info(f"🔔 Notification sent to checker {checker_id} for order {order['id']}")
        except Exception as e:
            logger.error(f"❌ Error sending notification to checker {checker_id}: {e}")
    
    async def notify_courier_assigned(self, courier_id: int, order: Dict[str, Any]):
        """Уведомление курьера о назначении"""
        
        message = f"🚚 <b>Заказ для доставки #{order['id']}</b>\n\n"
        message += f"👤 <b>Клиент:</b> {order.get('client_name', 'Не указано')}\n"
        message += f"📞 <b>Телефон:</b> {order.get('client_phone', 'Не указано')}\n"
        message += f"📍 <b>Адрес:</b> {order.get('client_address', 'Не указано')}"
        
        try:
            await self.bot.send_message(courier_id, message)
            logger.info(f"🔔 Notification sent to courier {courier_id} for order {order['id']}")
        except Exception as e:
            logger.error(f"❌ Error sending notification to courier {courier_id}: {e}")
    
    async def notify_order_delivered(self, client_id: int, order_id: int):
        """Уведомление клиента о доставке"""
        
        message = f"✅ <b>Заказ #{order_id} доставлен!</b>\n\n"
        message += "Спасибо за заказ! Надеемся, всё было в порядке.\n\n"
        message += "Если у вас есть вопросы, пожалуйста, свяжитесь с нами:\n"
        message += "📞 Телефон: +998 90 123 45 67"
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Delivery notification sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending delivery notification to client {client_id}: {e}")
    
    async def notify_payment_confirmed(self, client_id: int, order_id: int):
        """Уведомление клиента о подтверждении оплаты"""
        
        message = f"💳 <b>Оплата подтверждена!</b>\n\n"
        message += f"Ваш заказ #{order_id} передан в сборку.\n\n"
        message += "Мы сообщим вам, когда заказ будет готов."
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Payment confirmation sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending payment notification to client {client_id}: {e}")
    
    async def notify_order_ready(self, client_id: int, order_id: int):
        """Уведомление клиента о готовности заказа"""
        
        message = f"📦 <b>Заказ #{order_id} готов!</b>\n\n"
        message += "Заказ собран и проходит проверку качества.\n\n"
        message += "Скорее всего, курьер уже выехал к вам!"
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Ready notification sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending ready notification to client {client_id}: {e}")
    
    async def notify_courier_on_way(self, client_id: int, order_id: int, courier_name: str):
        """Уведомление клиента о выезде курьера"""
        
        message = f"🚚 <b>Курьер выехал!</b>\n\n"
        message += f"Курьер {courier_name} уже в пути с вашим заказом #{order_id}.\n\n"
        message += "Пожалуйста, будьте на месте и подготовьте деньги для оплаты."
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Courier on way notification sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending courier notification to client {client_id}: {e}")
    
    async def notify_order_cancelled(self, client_id: int, order_id: int, reason: str = ""):
        """Уведомление клиента об отмене заказа"""
        
        message = f"❌ <b>Заказ #{order_id} отменен</b>\n\n"
        
        if reason:
            message += f"Причина: {reason}\n\n"
        
        message += "Приносим извинения за неудобства.\n\n"
        message += "Если у вас есть вопросы, пожалуйста, свяжитесь с нами:\n"
        message += "📞 Телефон: +998 90 123 45 67"
        
        try:
            await self.bot.send_message(client_id, message)
            logger.info(f"🔔 Cancellation notification sent to client {client_id} for order {order_id}")
        except Exception as e:
            logger.error(f"❌ Error sending cancellation notification to client {client_id}: {e}")
    
    async def send_daily_report(self, director_id: int, stats: Dict[str, Any]):
        """Отправка дневного отчета директору"""
        
        message = f"📊 <b>Дневной отчет MAXXPHARM</b>\n\n"
        message += f"📅 <b>Дата:</b> {stats.get('date', 'Не указано')}\n\n"
        message += f"📦 <b>Заказы:</b>\n"
        message += f"• Всего: {stats.get('total_orders', 0)}\n"
        message += f"• Доставлено: {stats.get('delivered_orders', 0)}\n"
        message += f"• Отменено: {stats.get('cancelled_orders', 0)}\n"
        message += f"• В работе: {stats.get('in_progress_orders', 0)}\n\n"
        message += f"💰 <b>Выручка:</b> {stats.get('total_revenue', 0):.0f} сомони\n\n"
        
        # Добавляем рекомендации если есть
        if stats.get('recommendations'):
            message += f"💡 <b>Рекомендации:</b>\n"
            for rec in stats['recommendations'][:3]:
                message += f"• {rec}\n"
        
        try:
            await self.bot.send_message(director_id, message)
            logger.info(f"🔔 Daily report sent to director {director_id}")
        except Exception as e:
            logger.error(f"❌ Error sending daily report to director {director_id}: {e}")
    
    async def send_alert(self, admin_id: int, alert_type: str, message: str):
        """Отправка алерта администратору"""
        
        alert_emoji = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }
        
        emoji = alert_emoji.get(alert_type, "📢")
        
        alert_message = f"{emoji} <b>{alert_type.title()} Alert</b>\n\n{message}"
        
        try:
            await self.bot.send_message(admin_id, alert_message)
            logger.info(f"🔔 Alert sent to admin {admin_id}: {alert_type}")
        except Exception as e:
            logger.error(f"❌ Error sending alert to admin {admin_id}: {e}")

# Удобные функции для использования
async def notify_status_change(bot: Bot, client_id: int, order_id: int, new_status: str, additional_info: str = ""):
    """Уведомление об изменении статуса (удобная функция)"""
    service = NotificationService(bot)
    await service.notify_client_status_change(client_id, order_id, new_status, additional_info)

async def notify_new_order(bot: Bot, operator_ids: list, order: Dict[str, Any]):
    """Уведомление о новом заказе (удобная функция)"""
    service = NotificationService(bot)
    await service.notify_new_order(operator_ids, order)

async def notify_delivery(bot: Bot, client_id: int, order_id: int):
    """Уведомление о доставке (удобная функция)"""
    service = NotificationService(bot)
    await service.notify_order_delivered(client_id, order_id)
