#!/usr/bin/env python3
"""
📱 UX Interface - Визуальный интерфейс Telegram CRM как приложение
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.enums import ParseMode
from typing import List, Dict, Optional
from datetime import datetime

# 🎨 Визуальные стили
class UXStyles:
    """Стили для визуального оформления"""
    
    # Эмодзи для статусов
    STATUS_EMOJI = {
        "created": "📝",
        "waiting_payment": "💳",
        "rejected": "❌",
        "accepted": "✅",
        "processing": "🔄",
        "ready": "📦",
        "checking": "🔍",
        "waiting_courier": "🚚",
        "on_way": "📍",
        "delivered": "✅"
    }
    
    # Цвета статусов (через эмодзи)
    STATUS_COLORS = {
        "created": "🟡",
        "waiting_payment": "🟠",
        "rejected": "🔴",
        "accepted": "🟢",
        "processing": "🔵",
        "ready": "🟣",
        "checking": "🟤",
        "waiting_courier": "🟦",
        "on_way": "🟪",
        "delivered": "🟩"
    }

class ClientUX:
    """UX интерфейс для клиента"""
    
    @staticmethod
    def get_welcome_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню клиента"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Сделать заявку")],
                [KeyboardButton(text="💳 Оплата"), KeyboardButton(text="📍 Моя заявка")],
                [KeyboardButton(text="📞 Менеджер"), KeyboardButton(text="ℹ️ Информация")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_order_creation_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура создания заявки"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Текстом")],
                [KeyboardButton(text="📷 Фото рецепта")],
                [KeyboardButton(text="🎤 Голосом")],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите способ..."
        )
    
    @staticmethod
    def get_payment_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура оплаты"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💳 Оплатил", callback_data="payment_confirmed"),
                    InlineKeyboardButton(text="❌ Проблема", callback_data="payment_issue")
                ]
            ]
        )
    
    @staticmethod
    def format_order_card(order: Dict) -> str:
        """Форматирование карточки заказа"""
        status_emoji = UXStyles.STATUS_EMOJI.get(order.get('status', 'created'), '📝')
        
        return f"""
📦 <b>Заявка #{order['id']}</b>

{status_emoji} <b>Статус:</b> {order.get('status_text', 'Создана')}
💰 <b>Сумма:</b> ${order.get('amount', 0)}
📅 <b>Создана:</b> {order.get('created_at', '').strftime('%d.%m.%Y %H:%M')}

📋 <b>Содержание:</b>
{order.get('text', 'Нет описания')[:100]}...

🕐 <b>Последнее обновление:</b> {order.get('updated_at', '').strftime('%H:%M')}
"""
    
    @staticmethod
    def format_welcome_message(user_name: str) -> str:
        """Сообщение приветствия"""
        return f"""
👋 <b>Здравствуйте, {user_name}!</b>

Добро пожаловать в систему заказов фармпрепаратов 🏥

Выберите действие из меню ниже 👇
"""

class OperatorUX:
    """UX интерфейс для оператора"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню оператора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📥 Новые заявки")],
                [KeyboardButton(text="💳 Проверить оплату"), KeyboardButton(text="📊 Мои заявки")],
                [KeyboardButton(text="🔎 Найти заявку"), KeyboardButton(text="📈 Статистика")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура действий с заявкой"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_order_{order_id}"),
                    InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_order_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="💳 Подтвердить оплату", callback_data=f"confirm_payment_{order_id}")
                ]
            ]
        )
    
    @staticmethod
    def format_new_orders_list(orders: List[Dict]) -> str:
        """Форматирование списка новых заявок"""
        if not orders:
            return "📭 <b>Новых заявок нет</b>"
        
        header = f"📥 <b>Новые заявки ({len(orders)})</b>\n\n"
        order_list = []
        
        for order in orders[:10]:  # Показываем первые 10
            status_emoji = UXStyles.STATUS_EMOJI.get(order.get('status', 'created'), '📝')
            order_list.append(
                f"{status_emoji} <b>#{order['id']}</b> {order.get('client_name', 'Клиент')}\n"
                f"💰 ${order.get('amount', 0)} • 📅 {order.get('created_at', '').strftime('%H:%M')}"
            )
        
        return header + "\n".join(order_list)
    
    @staticmethod
    def format_order_details(order: Dict) -> str:
        """Детальная информация о заявке"""
        return f"""
📋 <b>Заявка #{order['id']}</b>

👤 <b>Клиент:</b> {order.get('client_name', 'Неизвестно')}
📞 <b>Телефон:</b> {order.get('phone', 'Не указан')}
💰 <b>Сумма:</b> ${order.get('amount', 0)}
📅 <b>Создана:</b> {order.get('created_at', '').strftime('%d.%m.%Y %H:%M')}

📝 <b>Содержание заявки:</b>
{order.get('text', 'Нет описания')}

📦 <b>Препараты:</b>
{order.get('items_text', 'Не указаны')}

{UXStyles.STATUS_COLORS.get(order.get('status', 'created'), '🟡')} <b>Статус:</b> {order.get('status_text', 'Создана')}
"""

