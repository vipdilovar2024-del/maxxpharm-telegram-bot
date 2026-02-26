from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class CourierKeyboards:
    """Keyboards for courier users"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Courier main menu"""
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
