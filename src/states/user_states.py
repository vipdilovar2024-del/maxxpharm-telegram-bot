from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """User management states"""
    
    # Registration states
    registration_phone = State()
    registration_address = State()
    
    # Profile states
    viewing_profile = State()
    editing_profile = State()
    
    # User management (admin)
    adding_user = State()
    editing_user_role = State()
    blocking_user = State()
    
    # Search states
    searching_users = State()
    
    # Support states
    contacting_support = State()
    writing_message = State()
