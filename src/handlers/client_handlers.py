from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.product_service import ProductService
from src.services.order_service import OrderService
from src.keyboards.client_keyboards import ClientKeyboards
from src.states.order_states import OrderStates
from src.states.product_states import ProductStates
from src.database import get_session


class ClientHandlers:
    """Handlers for client users"""
    
    def __init__(self, router: Router):
        self.router = router
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all client handlers"""
        # Main menu handlers
        self.router.message(F.text == "🛍 Каталог", self.handle_catalog)
        self.router.message(F.text == "🔍 Поиск", self.handle_search)
        self.router.message(F.text == "🛒 Корзина", self.handle_cart)
        self.router.message(F.text == "📦 Мои заказы", self.handle_orders)
        self.router.message(F.text == "📞 Поддержка", self.handle_support)
        self.router.message(F.text == "ℹ️ О нас", self.handle_about)
        
        # Catalog handlers
        self.router.message(F.text == "🏷 Категории", self.handle_categories)
        self.router.message(F.text == "🔍 Поиск по названию", self.handle_search_products)
        self.router.message(F.text == "🔥 Популярные", self.handle_popular_products)
        self.router.message(F.text == "💊 Новинки", self.handle_new_products)
        
        # Cart handlers
        self.router.message(F.text == "💳 Оформить заказ", self.handle_checkout)
        self.router.message(F.text == "🗑 Очистить корзину", self.handle_clear_cart)
        
        # Order handlers
        self.router.message(F.text == "📋 История заказов", self.handle_order_history)
        self.router.message(F.text == "🔄 Повторить заказ", self.handle_repeat_order)
        self.router.message(F.text == "📍 Отследить заказ", self.handle_track_order)
        
        # Support handlers
        self.router.message(F.text == "💬 Написать менеджеру", self.handle_contact_manager)
        self.router.message(F.text == "📞 Позвонить", self.handle_call_support)
        
        # Callback handlers
        self.router.callback_query(F.data.startswith("category_"), self.handle_category_callback)
        self.router.callback_query(F.data.startswith("product_"), self.handle_product_callback)
        self.router.callback_query(F.data.startswith("add_to_cart_"), self.handle_add_to_cart)
        self.router.callback_query(F.data.startswith("qty_"), self.handle_quantity_callback)
    
    async def handle_catalog(self, message: types.Message):
        """Handle catalog menu"""
        text = (
            "🛍️ *Каталог товаров*\n\n"
            "Выберите действие:\n"
            "• 🏷 Категории - просмотр по категориям\n"
            "• 🔍 Поиск - поиск по названию\n"
            "• 🔥 Популярные - самые популярные товары\n"
            "• 💊 Новинки - последние поступления"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.catalog_menu(), parse_mode="Markdown")
    
    async def handle_categories(self, message: types.Message, state: FSMContext):
        """Handle categories view"""
        async for session in get_session():
            product_service = ProductService(session)
            categories = await product_service.get_all_categories()
            
            if not categories:
                await message.answer("📭 Категории暂时 отсутствуют")
                return
            
            text = "🏷️ *Категории товаров:*\n\n"
            for category in categories:
                text += f"• {category.name}\n"
                if category.description:
                    text += f"  {category.description}\n"
                text += "\n"
            
            await message.answer(text, reply_markup=ClientKeyboards.categories_keyboard(categories), parse_mode="Markdown")
    
    async def handle_search(self, message: types.Message, state: FSMContext):
        """Handle search menu"""
        await state.set_state(ProductStates.searching_products)
        await message.answer(
            "🔍 *Поиск товаров*\n\n"
            "Введите название товара для поиска:",
            reply_markup=ClientKeyboards.back_button(),
            parse_mode="Markdown"
        )
    
    async def handle_search_products(self, message: types.Message, state: FSMContext):
        """Handle product search"""
        await state.set_state(ProductStates.searching_products)
        await message.answer(
            "🔍 *Поиск по названию*\n\n"
            "Введите название товара:",
            reply_markup=ClientKeyboards.back_button(),
            parse_mode="Markdown"
        )
    
    async def handle_popular_products(self, message: types.Message):
        """Handle popular products"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_all_products()  # In real app, would filter by popularity
            
            if not products:
                await message.answer("📭 Популярные товары暂时 отсутствуют")
                return
            
            text = "🔥 *Популярные товары:*\n\n"
            for product in products[:10]:  # Show top 10
                text += f"• {product.name} - {product.price} ₽\n"
                if product.stock_quantity > 0:
                    text += f"  ✅ В наличии: {product.stock_quantity} шт.\n"
                else:
                    text += f"  ❌ Нет в наличии\n"
                text += "\n"
            
            await message.answer(text, reply_markup=ClientKeyboards.products_keyboard(products), parse_mode="Markdown")
    
    async def handle_new_products(self, message: types.Message):
        """Handle new products"""
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_all_products()  # In real app, would filter by date
            
            if not products:
                await message.answer("📭 Новинки暂时 отсутствуют")
                return
            
            text = "💊 *Новые поступления:*\n\n"
            for product in products[:10]:  # Show latest 10
                text += f"• {product.name} - {product.price} ₽\n"
                if product.stock_quantity > 0:
                    text += f"  ✅ В наличии: {product.stock_quantity} шт.\n"
                else:
                    text += f"  ❌ Нет в наличии\n"
                text += "\n"
            
            await message.answer(text, reply_markup=ClientKeyboards.products_keyboard(products), parse_mode="Markdown")
    
    async def handle_cart(self, message: types.Message):
        """Handle cart view"""
        # In real implementation, would show cart items
        text = (
            "🛒 *Ваша корзина*\n\n"
            "📭 Корзина пуста\n\n"
            "Добавьте товары из каталога!"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.cart_menu(), parse_mode="Markdown")
    
    async def handle_orders(self, message: types.Message):
        """Handle orders menu"""
        text = (
            "📦 *Мои заказы*\n\n"
            "Выберите действие:\n"
            "• 📋 История заказов - все ваши заказы\n"
            "• 🔄 Повторить заказ - повторить предыдущий заказ\n"
            "• 📍 Отследить заказ - отследить текущий заказ"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.order_menu(), parse_mode="Markdown")
    
    async def handle_support(self, message: types.Message):
        """Handle support menu"""
        text = (
            "📞 *Поддержка*\n\n"
            "Выберите способ связи:\n"
            "• 💬 Написать менеджеру - чат с поддержкой\n"
            "• 📞 Позвонить - звонок в поддержку\n"
            "• ❓ Частые вопросы - ответы на популярные вопросы\n"
            "• 📧 Email поддержка - отправить письмо"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.support_menu(), parse_mode="Markdown")
    
    async def handle_about(self, message: types.Message):
        """Handle about info"""
        text = (
            "ℹ️ *О Maxxpharm*\n\n"
            "🏥 *Maxxpharm* - современная система заказа и доставки лекарств\n\n"
            "🎯 *Наша миссия:*\n"
            "• Быстрая доставка лекарств\n"
            "• Качественный сервис\n"
            "• Доступные цены\n"
            "• Профессиональная поддержка\n\n"
            "📱 *Наши преимущества:*\n"
            "• 🔍 Поиск лекарств по названию\n"
            "• 📦 Отслеживание заказа в реальном времени\n"
            "• 💳 Удобная оплата\n"
            "• 🚚 Быстрая доставка\n\n"
            "📞 *Контакты:*\n"
            "• Телефон: +998 71 200 00 00\n"
            "• Email: support@maxxpharm.uz\n"
            "• Telegram: @maxxpharm_support\n\n"
            "⏰ *Время работы:*\n"
            "• Пн-Пт: 9:00 - 18:00\n"
            "• Сб-Вс: 10:00 - 16:00"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.main_menu(), parse_mode="Markdown")
    
    async def handle_checkout(self, message: types.Message, state: FSMContext):
        """Handle checkout process"""
        await state.set_state(OrderStates.checkout_phone)
        await message.answer(
            "📞 *Оформление заказа*\n\n"
            "Шаг 1: Укажите ваш номер телефона\n"
            "Нажмите кнопку ниже или введите вручную:",
            reply_markup=ClientKeyboards.contact_keyboard(),
            parse_mode="Markdown"
        )
    
    async def handle_clear_cart(self, message: types.Message):
        """Handle cart clearing"""
        await message.answer(
            "🗑 *Корзина очищена*\n\n"
            "Все товары удалены из корзины",
            reply_markup=ClientKeyboards.cart_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_order_history(self, message: types.Message):
        """Handle order history"""
        async for session in get_session():
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if user:
                order_service = OrderService(session)
                orders = await order_service.get_user_orders(user.id)
                
                if not orders:
                    await message.answer("📭 У вас пока нет заказов")
                    return
                
                text = "📋 *История заказов:*\n\n"
                for order in orders[:10]:  # Show last 10 orders
                    text += f"📦 Заказ #{order.id}\n"
                    text += f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    text += f"💰 Сумма: {order.total_amount} ₽\n"
                    text += f"📊 Статус: {order.status.value}\n\n"
                
                await message.answer(text, reply_markup=ClientKeyboards.order_menu(), parse_mode="Markdown")
    
    async def handle_repeat_order(self, message: types.Message):
        """Handle order repeat"""
        await message.answer(
            "🔄 *Повтор заказа*\n\n"
            "Выберите заказ для повторения из истории заказов",
            reply_markup=ClientKeyboards.order_menu(),
            parse_mode="Markdown"
        )
    
    async def handle_track_order(self, message: types.Message, state: FSMContext):
        """Handle order tracking"""
        await state.set_state(OrderStates.tracking_order)
        await message.answer(
            "📍 *Отслеживание заказа*\n\n"
            "Введите номер заказа:",
            reply_markup=ClientKeyboards.back_button(),
            parse_mode="Markdown"
        )
    
    async def handle_contact_manager(self, message: types.Message, state: FSMContext):
        """Handle contact with manager"""
        await state.set_state(UserStates.writing_message)
        await message.answer(
            "💬 *Связь с менеджером*\n\n"
            "Напишите ваше сообщение:",
            reply_markup=ClientKeyboards.back_button(),
            parse_mode="Markdown"
        )
    
    async def handle_call_support(self, message: types.Message):
        """Handle call support"""
        text = (
            "📞 *Связь с поддержкой*\n\n"
            "📱 Телефон: +998 71 200 00 00\n"
            "⏰ Время работы: Пн-Пт 9:00-18:00, Сб-Вс 10:00-16:00\n\n"
            "🚀 Также можете написать нам в Telegram: @maxxpharm_support"
        )
        
        await message.answer(text, reply_markup=ClientKeyboards.support_menu(), parse_mode="Markdown")
    
    async def handle_category_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle category selection callback"""
        category_id = callback.data.split("_")[1]
        
        async for session in get_session():
            product_service = ProductService(session)
            products = await product_service.get_products_by_category(int(category_id))
            
            if not products:
                await callback.message.answer("📭 В этой категории暂时 нет товаров")
                return
            
            text = f"🏷️ *Товары категории:*\n\n"
            for product in products:
                text += f"• {product.name} - {product.price} ₽\n"
                if product.stock_quantity > 0:
                    text += f"  ✅ В наличии: {product.stock_quantity} шт.\n"
                else:
                    text += f"  ❌ Нет в наличии\n"
                text += "\n"
            
            await callback.message.answer(text, reply_markup=ClientKeyboards.products_keyboard(products), parse_mode="Markdown")
        
        await callback.answer()
    
    async def handle_product_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle product selection callback"""
        product_id = callback.data.split("_")[1]
        
        async for session in get_session():
            product_service = ProductService(session)
            product = await product_service.get_product_by_id(int(product_id))
            
            if not product:
                await callback.message.answer("📭 Товар не найден")
                return
            
            text = (
                f"🛍️ *{product.name}*\n\n"
                f"💰 Цена: {product.price} ₽\n"
                f"📦 В наличии: {product.stock_quantity} шт.\n"
            )
            
            if product.description:
                text += f"📝 Описание: {product.description}\n\n"
            
            if product.stock_quantity > 0:
                text += "✅ Товар доступен для заказа"
            else:
                text += "❌ Товар временно отсутствует"
            
            await callback.message.answer(
                text,
                reply_markup=ClientKeyboards.product_actions_keyboard(product.id),
                parse_mode="Markdown"
            )
        
        await callback.answer()
    
    async def handle_add_to_cart(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle add to cart callback"""
        product_id = callback.data.split("_")[3]
        
        await state.set_state(ProductStates.selecting_quantity)
        await state.update_data(product_id=int(product_id), quantity=1)
        
        await callback.message.answer(
            "🛒 *Выберите количество:*\n\n"
            "Текущее количество: 1",
            reply_markup=ClientKeyboards.product_quantity_keyboard(int(product_id), 1),
            parse_mode="Markdown"
        )
        
        await callback.answer()
    
    async def handle_quantity_callback(self, callback: types.CallbackQuery, state: FSMContext):
        """Handle quantity selection callback"""
        data = callback.data.split("_")
        action = data[1]
        product_id = int(data[2])
        
        current_data = await state.get_data()
        current_quantity = current_data.get("quantity", 1)
        
        if action == "plus":
            new_quantity = current_quantity + 1
        elif action == "minus":
            new_quantity = max(1, current_quantity - 1)
        else:
            new_quantity = current_quantity
        
        await state.update_data(quantity=new_quantity)
        
        await callback.message.edit_text(
            f"🛒 *Выберите количество:*\n\n"
            f"Текущее количество: {new_quantity}",
            reply_markup=ClientKeyboards.product_quantity_keyboard(product_id, new_quantity),
            parse_mode="Markdown"
        )
        
        await callback.answer()
