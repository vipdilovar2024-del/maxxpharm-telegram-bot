from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class ManagerKeyboards:
    """Keyboards for manager users"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Manager main menu"""
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
