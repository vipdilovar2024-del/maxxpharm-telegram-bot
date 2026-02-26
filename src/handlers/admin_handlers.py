from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.product_service import ProductService
from src.services.category_service import CategoryService
from src.services.order_service import OrderService
from src.keyboards.admin_keyboards import AdminKeyboards
from src.database import get_session


class AdminHandlers:
    """Handlers for admin users"""
    
    def __init__(self, router: Router):
        self.router = router
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all admin handlers"""
        # Main menu handlers
        self.router.message(F.text == "📊 Статистика", self.handle_statistics)
        self.router.message(F.text == "📦 Заказы", self.handle_orders)
        self.router.message(F.text == "👥 Пользователи", self.handle_users)
        self.router.message(F.text == "🧾 Товары", self.handle_products)
        self.router.message(F.text == "🏷 Категории", self.handle_categories)
        self.router.message(F.text == "🏪 Склад", self.handle_warehouse)
        self.router.message(F.text == "⚙ Настройки", self.handle_settings)
        self.router.message(F.text == "📝 Логи", self.handle_logs)
        
        # Users management handlers
        self.router.message(F.text == "👤 Добавить пользователя", self.handle_add_user)
        self.router.message(F.text == "📋 Список пользователей", self.handle_users_list)
        self.router.message(F.text == "🔐 Изменить роли", self.handle_change_roles)
        self.router.message(F.text == "🚫 Заблокировать", self.handle_block_user)
        self.router.message(F.text == "📈 Активность", self.handle_activity)
        
        # Products management handlers
        self.router.message(F.text == "➕ Добавить товар", self.handle_add_product)
        self.router.message(F.text == "📋 Список товаров", self.handle_products_list)
        self.router.message(F.text == "✏️ Редактировать товар", self.handle_edit_product)
        self.router.message(F.text == "🗑 Удалить товар", self.handle_delete_product)
        self.router.message(F.text == "📦 Управление остатками", self.handle_stock_management)
        
        # Categories management handlers
        self.router.message(F.text == "➕ Добавить категорию", self.handle_add_category)
        self.router.message(F.text == "📋 Список категорий", self.handle_categories_list)
        self.router.message(F.text == "✏️ Редактировать категорию", self.handle_edit_category)
        self.router.message(F.text == "🗑 Удалить категорию", self.handle_delete_category)
        
        # Orders management handlers
        self.router.message(F.text == "📋 Все заказы", self.handle_all_orders)
        self.router.message(F.text == "🆕 Новые заказы", self.handle_new_orders)
        self.router.message(F.text == "⏳ В обработке", self.handle_processing_orders)
        self.router.message(F.text == "🚚 В доставке", self.handle_delivery_orders)
        self.router.message(F.text == "✅ Завершенные", self.handle_completed_orders)
        self.router.message(F.text == "❌ Отмененные", self.handle_cancelled_orders)
        self.router.message(F.text == "📊 Статистика заказов", self.handle_order_statistics)
        
        # Warehouse management handlers
        self.router.message(F.text == "📦 Текущие остатки", self.handle_current_stock)
        self.router.message(F.text == "⚠️ Мало товара", self.handle_low_stock)
        self.router.message(F.text == "📥 Пополнение склада", self.handle_replenish_stock)
        self.router.message(F.text == "📊 История движений", self.handle_stock_history)
        self.router.message(F.text == "📈 Отчет по складу", self.handle_stock_report)
        
        # Statistics handlers
        self.router.message(F.text == "📊 Общая статистика", self.handle_general_stats)
        self.router.message(F.text == "💰 Финансовая статистика", self.handle_financial_stats)
        self.router.message(F.text == "👥 Статистика пользователей", self.handle_user_stats)
        self.router.message(F.text == "🛍 Статистика товаров", self.handle_product_stats)
    
    async def handle_statistics(self, message: types.Message):
        """Handle statistics menu"""
        text = (
            "📊 *Статистика*\n\n"
            "Выберите раздел статистики:\n"
            "• 📊 Общая статистика - общие показатели\n"
            "• 💰 Финансовая статистика - финансовые показатели\n"
            "• 👥 Статистика пользователей - активность пользователей\n"
            "• 🛍 Статистика товаров - популярные товары"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.statistics_menu(), parse_mode="Markdown")
    
    async def handle_orders(self, message: types.Message):
        """Handle orders menu"""
        text = (
            "📦 *Управление заказами*\n\n"
            "Выберите раздел:\n"
            "• 📋 Все заказы - все заказы системы\n"
            "• 🆕 Новые заказы - необработанные заказы\n"
            "• ⏳ В обработке - заказы в работе\n"
            "• 🚚 В доставке - заказы у курьеров\n"
            "• ✅ Завершенные - выполненные заказы\n"
            "• ❌ Отмененные - отмененные заказы\n"
            "• 📊 Статистика заказов - статистика по заказам"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
    async def handle_users(self, message: types.Message):
        """Handle users management menu"""
        text = (
            "👥 *Управление пользователями*\n\n"
            "Выберите действие:\n"
            "• 👤 Добавить пользователя - создать нового пользователя\n"
            "• 📋 Список пользователей - просмотр всех пользователей\n"
            "• 🔐 Изменить роли - изменить права доступа\n"
            "• 🚫 Заблокировать - заблокировать пользователя\n"
            "• 📈 Активность - статистика по пользователям"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.users_menu(), parse_mode="Markdown")
    
    async def handle_products(self, message: types.Message):
        """Handle products management menu"""
        text = (
            "🧾 *Управление товарами*\n\n"
            "Выберите действие:\n"
            "• ➕ Добавить товар - создать новый товар\n"
            "• 📋 Список товаров - просмотр всех товаров\n"
            "• ✏️ Редактировать товар - изменить информацию о товаре\n"
            "• 🗑 Удалить товар - удалить товар\n"
            "• 📦 Управление остатками - изменить количество товара"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.products_menu(), parse_mode="Markdown")
    
    async def handle_categories(self, message: types.Message):
        """Handle categories management menu"""
        text = (
            "🏷 *Управление категориями*\n\n"
            "Выберите действие:\n"
            "• ➕ Добавить категорию - создать новую категорию\n"
            "• 📋 Список категорий - просмотр всех категорий\n"
            "• ✏️ Редактировать категорию - изменить категорию\n"
            "• 🗑 Удалить категорию - удалить категорию"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.categories_menu(), parse_mode="Markdown")
    
    async def handle_warehouse(self, message: types.Message):
        """Handle warehouse management menu"""
        text = (
            "🏪 *Управление складом*\n\n"
            "Выберите действие:\n"
            "• 📦 Текущие остатки - просмотр остатков\n"
            "• ⚠️ Мало товара - товары с низким остатком\n"
            "• 📥 Пополнение склада - добавить товары на склад\n"
            "• 📊 История движений - история изменений\n"
            "• 📈 Отчет по складу - складской отчет"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.warehouse_menu(), parse_mode="Markdown")
    
    async def handle_settings(self, message: types.Message):
        """Handle settings menu"""
        text = (
            "⚙️ *Настройки системы*\n\n"
            "Раздел в разработке...\n\n"
            "Здесь будут доступны:\n"
            "• 🌐 Настройки бота\n"
            "• 💳 Настройки оплаты\n"
            "• 📧 Настройки уведомлений\n"
            "• 🔐 Настройки безопасности"
        )
        
        await message.answer(text, reply_markup=AdminKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_logs(self, message: types.Message):
        """Handle logs menu"""
        async for session in get_session():
            from src.services.log_service import LogService
            log_service = LogService(session)
            
            # Get recent logs
            recent_logs = await log_service.get_recent_logs(hours=24, limit=20)
            
            if not recent_logs:
                await message.answer("📝 За последние 24 часа действий не было")
                return
            
            text = "📝 *Последние действия (24ч):*\n\n"
            for log in recent_logs:
                user_info = f" от {log.user.full_name}" if log.user else " (система)"
                text += f"📅 {log.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                text += f"🔸 {log.action}{user_info}\n"
                if log.details:
                    text += f"📝 {log.details}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_add_user(self, message: types.Message):
        """Handle add user"""
        await message.answer(
            "👤 *Добавление пользователя*\n\n"
            "Для добавления пользователя:\n"
            "1. Попросите пользователя нажать /start в боте\n"
            "2. Найдите его в списке пользователей\n"
            "3. Измените его роль на нужную\n\n"
            "Или введите Telegram ID пользователя:",
            reply_markup=AdminKeyboards.users_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_users_list(self, message: types.Message):
        """Handle users list"""
        async for session in get_session():
            user_service = UserService(session)
            users = await user_service.get_all_users()
            
            if not users:
                await message.answer("📭 Пользователи暂时 отсутствуют")
                return
            
            text = "👥 *Список пользователей:*\n\n"
            for user in users[:20]:  # Show first 20 users
                status = "✅" if user.is_active else "🚫"
                text += f"{status} {user.full_name} (@{user.username or 'N/A'})\n"
                text += f"   📱 ID: {user.telegram_id}\n"
                text += f"   👤 Роль: {user.role}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.users_menu(), parse_mode="Markdown")
    
    async def handle_change_roles(self, message: types.Message):
        """Handle change roles"""
        await message.answer(
            "🔐 *Изменение ролей*\n\n"
            "Выберите пользователя из списка и измените его роль.\n\n"
            "Доступные роли:\n"
            "• 👤 CLIENT - Клиент\n"
            "• 🚚 COURIER - Курьер\n"
            "• 📦 MANAGER - Менеджер\n"
            "• 👑 ADMIN - Администратор\n"
            "• 🔥 SUPER_ADMIN - Супер-администратор",
            reply_markup=AdminKeyboards.users_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_block_user(self, message: types.Message):
        """Handle block user"""
        await message.answer(
            "🚫 *Блокировка пользователя*\n\n"
            "Выберите пользователя из списка для блокировки.\n\n"
            "⚠️ Заблокированный пользователь не сможет:\n"
            "• Создавать заказы\n"
            "• Просматривать товары\n"
            "• Использовать бота",
            reply_markup=AdminKeyboards.users_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_activity(self, message: types.Message):
        """Handle user activity"""
        async for session in get_session():
            from src.services.log_service import LogService
            log_service = LogService(session)
            
            # Get user activity summary
            activity = await log_service.get_user_activity_summary(days=7)
            
            if not activity:
                await message.answer("📈 За последние 7 дней активности не было")
                return
            
            text = "📈 *Активность пользователей (7 дней):*\n\n"
            for i, user_activity in enumerate(activity[:10], 1):
                text += f"{i}. {user_activity['full_name']} (@{user_activity['username'] or 'N/A'})\n"
                text += f"   📊 Действий: {user_activity['action_count']}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.users_menu(), parse_mode="Markdown")
    
    async def handle_add_product(self, message: types.Message):
        """Handle add product"""
        await message.answer(
            "➕ *Добавление товара*\n\n"
            "Для добавления товара введите:\n"
            "• Название товара\n"
            "• Цена\n"
            "• Категория\n"
            "• Количество на складе\n"
            "• Описание (опционально)\n\n"
            "Формат: Название | Цена | Категория | Количество | Описание",
            reply_markup=AdminKeyboards.products_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_products_list(self, message: types.Message):
        """Handle products list"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_all_products()
            
            if not products:
                await message.answer("📭 Товары暂时 отсутствуют")
                return
            
            text = "🧾 *Список товаров:*\n\n"
            for product in products[:20]:  # Show first 20 products
                status = "✅" if product.is_active else "🚫"
                stock_status = "✅" if product.stock_quantity > 10 else "⚠️" if product.stock_quantity > 0 else "❌"
                text += f"{status}{stock_status} {product.name}\n"
                text += f"   💰 Цена: {product.price} ₽\n"
                text += f"   📦 Остаток: {product.stock_quantity} шт.\n"
                text += f"   🏷️ Категория: {product.category.name if product.category else 'N/A'}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.products_menu(), parse_mode="Markdown")
    
    async def handle_edit_product(self, message: types.Message):
        """Handle edit product"""
        await message.answer(
            "✏️ *Редактирование товара*\n\n"
            "Выберите товар из списка для редактирования.\n\n"
            "Можно изменить:\n"
            "• Название\n"
            "• Цена\n"
            "• Описание\n"
            "• Количество на складе",
            reply_markup=AdminKeyboards.products_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_delete_product(self, message: types.Message):
        """Handle delete product"""
        await message.answer(
            "🗑 *Удаление товара*\n\n"
            "⚠️ Внимание! Удаление товара необратимо.\n\n"
            "Выберите товар из списка для удаления.",
            reply_markup=AdminKeyboards.products_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_stock_management(self, message: types.Message):
        """Handle stock management"""
        await message.answer(
            "📦 *Управление остатками*\n\n"
            "Выберите товар и укажите новое количество.\n\n"
            "Формат: Название товара | Новое количество",
            reply_markup=AdminKeyboards.products_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_add_category(self, message: types.Message):
        """Handle add category"""
        await message.answer(
            "➕ *Добавление категории*\n\n"
            "Введите название категории:\n\n"
            "Формат: Название | Описание",
            reply_markup=AdminKeyboards.categories_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_categories_list(self, message: types.Message):
        """Handle categories list"""
        async for session in get_session():
            category_service = CategoryService(session)
            categories = await category_service.get_all_categories()
            
            if not categories:
                await message.answer("📭 Категории暂时 отсутствуют")
                return
            
            text = "🏷️ *Список категорий:*\n\n"
            for category in categories:
                status = "✅" if category.is_active else "🚫"
                text += f"{status} {category.name}\n"
                if category.description:
                    text += f"   📝 {category.description}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.categories_menu(), parse_mode="Markdown")
    
    async def handle_edit_category(self, message: types.Message):
        """Handle edit category"""
        await message.answer(
            "✏️ *Редактирование категории*\n\n"
            "Выберите категорию из списка для редактирования.",
            reply_markup=AdminKeyboards.categories_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_delete_category(self, message: types.Message):
        """Handle delete category"""
        await message.answer(
            "🗑 *Удаление категории*\n\n"
            "⚠️ Внимание! При удалении категории все товары в ней будут скрыты.\n\n"
            "Выберите категорию из списка для удаления.",
            reply_markup=AdminKeyboards.categories_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_all_orders(self, message: types.Message):
        """Handle all orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_all_orders()
            
            if not orders:
                await message.answer("📭 Заказы暂时 отсутствуют")
                return
            
            text = "📋 *Все заказы:*\n\n"
            for order in orders[:20]:  # Show first 20 orders
                status_emoji = {
                    "NEW": "🆕",
                    "CONFIRMED": "✅",
                    "IN_PROGRESS": "⏳",
                    "IN_DELIVERY": "🚚",
                    "COMPLETED": "✔️",
                    "CANCELLED": "❌"
                }
                
                emoji = status_emoji.get(order.status.value, "❓")
                text += f"{emoji} Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
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
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
    async def handle_processing_orders(self, message: types.Message):
        """Handle processing orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_PROGRESS")
            
            if not orders:
                await message.answer("📭 Заказов в обработке暂时 нет")
                return
            
            text = "⏳ *Заказы в обработке:*\n\n"
            for order in orders:
                text += f"⏳ Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
    async def handle_delivery_orders(self, message: types.Message):
        """Handle delivery orders"""
        async for session in get_session():
            order_service = OrderService(session)
            orders = await order_service.get_orders_by_status("IN_DELIVERY")
            
            if not orders:
                await message.answer("📭 Заказов в доставке暂时 нет")
                return
            
            text = "🚚 *Заказы в доставке:*\n\n"
            for order in orders:
                text += f"🚚 Заказ #{order.id}\n"
                text += f"   👤 Клиент: {order.user.full_name}\n"
                text += f"   💰 Сумма: {order.total_amount} ₽\n"
                text += f"   📍 Адрес: {order.delivery_address or 'N/A'}\n"
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
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
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
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
                text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
    async def handle_order_statistics(self, message: types.Message):
        """Handle order statistics"""
        async for session in get_session():
            order_service = OrderService(session)
            stats = await order_service.get_order_statistics()
            
            text = "📊 *Статистика заказов:*\n\n"
            total_orders = sum(stats.values())
            text += f"📦 Всего заказов: {total_orders}\n\n"
            
            status_emoji = {
                "NEW": "🆕",
                "CONFIRMED": "✅",
                "IN_PROGRESS": "⏳",
                "IN_DELIVERY": "🚚",
                "COMPLETED": "✔️",
                "CANCELLED": "❌"
            }
            
            for status, count in stats.items():
                emoji = status_emoji.get(status, "❓")
                text += f"{emoji} {status}: {count}\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.orders_menu(), parse_mode="Markdown")
    
    async def handle_current_stock(self, message: types.Message):
        """Handle current stock"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_all_products()
            
            if not products:
                await message.answer("📭 Товары暂时 отсутствуют")
                return
            
            total_stock = sum(p.stock_quantity for p in products)
            low_stock_products = [p for p in products if p.stock_quantity <= 10]
            out_of_stock = [p for p in products if p.stock_quantity == 0]
            
            text = "📦 *Текущие остатки на складе:*\n\n"
            text += f"📊 Всего товаров: {len(products)}\n"
            text += f"📦 Общий остаток: {total_stock} шт.\n"
            text += f"⚠️ Мало товара: {len(low_stock_products)}\n"
            text += f"❌ Нет в наличии: {len(out_of_stock)}\n\n"
            
            text += "📦 *Товары с низким остатком:*\n"
            for product in low_stock_products[:10]:
                text += f"• {product.name}: {product.stock_quantity} шт.\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.warehouse_menu(), parse_mode="Markdown")
    
    async def handle_low_stock(self, message: types.Message):
        """Handle low stock products"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_low_stock_products(threshold=10)
            
            if not products:
                await message.answer("✅ Все товары в наличии")
                return
            
            text = "⚠️ *Товары с низким остатком:*\n\n"
            for product in products:
                status = "❌" if product.stock_quantity == 0 else "⚠️"
                text += f"{status} {product.name}\n"
                text += f"   📦 Остаток: {product.stock_quantity} шт.\n"
                text += f"   💰 Цена: {product.price} ₽\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.warehouse_menu(), parse_mode="Markdown")
    
    async def handle_replenish_stock(self, message: types.Message):
        """Handle stock replenishment"""
        await message.answer(
            "📥 *Пополнение склада*\n\n"
            "Введите данные для пополнения:\n\n"
            "Формат: Название товара | Количество для добавления",
            reply_markup=AdminKeyboards.warehouse_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_stock_history(self, message: types.Message):
        """Handle stock history"""
        await message.answer(
            "📊 *История движений склада*\n\n"
            "Раздел в разработке...\n\n"
            "Здесь будет доступна история:\n"
            "• Поступления товаров\n"
            "• Списания товаров\n"
            "• Изменения остатков",
            reply_markup=AdminKeyboards.warehouse_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_stock_report(self, message: types.Message):
        """Handle stock report"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_all_products()
            
            if not products:
                await message.answer("📭 Товары暂时 отсутствуют")
                return
            
            total_value = sum(p.price * p.stock_quantity for p in products)
            total_stock = sum(p.stock_quantity for p in products)
            
            text = "📈 *Отчет по складу:*\n\n"
            text += f"📊 Всего товаров: {len(products)}\n"
            text += f"📦 Общий остаток: {total_stock} шт.\n"
            text += f"💰 Общая стоимость: {total_value:,.2f} ₽\n"
            text += f"💸 Средняя цена за единицу: {total_value/total_stock if total_stock > 0 else 0:,.2f} ₽\n\n"
            
            # Top 10 most valuable products
            text += "💰 *Топ-10 товаров по стоимости:*\n"
            sorted_products = sorted(products, key=lambda p: p.price * p.stock_quantity, reverse=True)[:10]
            
            for i, product in enumerate(sorted_products, 1):
                value = product.price * product.stock_quantity
                text += f"{i}. {product.name}: {value:,.2f} ₽\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.warehouse_menu(), parse_mode="Markdown")
    
    async def handle_general_stats(self, message: types.Message):
        """Handle general statistics"""
        async for session in get_session():
            from src.services.user_service import UserService
            from src.services.product_service import ProductService
            from src.services.order_service import OrderService
            
            user_service = UserService(session)
            product_service = ProductService(session)
            order_service = OrderService(session)
            
            users = await user_service.get_all_users()
            products = await product_service.get_all_products()
            orders = await order_service.get_all_orders()
            
            text = "📊 *Общая статистика:*\n\n"
            text += f"👥 Всего пользователей: {len(users)}\n"
            text += f"🧾 Всего товаров: {len(products)}\n"
            text += f"📦 Всего заказов: {len(orders)}\n\n"
            
            # Users by role
            role_stats = {}
            for user in users:
                role_stats[user.role] = role_stats.get(user.role, 0) + 1
            
            text += "👥 *Пользователи по ролям:*\n"
            for role, count in role_stats.items():
                text += f"• {role}: {count}\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.statistics_menu(), parse_mode="Markdown")
    
    async def handle_financial_stats(self, message: types.Message):
        """Handle financial statistics"""
        async for session in get_session():
            from src.services.order_service import OrderService
            
            order_service = OrderService(session)
            orders = await order_service.get_all_orders()
            
            if not orders:
                await message.answer("📭 Заказов暂时 нет")
                return
            
            completed_orders = [o for o in orders if o.status.value == "COMPLETED"]
            total_revenue = sum(o.total_amount for o in completed_orders)
            avg_order_value = total_revenue / len(completed_orders) if completed_orders else 0
            
            text = "💰 *Финансовая статистика:*\n\n"
            text += f"💰 Общая выручка: {total_revenue:,.2f} ₽\n"
            text += f"📦 Выполненных заказов: {len(completed_orders)}\n"
            text += f"💸 Средний чек: {avg_order_value:,.2f} ₽\n"
            text += f"📊 Конверсия: {len(completed_orders)/len(orders)*100:.1f}%\n\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.statistics_menu(), parse_mode="Markdown")
    
    async def handle_user_stats(self, message: types.Message):
        """Handle user statistics"""
        async for session in get_session():
            from src.services.user_service import UserService
            from src.services.order_service import OrderService
            
            user_service = UserService(session)
            order_service = OrderService(session)
            
            users = await user_service.get_all_users()
            
            text = "👥 *Статистика пользователей:*\n\n"
            text += f"👥 Всего пользователей: {len(users)}\n\n"
            
            # Active users (with orders)
            active_users = 0
            for user in users:
                user_orders = await order_service.get_user_orders(user.id)
                if user_orders:
                    active_users += 1
            
            text += f"✅ Активных пользователей: {active_users}\n"
            text += f"📊 Активность: {active_users/len(users)*100:.1f}%\n\n"
            
            # Users by role
            role_stats = {}
            for user in users:
                role_stats[user.role] = role_stats.get(user.role, 0) + 1
            
            text += "👤 *Распределение по ролям:*\n"
            for role, count in role_stats.items():
                percentage = count / len(users) * 100
                text += f"• {role}: {count} ({percentage:.1f}%)\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.statistics_menu(), parse_mode="Markdown")
    
    async def handle_product_stats(self, message: types.Message):
        """Handle product statistics"""
        async for session in get_session():
            from src.services.product_service import ProductService
            from src.services.order_service import OrderService
            
            product_service = ProductService(session)
            order_service = OrderService(session)
            
            products = await product_service.get_all_products()
            orders = await order_service.get_all_orders()
            
            text = "🛍️ *Статистика товаров:*\n\n"
            text += f"🧾 Всего товаров: {len(products)}\n"
            
            in_stock = len([p for p in products if p.stock_quantity > 0])
            out_of_stock = len([p for p in products if p.stock_quantity == 0])
            low_stock = len([p for p in products if 0 < p.stock_quantity <= 10])
            
            text += f"✅ В наличии: {in_stock}\n"
            text += f"❌ Нет в наличии: {out_of_stock}\n"
            text += f"⚠️ Мало товара: {low_stock}\n\n"
            
            # Most expensive products
            expensive_products = sorted(products, key=lambda p: p.price, reverse=True)[:5]
            text += "💰 *Самые дорогие товары:*\n"
            for product in expensive_products:
                text += f"• {product.name}: {product.price} ₽\n"
            
            await message.answer(text, reply_markup=AdminKeyboards.statistics_menu(), parse_mode="Markdown")
