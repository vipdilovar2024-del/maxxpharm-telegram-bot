from aiogram.fsm.state import State, StatesGroup


class ProductStates(StatesGroup):
    """Product management states"""
    
    # Catalog states
    browsing_catalog = State()
    viewing_category = State()
    viewing_product = State()
    
    # Search states
    searching_products = State()
    filtering_products = State()
    
    # Product management (admin)
    adding_product = State()
    editing_product_name = State()
    editing_product_price = State()
    editing_product_description = State()
    editing_product_stock = State()
    deleting_product = State()
    
    # Category management (admin)
    adding_category = State()
    editing_category = State()
    deleting_category = State()
    
    # Cart states
    selecting_quantity = State()
    adding_to_cart = State()
