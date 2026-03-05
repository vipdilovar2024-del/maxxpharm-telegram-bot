"""
📋 Database Setup Instructions - Инструкции по установке базы данных
MAXXPHARM Telegram CRM - PostgreSQL Setup Guide
"""

# 📋 ИНСТРУКЦИИ ПО УСТАНОВКЕ БАЗЫ ДАННЫХ
# ===========================================
# MAXXPHARM Telegram CRM - PostgreSQL Setup Guide

"""
🗄️ MAXXPHARM CRM DATABASE SETUP GUIDE
=====================================

📋 СОДЕРЖАНИЕ:
1. 🚀 Быстрый старт (Render)
2. 💻 Локальная установка
3. 🔌 Подключение к боту
4. 🧪 Тестирование
5. 📊 Проверка данных

---

## 🚀 1️⃣ БЫСТРЫЙ СТАРТ (RENDER)

Если вы используете Render.com, база данных уже готова!

### ✅ Что уже сделано:
- База данных создана на Render
- Все таблицы созданы
- Индексы оптимизированы
- Данные готовы к использованию

### 🔌 Просто подключитесь:
```python
# В вашем боте используйте:
from database_connection import get_connection, create_order_example

# Получение соединения
conn = await get_connection()

# Создание заказа
order = await create_order_example(
    client_id=1,
    comment="Срочно нужны лекарства",
    total_price=150.50,
    zone="центр",
    address="ул. Рудаки 45"
)
```

---

## 💻 2️⃣ ЛОКАЛЬНАЯ УСТАНОВКА

### 📋 Требования:
- PostgreSQL 12+
- Python 3.8+
- aiogram

### 🗄️ Шаг 1: Установка PostgreSQL

#### Windows:
```bash
# Скачайте и установите PostgreSQL с официального сайта
# https://www.postgresql.org/download/windows/

# Или используйте Chocolatey:
choco install postgresql
```

#### macOS:
```bash
# Используйте Homebrew:
brew install postgresql
brew services start postgresql
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 🗄️ Шаг 2: Создание базы данных

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Создайте базу данных
CREATE DATABASE pharma_crm;

# Создайте пользователя (опционально)
CREATE USER pharma_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pharma_crm TO pharma_user;

# Выйдите из psql
\q
```

### 🗄️ Шаг 3: Выполнение SQL файла

```bash
# Способ 1: Через psql
psql -U postgres -d pharma_crm -f crm_database.sql

# Способ 2: Через файл (если пароль требуется)
PGPASSWORD=your_password psql -U postgres -d pharma_crm -f crm_database.sql

# Способ 3: Через интерактивную сессию
psql -U postgres -d pharma_crm
\i crm_database.sql
```

### ✅ Проверка установки:

```bash
# Подключитесь к базе
psql -U postgres -d pharma_crm

# Проверьте таблицы
\dt

# Проверьте данные
SELECT * FROM users LIMIT 5;
SELECT * FROM settings;
```

---

## 🔌 3️⃣ ПОДКЛЮЧЕНИЕ К БОТУ

### 📋 Шаг 1: Установка зависимостей

```bash
pip install asyncpg aiogram
```

### 📋 Шаг 2: Настройка подключения

#### Для локальной базы:
```python
# config.py
DATABASE_URL = "postgresql://postgres:password@localhost/pharma_crm"
```

#### Для Render:
```python
# config.py
DATABASE_URL = os.getenv("DATABASE_URL")  # Render автоматически установит
```

#### Для вашей текущей базы:
```python
# config.py
DATABASE_URL = "postgresql+asyncpg://solimfarm_db_steg_user:B4a9T78li3OZlOfVu3f6bF9iBfLWJfu9@dpg-d6ane6cr85hc73ep4qd0-a.oregon-postgres.render.com/solimfarm_db_steg"
```

### 📋 Шаг 3: Использование в боте

```python
# main.py
import asyncio
from aiogram import Bot, Dispatcher
from database_connection import initialize_database

async def main():
    # Инициализация базы данных
    await initialize_database()
    
    # Создание бота
    bot = Bot(token="YOUR_BOT_TOKEN")
    dp = Dispatcher()
    
    # Настройка handlers...
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 4️⃣ ТЕСТИРОВАНИЕ

### 📋 Тест подключения:

```python
# test_db.py
import asyncio
from database_connection import test_database_connection

async def main():
    success = await test_database_connection()
    if success:
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 📋 Тест создания заказа:

```python
# test_order.py
import asyncio
from database_connection import quick_create_order

async def main():
    # Тестовые данные
    items = [
        {"product_name": "Парацетамол", "quantity": 2, "price": 25.00},
        {"product_name": "Витамин C", "quantity": 1, "price": 45.00}
    ]
    
    order_id = await quick_create_order(
        telegram_id=697780123,
        comment="Тестовый заказ",
        items=items,
        zone="центр",
        address="ул. Рудаки 45"
    )
    
    print(f"✅ Test order created: #{order_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 5️⃣ ПРОВЕРКА ДАННЫХ

### 🗄️ SQL запросы для проверки:

```sql
-- Проверка пользователей
SELECT * FROM users ORDER BY created_at DESC;

-- Проверка клиентов
SELECT * FROM clients ORDER BY created_at DESC;

-- Проверка заказов
SELECT o.id, o.status, o.total_price, c.name as client_name
FROM orders o
LEFT JOIN clients c ON o.client_id = c.id
ORDER BY o.created_at DESC;

-- Проверка товаров в заказах
SELECT oi.product_name, oi.quantity, oi.price, o.id as order_id
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
ORDER BY o.created_at DESC;

-- Проверка истории статусов
SELECT osh.order_id, osh.old_status, osh.new_status, osh.created_at
FROM order_status_history osh
ORDER BY osh.created_at DESC;

-- Проверка настроек
SELECT * FROM settings ORDER BY key;
```

### 📊 Python функции для проверки:

```python
# check_data.py
import asyncio
from database_connection import get_connection

async def check_all_data():
    conn = await get_connection()
    
    try:
        # Проверка пользователей
        users = await conn.fetch("SELECT COUNT(*) as count FROM users")
        print(f"👥 Users: {users[0]['count']}")
        
        # Проверка клиентов
        clients = await conn.fetch("SELECT COUNT(*) as count FROM clients")
        print(f"👤 Clients: {clients[0]['count']}")
        
        # Проверка заказов
        orders = await conn.fetch("SELECT COUNT(*) as count FROM orders")
        print(f"📦 Orders: {orders[0]['count']}")
        
        # Проверка товаров
        items = await conn.fetch("SELECT COUNT(*) as count FROM order_items")
        print(f"💊 Order items: {items[0]['count']}")
        
        # Проверка статусов заказов
        status_counts = await conn.fetch("""
            SELECT status, COUNT(*) as count 
            FROM orders 
            GROUP BY status 
            ORDER BY count DESC
        """)
        
        print("\n📊 Order statuses:")
        for status in status_counts:
            print(f"  {status['status']}: {status['count']}")
        
    finally:
        await conn.release()

if __name__ == "__main__":
    asyncio.run(check_all_data())
```

---

## 🔧 6️⃣ УСТРАНЕНИЕ ПРОБЛЕМ

### ❌ Ошибка: "Connection refused"
```bash
# Решение:
# 1. Проверьте, что PostgreSQL запущен
sudo systemctl status postgresql

# 2. Проверьте порт
netstat -an | grep 5432

# 3. Проверьте хост и порт в строке подключения
```

### ❌ Ошибка: "FATAL: database does not exist"
```bash
# Решение:
# 1. Создайте базу данных
createdb pharma_crm

# 2. Проверьте имя базы данных
psql -l
```

### ❌ Ошибка: "FATAL: password authentication failed"
```bash
# Решение:
# 1. Установите пароль для пользователя
ALTER USER postgres PASSWORD 'your_password';

# 2. Используйте правильный пароль в строке подключения
```

### ❌ Ошибка: "relation does not exist"
```bash
# Решение:
# 1. Выполните SQL файл заново
psql -U postgres -d pharma_crm -f crm_database.sql

# 2. Проверьте таблицы
\dt
```

---

## 🚀 7️⃣ ЗАПУСК БОТА

### 📋 Полный пример бота с базой данных:

```python
# bot_with_db.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from database_connection import initialize_database, quick_create_order

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация базы данных
    await initialize_database()
    
    # Создание бота
    bot = Bot(token="YOUR_BOT_TOKEN")
    dp = Dispatcher()
    
    @dp.message(F.text.startswith("/order"))
    async def handle_order(message: Message):
        try:
            # Пример создания заказа
            items = [
                {"product_name": "Парацетамол", "quantity": 1, "price": 25.00}
            ]
            
            order_id = await quick_create_order(
                telegram_id=message.from_user.id,
                comment=message.text.replace("/order", "").strip(),
                items=items,
                zone="центр",
                address="ул. Рудаки 45"
            )
            
            await message.answer(f"✅ Заказ создан: #{order_id}")
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            await message.answer("❌ Ошибка создания заказа")
    
    @dp.message(F.text.startswith("/status"))
    async def handle_status(message: Message):
        try:
            conn = await get_connection()
            
            orders = await conn.fetch("""
                SELECT o.id, o.status, o.total_price, o.created_at
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                WHERE c.telegram_id = $1
                ORDER BY o.created_at DESC
                LIMIT 5
            """, message.from_user.id)
            
            if orders:
                text = "📦 Ваши заказы:\n\n"
                for order in orders:
                    text += f"#{order['id']} - {order['status']} - {order['total_price']} сомони\n"
                
                await message.answer(text)
            else:
                await message.answer("📭 У вас нет заказов")
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            await message.answer("❌ Ошибка получения заказов")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ✅ 8️⃣ ГОТОВО К ИСПОЛЬЗОВАНИЮ

### 🎯 Что теперь доступно:
- ✅ Полная база данных для CRM
- ✅ Все таблицы созданы и оптимизированы
- ✅ Индексы для высокой производительности
- ✅ Триггеры для автоматического обновления
- ✅ Функции для бизнес-логики
- ✅ Python код для подключения
- ✅ Примеры использования в боте

### 🚀 Следующие шаги:
1. Подключите базу данных к вашему боту
2. Используйте готовые функции для CRUD операций
3. Добавьте обработчики для заказов
4. Настройте уведомления
5. Тестируйте и развивайте систему

---

## 📞 ПОДДЕРЖКА

Если возникнут проблемы:
1. Проверьте логи ошибок
2. Убедитесь, что PostgreSQL запущен
3. Проверьте строку подключения
4. Выполните SQL файл заново

---

## 🎉 УСПЕХ!

**✅ База данных MAXXPHARM CRM готова!**
**🚀 Бот может работать с PostgreSQL!**
**📊 Все функции оптимизированы!**
**🔥 Высокая производительность!**

**Теперь у вас полноценная CRM система!** 🏥💊
"""

def print_setup_guide():
    """Вывод полной инструкции по установке"""
    print(setup_guide)

if __name__ == "__main__":
    print_setup_guide()
