"""
🔌 PostgreSQL Connection - Подключение к базе данных для MAXXPHARM CRM
Простое подключение для aiogram + PostgreSQL + Render
"""

import asyncpg
import os
from typing import Optional

# 🔌 Настройки подключения к базе данных
# Для локальной разработки
LOCAL_DATABASE_URL = "postgresql://postgres:password@localhost/pharma_crm"

# Для Render (из environment variables)
RENDER_DATABASE_URL = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)

# Для вашей текущей базы данных
CURRENT_DATABASE_URL = "postgresql+asyncpg://solimfarm_db_steg_user:B4a9T78li3OZlOfVu3f6bF9iBfLWJfu9@dpg-d6ane6cr85hc73ep4qd0-a.oregon-postgres.render.com/solimfarm_db_steg"

# Глобальная переменная для пула соединений
pool = None

async def create_database_pool():
    """Создание пула соединений с базой данных"""
    global pool
    
    try:
        # Используем вашу текущую базу данных
        pool = await asyncpg.create_pool(
            CURRENT_DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ Database pool created successfully")
        return pool
    except Exception as e:
        print(f"❌ Failed to create database pool: {e}")
        raise

async def get_connection():
    """Получение соединения с базой данных"""
    global pool
    
    if pool is None:
        pool = await create_database_pool()
    
    return pool.acquire()

async def close_database_pool():
    """Закрытие пула соединений"""
    global pool
    
    if pool:
        await pool.close()
        pool = None
        print("🔒 Database pool closed")

# 🚀 Примеры использования в боте

async def create_order_example(client_id: int, comment: str, total_price: float, zone: str, address: str):
    """Пример создания заказа"""
    conn = await get_connection()
    
    try:
        # Создаем заказ
        order = await conn.fetchrow("""
            INSERT INTO orders(client_id, status, comment, total_price, zone, address)
            VALUES ($1, 'created', $2, $3, $4, $5)
            RETURNING id, created_at
        """, client_id, comment, total_price, zone, address)
        
        print(f"✅ Order created: #{order['id']}")
        return order
        
    finally:
        await conn.release()

async def get_user_by_telegram_id(telegram_id: int):
    """Пример получения пользователя по Telegram ID"""
    conn = await get_connection()
    
    try:
        user = await conn.fetchrow("""
            SELECT id, name, role, zone, is_online, active_orders
            FROM users
            WHERE telegram_id = $1
        """, telegram_id)
        
        return dict(user) if user else None
        
    finally:
        await conn.release()

async def get_orders_by_status(status: str, limit: int = 10):
    """Пример получения заказов по статусу"""
    conn = await get_connection()
    
    try:
        orders = await conn.fetch("""
            SELECT o.id, o.total_price, o.zone, o.created_at,
                   c.name as client_name, c.phone as client_phone
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            WHERE o.status = $1
            ORDER BY o.created_at DESC
            LIMIT $2
        """, status, limit)
        
        return [dict(order) for order in orders]
        
    finally:
        await conn.release()

async def update_order_status(order_id: int, new_status: str, changed_by: int):
    """Пример обновления статуса заказа"""
    conn = await get_connection()
    
    try:
        async with conn.transaction():
            # Получаем старый статус
            old_status = await conn.fetchval("SELECT status FROM orders WHERE id = $1", order_id)
            
            # Обновляем статус
            await conn.execute("""
                UPDATE orders 
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            """, new_status, order_id)
            
            # Записываем в историю
            await conn.execute("""
                INSERT INTO order_status_history(order_id, old_status, new_status, changed_by)
                VALUES ($1, $2, $3, $4)
            """, order_id, old_status, new_status, changed_by)
            
            print(f"✅ Order #{order_id} status updated: {old_status} → {new_status}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to update order status: {e}")
        return False
    finally:
        await conn.release()

async def get_optimal_worker(role: str, zone: str = None):
    """Пример получения оптимального сотрудника (Uber-алгоритм)"""
    conn = await get_connection()
    
    try:
        worker = await conn.fetchrow("""
            SELECT * FROM get_optimal_worker($1, $2)
        """, role, zone)
        
        return dict(worker) if worker else None
        
    finally:
        await conn.release()

async def update_worker_load(user_id: int, delta: int):
    """Пример обновления нагрузки сотрудника"""
    conn = await get_connection()
    
    try:
        success = await conn.fetchval("SELECT update_worker_load($1, $2)", user_id, delta)
        return success
        
    finally:
        await conn.release()

# 📊 Примеры аналитических запросов

async def get_daily_statistics():
    """Пример получения дневной статистики"""
    conn = await get_connection()
    
    try:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(*) FILTER (WHERE status = 'delivered') as delivered_orders,
                COUNT(*) FILTER (WHERE status IN ('rejected', 'cancelled')) as cancelled_orders,
                COALESCE(SUM(total_price), 0) as total_revenue,
                AVG(total_price) as avg_order_value
            FROM orders
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        return dict(stats)
        
    finally:
        await conn.release()

async def get_worker_performance(user_id: int):
    """Пример получения производительности сотрудника"""
    conn = await get_connection()
    
    try:
        performance = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(*) FILTER (WHERE o.status = 'delivered') as delivered_orders,
                AVG(EXTRACT(EPOCH FROM (o.completed_at - o.created_at)) / 60) as avg_completion_time_minutes,
                (COUNT(*) FILTER (WHERE o.status = 'delivered')::NUMERIC / NULLIF(COUNT(*), 0)) * 100 as success_rate
            FROM orders o
            WHERE o.operator_id = $1 OR o.picker_id = $1 OR o.checker_id = $1 OR o.courier_id = $1
        """, user_id)
        
        return dict(performance)
        
    finally:
        await conn.release()

# 🧪 Тестовые функции

async def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        conn = await get_connection()
        
        # Тестовый запрос
        result = await conn.fetchval("SELECT NOW()")
        
        print(f"✅ Database connection test successful: {result}")
        await conn.release()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

async def setup_database():
    """Настройка базы данных при запуске бота"""
    try:
        # Создаем пул соединений
        await create_database_pool()
        
        # Тестируем подключение
        if await test_database_connection():
            print("🚀 Database ready for bot!")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

# 📋 Удобные функции для использования в handlers

async def quick_create_order(telegram_id: int, comment: str, items: list, zone: str, address: str):
    """Быстрое создание заказа с товарами"""
    conn = await get_connection()
    
    try:
        async with conn.transaction():
            # Находим или создаем клиента
            client = await conn.fetchrow("""
                SELECT id FROM clients WHERE telegram_id = $1
            """, telegram_id)
            
            if not client:
                client = await conn.fetchrow("""
                    INSERT INTO clients(telegram_id, name, zone, address)
                    VALUES ($1, 'Client', $2, $3)
                    RETURNING id
                """, telegram_id, zone, address)
            
            client_id = client['id']
            
            # Рассчитываем общую сумму
            total_price = sum(item['price'] * item['quantity'] for item in items)
            
            # Создаем заказ
            order = await conn.fetchrow("""
                INSERT INTO orders(client_id, status, comment, total_price, zone, address)
                VALUES ($1, 'created', $2, $3, $4, $5)
                RETURNING id
            """, client_id, comment, total_price, zone, address)
            
            order_id = order['id']
            
            # Добавляем товары
            for item in items:
                await conn.execute("""
                    INSERT INTO order_items(order_id, product_name, quantity, price, total_price)
                    VALUES ($1, $2, $3, $4, $5)
                """, order_id, item['product_name'], item['quantity'], item['price'], item['price'] * item['quantity'])
            
            print(f"✅ Order #{order_id} created with {len(items)} items")
            return order_id
            
    finally:
        await conn.release()

# 🎯 Основная функция для инициализации
async def initialize_database():
    """Инициализация базы данных для бота"""
    print("🗄️ Initializing MAXXPHARM CRM Database...")
    
    success = await setup_database()
    
    if success:
        print("✅ Database initialization completed!")
        print("🚀 Bot is ready to work with database!")
    else:
        print("❌ Database initialization failed!")
    
    return success

if __name__ == "__main__":
    import asyncio
    
    # Тест подключения
    asyncio.run(test_database_connection())
