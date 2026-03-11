#!/usr/bin/env python3
"""
🏥 MAXXPHARM CRM - Setup Script
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def setup_database():
    """Инициализация базы данных"""
    print("🗄️ Initializing database...")
    
    try:
        from database import init_db
        await init_db()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def create_admin():
    """Создание администратора"""
    print("👑 Creating admin user...")
    
    try:
        from services.user_service import UserService
        from models.database import UserRole
        from database import get_db
        
        async for session in get_db():
            user_service = UserService(session)
            
            # Проверяем, существует ли администратор
            admin_id = 697780123
            existing_admin = await user_service.get_user_by_telegram_id(admin_id)
            
            if not existing_admin:
                # Создаем администратора
                admin = await user_service.create_user(
                    telegram_id=admin_id,
                    full_name="Administrator",
                    username="admin",
                    role=UserRole.ADMIN
                )
                print(f"✅ Admin user created: {admin.full_name}")
            else:
                print(f"✅ Admin user already exists: {existing_admin.full_name}")
            
            break
            
        return True
    except Exception as e:
        print(f"❌ Admin creation failed: {e}")
        return False

async def test_bot():
    """Тестирование бота"""
    print("🤖 Testing bot connection...")
    
    try:
        from config import settings
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        bot_info = await bot.get_me()
        
        print(f"✅ Bot connected successfully!")
        print(f"🤖 Bot name: @{bot_info.username}")
        print(f"📝 Bot ID: {bot_info.id}")
        
        return True
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        return False

async def main():
    """Основная функция установки"""
    print("🏥 MAXXPHARM CRM - Setup Script")
    print("=" * 50)
    
    # Шаг 1: Инициализация базы данных
    if not await setup_database():
        print("❌ Setup failed at database initialization")
        return False
    
    # Шаг 2: Создание администратора
    if not await create_admin():
        print("❌ Setup failed at admin creation")
        return False
    
    # Шаг 3: Тестирование бота
    if not await test_bot():
        print("❌ Setup failed at bot testing")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 MAXXPHARM CRM setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. 🚀 Start the bot: python run_crm.py")
    print("2. 📱 Test the bot in Telegram: @solimfarm_bot")
    print("3. 🌐 Deploy to Render or your server")
    print("4. 📊 Configure additional settings")
    print("\n🏥 MAXXPHARM CRM - Ready to serve pharmacies!")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
