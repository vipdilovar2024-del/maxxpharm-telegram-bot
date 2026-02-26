from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class AdminKeyboards:
    """Keyboards for admin users"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Admin main menu"""
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
    def users_menu() -> ReplyKeyboardMarkup:
        """Users management menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="👤 Добавить пользователя"),
            KeyboardButton(text="📋 Список пользователей")
        )
        builder.row(
            KeyboardButton(text="🔐 Изменить роли"),
            KeyboardButton(text="🚫 Заблокировать")
        )
        builder.row(
            KeyboardButton(text="📈 Активность"),
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def products_menu() -> ReplyKeyboardMarkup:
        """Products management menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="➕ Добавить товар"),
            KeyboardButton(text="📋 Список товаров")
        )
        builder.row(
            KeyboardButton(text="✏️ Редактировать товар"),
            KeyboardButton(text="🗑 Удалить товар")
        )
        builder.row(
            KeyboardButton(text="📦 Управление остатками"),
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def categories_menu() -> ReplyKeyboardMarkup:
        """Categories management menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="➕ Добавить категорию"),
            KeyboardButton(text="📋 Список категорий")
        )
        builder.row(
            KeyboardButton(text="✏️ Редактировать категорию"),
            KeyboardButton(text="🗑 Удалить категорию")
        )
        builder.row(
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def orders_menu() -> ReplyKeyboardMarkup:
        """Orders management menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📋 Все заказы"),
            KeyboardButton(text="🆕 Новые заказы")
        )
        builder.row(
            KeyboardButton(text="⏳ В обработке"),
            KeyboardButton(text="🚚 В доставке")
        )
        builder.row(
            KeyboardButton(text="✅ Завершенные"),
            KeyboardButton(text="❌ Отмененные")
        )
        builder.row(
            KeyboardButton(text="📊 Статистика заказов"),
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def warehouse_menu() -> ReplyKeyboardMarkup:
        """Warehouse management menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📦 Текущие остатки"),
            KeyboardButton(text="⚠️ Мало товара")
        )
        builder.row(
            KeyboardButton(text="📥 Пополнение склада"),
            KeyboardButton(text="📊 История движений")
        )
        builder.row(
            KeyboardButton(text="📈 Отчет по складу"),
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def statistics_menu() -> ReplyKeyboardMarkup:
        """Statistics menu"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="📊 Общая статистика"),
            KeyboardButton(text="💰 Финансовая статистика")
        )
        builder.row(
            KeyboardButton(text="👥 Статистика пользователей"),
            KeyboardButton(text="🛍 Статистика товаров")
        )
        builder.row(
            KeyboardButton(text="📦 Статистика заказов"),
            KeyboardButton(text="🔙 Назад")
        )
        
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def user_management_keyboard(user_id: int, current_role: str, is_active: bool) -> InlineKeyboardMarkup:
        """User management actions keyboard"""
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
        if is_active:
            builder.add(
                InlineKeyboardButton(
                    text="🚫 Заблокировать",
                    callback_data=f"block_user_{user_id}"
                )
            )
        else:
            builder.add(
                InlineKeyboardButton(
                    text="✅ Разблокировать",
                    callback_data=f"unblock_user_{user_id}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def product_management_keyboard(product_id: int) -> InlineKeyboardMarkup:
        """Product management actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_product_{product_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_product_{product_id}")
        )
        builder.row(
            InlineKeyboardButton(text="📦 Изменить остатки", callback_data=f"edit_stock_{product_id}")
        )
        builder.row(
            InlineKeyboardButton(text="ℹ️ Детали", callback_data=f"product_details_{product_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def order_management_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
        """Order management actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        # Status change buttons based on current status
        if status == "NEW":
            builder.row(
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order_{order_id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_id}")
            )
        elif status == "CONFIRMED":
            builder.row(
                InlineKeyboardButton(text="⏳ В обработку", callback_data=f"process_order_{order_id}")
            )
        elif status == "IN_PROGRESS":
            builder.row(
                InlineKeyboardButton(text="🚚 В доставку", callback_data=f"deliver_order_{order_id}")
            )
        elif status == "IN_DELIVERY":
            builder.row(
                InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_order_{order_id}")
            )
        
        builder.row(
            InlineKeyboardButton(text="ℹ️ Детали заказа", callback_data=f"order_details_{order_id}")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Связь с клиентом", callback_data=f"contact_client_{order_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def category_management_keyboard(category_id: int) -> InlineKeyboardMarkup:
        """Category management actions keyboard"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_category_{category_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_category_{category_id}")
        )
        builder.row(
            InlineKeyboardButton(text="📋 Товары категории", callback_data=f"category_products_{category_id}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def users_list_keyboard(users: list, page: int = 1) -> InlineKeyboardMarkup:
        """Users list keyboard"""
        builder = InlineKeyboardBuilder()
        
        for user in users:
            status = "✅" if user['is_active'] else "🚫"
            builder.add(
                InlineKeyboardButton(
                    text=f"{status} {user['full_name']} ({user['role']})",
                    callback_data=f"user_details_{user['id']}"
                )
            )
        
        # Pagination
        builder.row(
            InlineKeyboardButton(text="⬅️", callback_data=f"users_page_{page - 1}"),
            InlineKeyboardButton(text=f"{page}", callback_data="current_page"),
            InlineKeyboardButton(text="➡️", callback_data=f"users_page_{page + 1}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def products_list_keyboard(products: list, page: int = 1) -> InlineKeyboardMarkup:
        """Products list keyboard"""
        builder = InlineKeyboardBuilder()
        
        for product in products:
            status = "✅" if product['is_active'] else "🚫"
            stock_status = "✅" if product['stock_quantity'] > 10 else "⚠️" if product['stock_quantity'] > 0 else "❌"
            builder.add(
                InlineKeyboardButton(
                    text=f"{status}{stock_status} {product['name']} - {product['price']} ₽",
                    callback_data=f"product_details_{product['id']}"
                )
            )
        
        # Pagination
        builder.row(
            InlineKeyboardButton(text="⬅️", callback_data=f"products_page_{page - 1}"),
            InlineKeyboardButton(text=f"{page}", callback_data="current_page"),
            InlineKeyboardButton(text="➡️", callback_data=f"products_page_{page + 1}")
        )
        
        return builder.as_markup()
