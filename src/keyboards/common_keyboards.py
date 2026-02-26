from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class CommonKeyboards:
    """Common keyboards for all users"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard"""
        builder = ReplyKeyboardBuilder()
        
        # Determine user role and show appropriate menu
        # This will be customized based on user role
        builder.row(
            KeyboardButton(text="🛍 Каталог"),
            KeyboardButton(text="🔍 Поиск")
        )
        builder.row(
            KeyboardButton(text="🛒 Корзина"),
            KeyboardButton(text="📦 Мои заказы")
        )
        builder.row(
            KeyboardButton(text="📞 Поддержка"),
            KeyboardButton(text="ℹ️ О нас")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        """Admin menu keyboard"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="📦 Заказы")
        )
        builder.row(
            KeyboardButton(text="👥 Пользователи"),
            KeyboardButton(text="🧾 Товары")
        )
        builder.row(
            KeyboardButton(text="🏷 Категории"),
            KeyboardButton(text="🏪 Склад")
        )
        builder.row(
            KeyboardButton(text="⚙ Настройки"),
            KeyboardButton(text="📝 Логи")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def manager_menu() -> ReplyKeyboardMarkup:
        """Manager menu keyboard"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📦 Новые заказы"),
            KeyboardButton(text="⏳ В работе")
        )
        builder.row(
            KeyboardButton(text="✔ Завершенные"),
            KeyboardButton(text="❌ Отмененные")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def courier_menu() -> ReplyKeyboardMarkup:
        """Courier menu keyboard"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="🚚 Мои доставки"),
            KeyboardButton(text="📍 Адреса")
        )
        builder.row(
            KeyboardButton(text="📞 Связь с клиентом"),
            KeyboardButton(text="✅ Доставлено")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def back_button() -> ReplyKeyboardMarkup:
        """Back button keyboard"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="🔙 Назад"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def cancel_button() -> ReplyKeyboardMarkup:
        """Cancel button keyboard"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="❌ Отмена"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def contact_keyboard() -> ReplyKeyboardMarkup:
        """Contact request keyboard"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📞 Поделиться контактом", request_contact=True))
        builder.add(KeyboardButton(text="❌ Отмена"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def location_keyboard() -> ReplyKeyboardMarkup:
        """Location request keyboard"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📍 Отправить локацию", request_location=True))
        builder.add(KeyboardButton(text="❌ Отмена"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def confirm_cancel_keyboard() -> InlineKeyboardMarkup:
        """Confirm/Cancel inline keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        )
        return builder.as_markup()
    
    @staticmethod
    def pagination_keyboard(
        current_page: int,
        total_pages: int,
        callback_prefix: str
    ) -> InlineKeyboardMarkup:
        """Pagination inline keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Previous button
        if current_page > 1:
            builder.add(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"{callback_prefix}_page_{current_page - 1}"
                )
            )
        
        # Page indicator
        builder.add(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="current_page"
            )
        )
        
        # Next button
        if current_page < total_pages:
            builder.add(
                InlineKeyboardButton(
                    text="➡️ Вперед",
                    callback_data=f"{callback_prefix}_page_{current_page + 1}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
        """Product actions inline keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"product_details_{product_id}")
        )
        return builder.as_markup()
    
    @staticmethod
    def order_actions_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
        """Order actions inline keyboard"""
        builder = InlineKeyboardBuilder()
        
        if status == "NEW":
            builder.row(
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order_{order_id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_id}")
            )
        elif status == "CONFIRMED":
            builder.row(
                InlineKeyboardButton(text="🚚 В доставку", callback_data=f"deliver_order_{order_id}")
            )
        elif status == "IN_DELIVERY":
            builder.row(
                InlineKeyboardButton(text="✅ Доставлено", callback_data=f"complete_order_{order_id}")
            )
        
        builder.row(
            InlineKeyboardButton(text="ℹ️ Детали заказа", callback_data=f"order_details_{order_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def user_management_keyboard(user_id: int, current_role: str) -> InlineKeyboardMarkup:
        """User management inline keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Role change buttons
        roles = ["CLIENT", "COURIER", "MANAGER", "ADMIN", "SUPER_ADMIN"]
        for role in roles:
            if role != current_role:
                builder.add(
                    InlineKeyboardButton(
                        text=f"👤 Сделать {role}",
                        callback_data=f"change_role_{user_id}_{role}"
                    )
                )
        
        # Block/Unblock button
        builder.add(
            InlineKeyboardButton(
                text="🚫 Заблокировать",
                callback_data=f"block_user_{user_id}"
            )
        )
        
        return builder.as_markup()
