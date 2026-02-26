from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Order management states"""
    
    # Cart states
    viewing_cart = State()
    adding_to_cart = State()
    removing_from_cart = State()
    
    # Checkout states
    checkout_phone = State()
    checkout_address = State()
    checkout_comment = State()
    checkout_confirm = State()
    
    # Order management states
    viewing_orders = State()
    viewing_order_details = State()
    
    # Order tracking
    tracking_order = State()
    
    # Order actions
    cancelling_order = State()
    repeating_order = State()
    
    # Search states
    searching_orders = State()
    filtering_orders = State()
