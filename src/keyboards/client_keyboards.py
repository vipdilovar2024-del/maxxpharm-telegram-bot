from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class ClientKeyboards:
    """Keyboards for client users"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Client main menu"""
        builder = ReplyKeyboardBuilder()
        
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
    def catalog_menu() -> ReplyKeyboardMarkup:
        """Catalog menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="🏷 Категории"),
            KeyboardButton(text="🔍 Поиск по названию")
        )
        builder.row(
            KeyboardButton(text="🔥 Популярные"),
            KeyboardButton(text="💊 Новинки")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def cart_menu() -> ReplyKeyboardMarkup:
        """Cart menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="➕ Добавить товар"),
            KeyboardButton(text="➖ Убрать товар")
        )
        builder.row(
            KeyboardButton(text="💳 Оформить заказ"),
            KeyboardButton(text="🗑 Очистить корзину")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def order_menu() -> ReplyKeyboardMarkup:
        """Order menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📋 История заказов"),
            KeyboardButton(text="🔄 Повторить заказ")
        )
        builder.row(
            KeyboardButton(text="📍 Отследить заказ"),
            KeyboardButton(text="💬 Связь с менеджером")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def support_menu() -> ReplyKeyboardMarkup:
        """Support menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="💬 Написать менеджеру"),
            KeyboardButton(text="📞 Позвонить")
        )
        builder.row(
            KeyboardButton(text="❓ Частые вопросы"),
            KeyboardButton(text="📧 Email поддержка")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def checkout_menu() -> ReplyKeyboardMarkup:
        """Checkout menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📞 Указать телефон"),
            KeyboardButton(text="📍 Указать адрес")
        )
        builder.row(
            KeyboardButton(text="💬 Комментарий"),
            KeyboardButton(text="✅ Подтвердить заказ")
        )
        builder.row(
            KeyboardButton(text="❌ Отмена")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def product_quantity_keyboard(product_id: int, current_quantity: int = 1) -> InlineKeyboardMarkup:
        """Product quantity selection keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Quantity buttons
        if current_quantity > 1:
            builder.add(
                InlineKeyboardButton(text="➖", callback_data=f"qty_minus_{product_id}")
            )
        
        builder.add(
            InlineKeyboardButton(text=str(current_quantity), callback_data="qty_current")
        )
        
        builder.add(
            InlineKeyboardButton(text="➕", callback_data=f"qty_plus_{product_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_qty_cart_{product_id}_{current_quantity}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def cart_item_keyboard(product_id: int, order_item_id: int) -> InlineKeyboardMarkup:
        """Cart item actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="➕ Увеличить", callback_data=f"cart_plus_{order_item_id}"),
            InlineKeyboardButton(text="➖ Уменьшить", callback_data=f"cart_minus_{order_item_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"cart_remove_{order_item_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def order_tracking_keyboard(order_id: int) -> InlineKeyboardMarkup:
        """Order tracking keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📋 Детали заказа", callback_data=f"order_details_{order_id}")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Связь с курьером", callback_data=f"contact_courier_{order_id}")
        )
        builder.row(
            InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
        """Categories selection keyboard"""
        builder = InlineKeyboardBuilder()
        
        for category in categories:
            builder.add(
                InlineKeyboardButton(
                    text=category['name'],
                    callback_data=f"category_{category['id']}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def products_keyboard(products: list, page: int = 1) -> InlineKeyboardMarkup:
        """Products list keyboard"""
        builder = InlineKeyboardBuilder()
        
        for product in products:
            builder.add(
                InlineKeyboardButton(
                    text=f"{product['name']} - {product['price']} ₽",
                    callback_data=f"product_{product['id']}"
                )
            )
        
        # Pagination
        builder.row(
            InlineKeyboardButton(text="⬅️", callback_data=f"products_page_{page - 1}"),
            InlineKeyboardButton(text=f"{page}", callback_data="current_page"),
            InlineKeyboardButton(text="➡️", callback_data=f"products_page_{page + 1}")
        )
        
        return builder.as_markup()