class PickerUX:
    """UX интерфейс для сборщика"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню сборщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Заявки в сборке")],
                [KeyboardButton(text="🔄 В обработке"), KeyboardButton(text="✅ Готово")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_picker_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура действий сборщика"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Начать сборку", callback_data=f"start_picking_{order_id}"),
                    InlineKeyboardButton(text="✅ Собрано", callback_data=f"finish_picking_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="❌ Проблема", callback_data=f"picking_issue_{order_id}")
                ]
            ]
        )
    
    @staticmethod
    def format_picker_orders(orders: List[Dict]) -> str:
        """Форматирование заказов для сборщика"""
        if not orders:
            return "📭 <b>Назначенных заявок нет</b>"
        
        header = f"📦 <b>Заявки в сборке ({len(orders)})</b>\n\n"
        order_list = []
        
        for order in orders:
            urgency = "🔥" if order.get('urgent', False) else "📦"
            order_list.append(
                f"{urgency} <b>#{order['id']}</b>\n"
                f"📝 {order.get('text', 'Нет описания')[:30]}...\n"
                f"💰 ${order.get('amount', 0)} • 📅 {order.get('created_at', '').strftime('%H:%M')}"
            )
        
        return header + "\n\n".join(order_list)

class CheckerUX:
    """UX интерфейс для проверщика"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню проверщика"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 На проверке")],
                [KeyboardButton(text="❌ Ошибка"), KeyboardButton(text="✅ Проверено")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_checker_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура действий проверщика"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Проверено", callback_data=f"check_passed_{order_id}"),
                    InlineKeyboardButton(text="❌ Ошибка", callback_data=f"check_failed_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="📝 Комментарий", callback_data=f"add_comment_{order_id}")
                ]
            ]
        )
    
    @staticmethod
    def format_checking_order(order: Dict) -> str:
        """Форматирование заказа на проверке"""
        return f"""
🔍 <b>Проверка заказа #{order['id']}</b>

📦 <b>Проверить:</b>
• Серию препаратов
• Срок годности
• Количество
• Комплектность

📋 <b>Содержание:</b>
{order.get('items_text', 'Не указаны')}

💰 <b>Сумма:</b> ${order.get('amount', 0)}

⏱️ <b>Время проверки:</b> {datetime.now().strftime('%H:%M')}
"""

class CourierUX:
    """UX интерфейс для курьера"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню курьера"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚚 Заявки к доставке")],
                [KeyboardButton(text="📍 В пути"), KeyboardButton(text="✅ Доставлено")],
                [KeyboardButton(text="📊 Статистика")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def get_courier_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
        """Клавиатура действий курьера"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚚 Взять заказ", callback_data=f"take_delivery_{order_id}"),
                    InlineKeyboardButton(text="📍 В пути", callback_data=f"on_way_{order_id}")
                ],
                [
                    InlineKeyboardButton(text="✅ Доставлено", callback_data=f"delivered_{order_id}")
                ]
            ]
        )
    
    @staticmethod
    def format_delivery_order(order: Dict) -> str:
        """Форматирование заказа для доставки"""
        return f"""
🚚 <b>Заказ #{order['id']}</b>

👤 <b>Клиент:</b> {order.get('client_name', 'Неизвестно')}
📍 <b>Адрес:</b> {order.get('address', 'Не указан')}
📞 <b>Телефон:</b> {order.get('phone', 'Не указан')}

📦 <b>Содержание:</b>
{order.get('items_text', 'Не указано')}

💰 <b>Сумма:</b> ${order.get('amount', 0)}

⏱️ <b>Время доставки:</b> {datetime.now().strftime('%H:%M')}
"""

class DirectorUX:
    """UX интерфейс для директора"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню директора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Дашборд")],
                [KeyboardButton(text="📈 Продажи"), KeyboardButton(text="📦 Воронка заказов")],
                [KeyboardButton(text="⏱ Время обработки"), KeyboardButton(text="👥 Сотрудники")],
                [KeyboardButton(text="🧠 AI Анализ")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def format_dashboard(data: Dict) -> str:
        """Форматирование дашборда"""
        return f"""
📊 <b>Дашборд MAXXPHARM</b>
📅 {datetime.now().strftime('%d %B %Y')}

📈 <b>Сегодня:</b>
📦 Заказов: {data.get('today_orders', 0)}
🚚 Доставлено: {data.get('delivered_today', 0)}
❌ Отказ: {data.get('rejected_today', 0)}

