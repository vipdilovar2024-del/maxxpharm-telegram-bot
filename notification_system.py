#!/usr/bin/env python3
"""
📢 Notification System - Система уведомлений SaaS CRM
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from aiogram import Bot
from saas_crm_core import SaaSCRMCore, UserRole, OrderStatus

class NotificationSystem:
    """Система уведомлений"""
    
    def __init__(self, bot: Bot, crm: SaaSCRMCore):
        self.bot = bot
        self.crm = crm
        self.logger = logging.getLogger("notification_system")
        
        # 🎭 Шаблоны уведомлений
        self.notification_templates = {
            "order_created": {
                UserRole.CLIENT: "📦 Ваша заявка #{order_id} создана и ожидает оплаты",
                UserRole.OPERATOR: "📥 Новая заявка #{order_id} от клиента {client_name}",
                UserRole.ADMIN: "📊 Создана новая заявка #{order_id}"
            },
            "payment_confirmed": {
                UserRole.CLIENT: "✅ Оплата заявки #{order_id} подтверждена. Заказ в обработке",
                UserRole.PICKER: "📦 Новая заявка #{order_id} для сборки",
                UserRole.ADMIN: "💰 Оплата заявки #{order_id} подтверждена"
            },
            "order_processing": {
                UserRole.CLIENT: "🔄 Ваша заявка #{order_id} в сборке",
                UserRole.ADMIN: "📦 Заявка #{order_id} в сборке"
            },
            "order_ready": {
                UserRole.CLIENT: "📦 Ваша заявка #{order_id} собрана и готова к проверке",
                UserRole.CHECKER: "🔍 Новая заявка #{order_id} на проверку",
                UserRole.ADMIN: "✅ Заявка #{order_id} собрана"
            },
            "order_checked": {
                UserRole.CLIENT: "✅ Ваша заявка #{order_id} проверена и готова к доставке",
                UserRole.COURIER: "🚚 Новая заявка #{order_id} для доставки",
                UserRole.ADMIN: "🔍 Заявка #{order_id} проверена"
            },
            "order_on_way": {
                UserRole.CLIENT: "🚚 Ваша заявка #{order_id} в пути! Ожидайте доставку",
                UserRole.ADMIN: "🚚 Заявка #{order_id} в пути"
            },
            "order_delivered": {
                UserRole.CLIENT: "✅ Ваша заявка #{order_id} доставлена! Спасибо за заказ!",
                UserRole.ADMIN: "✅ Заявка #{order_id} доставлена"
            },
            "order_rejected": {
                UserRole.CLIENT: "❌ Ваша заявка #{order_id} отклонена. Свяжитесь с менеджером",
                UserRole.ADMIN: "❌ Заявка #{order_id} отклонена"
            }
        }
    
    async def notify_role(self, role: UserRole, message: str, exclude_users: List[int] = None):
        """Отправка уведомления всем пользователям роли"""
        exclude_users = exclude_users or []
        
        for user in self.crm.users.values():
            if user.role == role and user.id not in exclude_users and user.is_active:
                try:
                    await self.bot.send_message(user.telegram_id, message)
                    await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями
                except Exception as e:
                    self.logger.error(f"❌ Failed to notify user {user.id}: {e}")
    
    async def notify_user(self, user_id: int, message: str):
        """Отправка уведомления конкретному пользователю"""
        user = self.crm.users.get(user_id)
        if not user:
            return False
        
        try:
            await self.bot.send_message(user.telegram_id, message)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to notify user {user_id}: {e}")
            return False
    
    async def notify_order_status_change(self, order_id: int, old_status: OrderStatus, new_status: OrderStatus, changed_by: int):
        """Уведомление об изменении статуса заказа"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        # Определяем тип уведомления
        notification_key = f"order_{new_status.value}"
        
        # Получаем шаблон
        templates = self.notification_templates.get(notification_key, {})
        
        # Отправляем уведомления разным ролям
        for role, template in templates.items():
            try:
                # Формируем сообщение
                message = template.format(
                    order_id=order_id,
                    client_name=self._get_client_name(order.client_id),
                    amount=order.amount
                )
                
                # Добавляем временную метку
                message += f"\n🕐 {datetime.now().strftime('%H:%M')}"
                
                # Отправляем уведомление
                if role == UserRole.CLIENT:
                    await self.notify_user(order.client_id, message)
                else:
                    await self.notify_role(role, message, exclude_users=[changed_by])
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to send notification for {role}: {e}")
    
    async def notify_new_order(self, order_id: int):
        """Уведомление о новом заказе"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        # Уведомляем операторов
        await self.notify_role(
            UserRole.OPERATOR,
            f"📥 <b>Новая заявка #{order_id}</b>\n\n"
            f"👤 Клиент: {self._get_client_name(order.client_id)}\n"
            f"💰 Сумма: ${order.amount}\n"
            f"📝 {order.text[:100]}...\n\n"
            f"🔥 Срочно обработайте!",
            exclude_users=[order.client_id]
        )
        
        # Уведомляем админов
        await self.notify_role(
            UserRole.ADMIN,
            f"📊 <b>Новая заявка #{order_id}</b>\n\n"
            f"💰 Сумма: ${order.amount}\n"
            f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}",
            exclude_users=[order.client_id]
        )
    
    async def notify_payment_confirmation(self, order_id: int, confirmed_by: int):
        """Уведомление о подтверждении оплаты"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        # Уведомляем клиента
        await self.notify_user(
            order.client_id,
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"📦 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n\n"
            f"🔄 Ваш заказ передан в сборку"
        )
        
        # Уведомляем сборщиков
        await self.notify_role(
            UserRole.PICKER,
            f"📦 <b>Новая заявка для сборки</b>\n\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n"
            f"📝 {order.text[:50]}...",
            exclude_users=[confirmed_by, order.client_id]
        )
    
    async def notify_order_ready_for_delivery(self, order_id: int):
        """Уведомление о готовности заказа к доставке"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        # Уведомляем курьеров
        await self.notify_role(
            UserRole.COURIER,
            f"🚚 <b>Новая заявка для доставки</b>\n\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n"
            f"👤 Клиент: {self._get_client_name(order.client_id)}\n\n"
            f"🔥 Заберите заказ для доставки!"
        )
        
        # Уведомляем клиента
        await self.notify_user(
            order.client_id,
            f"📦 <b>Ваш заказ готов!</b>\n\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n\n"
            f"🚚 Курьер скоро заберет заказ"
        )
    
    async def notify_order_delivered(self, order_id: int, delivered_by: int):
        """Уведомление о доставке заказа"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        # Уведомляем клиента
        await self.notify_user(
            order.client_id,
            f"✅ <b>Заказ доставлен!</b>\n\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n\n"
            f"🙏 Спасибо за покупку!\n"
            f"⭐ Оцените качество обслуживания"
        )
        
        # Уведомляем админов
        await self.notify_role(
            UserRole.ADMIN,
            f"✅ <b>Заказ доставлен!</b>\n\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n"
            f"👤 Курьер: {self._get_user_name(delivered_by)}",
            exclude_users=[delivered_by, order.client_id]
        )
    
    async def notify_system_alert(self, alert_type: str, message: str, roles: List[UserRole] = None):
        """Системное уведомление"""
        if roles is None:
            roles = [UserRole.ADMIN, UserRole.DIRECTOR]
        
        alert_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }
        
        emoji = alert_emoji.get(alert_type, "📢")
        
        alert_message = f"""
{emoji} <b>Системное уведомление</b>

{message}

🕐 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        for role in roles:
            await self.notify_role(role, alert_message)
    
    async def notify_daily_summary(self):
        """Ежедневная сводка для директора"""
        dashboard_data = self.crm.get_dashboard_data()
        
        summary = f"""