💰 <b>Финансы:</b>
💵 Выручка: ${data.get('total_revenue', 0):,}
💳 Средний чек: ${data.get('avg_order', 0):,}

📊 <b>Конверсия:</b> {data.get('conversion_rate', 0):.1f}%

👥 <b>Активность:</b>
🔥 Активных заказов: {data.get('active_orders', 0)}
👤 Онлайн сотрудников: {data.get('online_staff', 0)}
"""
    
    @staticmethod
    def format_sales_funnel(data: Dict) -> str:
        """Форматирование воронки продаж"""
        return f"""
📦 <b>Воронка заказов</b>

📝 Создано: {data.get('created', 0)}
💳 Оплачено: {data.get('paid', 0)}
✅ Принято: {data.get('accepted', 0)}
🔄 В обработке: {data.get('processing', 0)}
🚚 Доставлено: {data.get('delivered', 0)}

📈 <b>Конверсия:</b>
💳 Оплата: {(data.get('paid', 0) / data.get('created', 1) * 100):.1f}%
✅ Принятие: {(data.get('accepted', 0) / data.get('paid', 1) * 100):.1f}%
🚚 Доставка: {(data.get('delivered', 0) / data.get('accepted', 1) * 100):.1f}%
"""
    
    @staticmethod
    def format_ai_report(report: Dict) -> str:
        """Форматирование AI отчета"""
        return f"""
🧠 <b>AI Анализ бизнеса</b>

📊 <b>Метрики дня:</b>
📦 Заказов: {report.get('orders', 0)}
💰 Выручка: ${report.get('revenue', 0):,}
👥 Клиентов: {report.get('clients', 0)}

⚠️ <b>Проблемы:</b>
"""
        
        for problem in report.get('problems', []):
            report_text += f"• {problem}\n"
        
        report_text += f"""
💡 <b>Рекомендации:</b>
"""
        
        for recommendation in report.get('recommendations', []):
            report_text += f"• {recommendation}\n"
        
        report_text += f"""
🎯 <b>Прогноз на завтра:</b>
📦 {report.get('forecast_orders', 0)} заказов
💰 ${report.get('forecast_revenue', 0):,} выручки

🕐 {datetime.now().strftime('%H:%M')}
"""
        
        return report_text

class AdminUX:
    """UX интерфейс для администратора"""
    
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        """Главное меню администратора"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Все заявки")],
                [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📈 Аналитика")],
                [KeyboardButton(text="🧾 Логи"), KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def format_users_list(users: List[Dict]) -> str:
        """Форматирование списка пользователей"""
        if not users:
            return "📭 <b>Пользователей нет</b>"
        
        header = f"👥 <b>Пользователи ({len(users)})</b>\n\n"
        user_list = []
        
        for user in users[:20]:  # Показываем первых 20
            status = "🟢" if user.get('is_active', True) else "🔴"
            role_emoji = {
                'client': '👤',
                'operator': '👨‍💻',
                'picker': '📦',
                'checker': '🔍',
                'courier': '🚚',
                'admin': '👑',
                'director': '🎯'
            }.get(user.get('role', 'client'), '👤')
            
            user_list.append(
                f"{status} {role_emoji} <b>{user.get('name', 'Неизвестно')}</b>\n"
                f"📞 {user.get('phone', 'Нет телефона')} • 📅 {user.get('created_at', '').strftime('%d.%m.%Y')}"
            )
        
        return header + "\n\n".join(user_list)

# 🎨 Глобальные UX функции
class UXHelper:
    """Вспомогательные функции UX"""
    
    @staticmethod
    def format_status_badge(status: str) -> str:
        """Форматирование значка статуса"""
        emoji = UXStyles.STATUS_EMOJI.get(status, '📝')
        color = UXStyles.STATUS_COLORS.get(status, '🟡')
        return f"{color} {emoji} {status.title()}"
    
    @staticmethod
    def format_price(amount: float) -> str:
        """Форматирование цены"""
        return f"${amount:,.2f}"
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Форматирование даты и времени"""
        return dt.strftime('%d.%m.%Y %H:%M')
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """Форматирование времени"""
        return dt.strftime('%H:%M')
    
    @staticmethod
    def get_loading_message() -> str:
        """Сообщение загрузки"""
        return "⏳ <b>Загрузка...</b>"
    
    @staticmethod
    def get_success_message(action: str) -> str:
        """Сообщение об успехе"""
        return f"✅ <b>{action} выполнено успешно!</b>"
    
    @staticmethod
    def get_error_message(error: str) -> str:
        """Сообщение об ошибке"""
        return f"❌ <b>Ошибка:</b> {error}"
    
    @staticmethod
    def get_empty_state_message(entity: str) -> str:
        """Сообщение пустого состояния"""
        return f"📭 <b>{entity} нет</b>"