📊 <b>Ежедневная сводка MAXXPHARM</b>
📅 {datetime.now().strftime('%d %B %Y')}

📈 <b>Сегодня:</b>
• Заказов: {dashboard_data['today_orders']}
• Доставлено: {dashboard_data['delivered_today']}
• Отказ: {dashboard_data['rejected_today']}
• Выручка: ${dashboard_data['total_revenue']}

📊 <b>Активность:</b>
• Активных заказов: {dashboard_data['active_orders']}
• Всего пользователей: {dashboard_data['total_users']}

🎯 <b>Конверсия:</b> {round((dashboard_data['delivered_today'] / dashboard_data['today_orders'] * 100) if dashboard_data['today_orders'] > 0 else 0, 1)}%
"""
        
        await self.notify_role(UserRole.DIRECTOR, summary)
    
    def _get_client_name(self, client_id: int) -> str:
        """Получение имени клиента"""
        client = self.crm.users.get(client_id)
        return client.name if client else f"Клиент #{client_id}"
    
    def _get_user_name(self, user_id: int) -> str:
        """Получение имени пользователя"""
        user = self.crm.users.get(user_id)
        return user.name if user else f"Пользователь #{user_id}"
    
    async def send_bulk_notification(self, user_ids: List[int], message: str):
        """Массовая отправка уведомлений"""
        tasks = []
        for user_id in user_ids:
            tasks.append(self.notify_user(user_id, message))
        
        # Отправляем все уведомления параллельно
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_order_assignment(self, order_id: int, assigned_to: int, role: UserRole):
        """Уведомление о назначении заказа"""
        order = self.crm.orders.get(order_id)
        if not order:
            return
        
        role_names = {
            UserRole.PICKER: "сборщик",
            UserRole.CHECKER: "проверщик",
            UserRole.COURIER: "курьер"
        }
        
        role_name = role_names.get(role, "исполнитель")
        
        await self.notify_user(
            assigned_to,
            f"📋 <b>Назначен новый заказ</b>\n\n"
            f"🔹 Роль: {role_name}\n"
            f"📋 Заявка #{order_id}\n"
            f"💰 Сумма: ${order.amount}\n"
            f"📝 {order.text[:50]}...\n\n"
            f"🔥 Начните работу!"
        )
