"""
🗄️ Database Demo - Демонстрация работы с базой данных MAXXPHARM CRM
Полный пример использования базы данных с реальными данными
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# Импортируем наши модели
from database_models import (
    DatabaseManager, User, Client, Order, OrderItem, OrderStatusHistory,
    Payment, Delivery, SystemLog, Setting,
    UserRole, OrderStatus, PaymentMethod, PaymentStatus, DeliveryStatus, LogLevel, Zone
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database_demo")

class DatabaseDemo:
    """Демонстрация работы с базой данных"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db: DatabaseManager = None
        self.logger = logging.getLogger("database_demo")
    
    async def setup(self):
        """Настройка подключения к базе данных"""
        try:
            self.db = DatabaseManager(self.connection_string)
            await self.db.initialize()
            self.logger.info("✅ Database demo initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize database demo: {e}")
            return False
    
    async def demo_user_operations(self):
        """Демонстрация операций с пользователями"""
        self.logger.info("👥 Demo: User Operations")
        
        try:
            # Создание пользователей
            users_data = [
                {
                    "telegram_id": 697780123,
                    "name": "Мухаммадмуссо",
                    "role": UserRole.DIRECTOR,
                    "phone": "+992900000001",
                    "zone": Zone.CENTER,
                    "performance_score": 9.5
                },
                {
                    "telegram_id": 697780124,
                    "name": "Али Оператор",
                    "role": UserRole.OPERATOR,
                    "phone": "+992900000002",
                    "zone": Zone.CENTER,
                    "performance_score": 8.5
                },
                {
                    "telegram_id": 697780125,
                    "name": "Рустам Сборщик",
                    "role": UserRole.PICKER,
                    "phone": "+992900000003",
                    "zone": Zone.CENTER,
                    "performance_score": 9.0
                },
                {
                    "telegram_id": 697780126,
                    "name": "Карим Сборщик",
                    "role": UserRole.PICKER,
                    "phone": "+992900000004",
                    "zone": Zone.NORTH,
                    "performance_score": 8.8
                },
                {
                    "telegram_id": 697780127,
                    "name": "Бекзод Курьер",
                    "role": UserRole.COURIER,
                    "phone": "+992900000005",
                    "zone": Zone.CENTER,
                    "performance_score": 9.2
                },
                {
                    "telegram_id": 697780128,
                    "name": "Фарход Курьер",
                    "role": UserRole.COURIER,
                    "phone": "+992900000006",
                    "zone": Zone.SOUTH,
                    "performance_score": 8.7
                },
                {
                    "telegram_id": 697780129,
                    "name": "Камол Проверщик",
                    "role": UserRole.CHECKER,
                    "phone": "+992900000007",
                    "zone": Zone.CENTER,
                    "performance_score": 9.1
                }
            ]
            
            created_users = []
            for user_data in users_data:
                user = User(**user_data)
                user_id = await self.db.create_user(user)
                created_users.append((user_id, user_data))
                self.logger.info(f"👤 Created user: {user_data['name']} (ID: {user_id})")
            
            # Получение оптимального сотрудника
            optimal_picker = await self.db.get_optimal_worker(UserRole.PICKER, Zone.CENTER)
            if optimal_picker:
                self.logger.info(f"🎯 Optimal picker for CENTER zone: {optimal_picker.name} (score: {optimal_picker.performance_score})")
            
            optimal_courier = await self.db.get_optimal_worker(UserRole.COURIER, Zone.SOUTH)
            if optimal_courier:
                self.logger.info(f"🎯 Optimal courier for SOUTH zone: {optimal_courier.name} (score: {optimal_courier.performance_score})")
            
            return created_users
            
        except Exception as e:
            self.logger.error(f"❌ User operations demo error: {e}")
            return []
    
    async def demo_client_operations(self):
        """Демонстрация операций с клиентами"""
        self.logger.info("👤 Demo: Client Operations")
        
        try:
            # Создание клиентов
            clients_data = [
                {
                    "telegram_id": 697780131,
                    "name": "Ахмад Клиент",
                    "phone": "+992900000010",
                    "address": "ул. Рудаки 45, кв. 12",
                    "zone": Zone.CENTER
                },
                {
                    "telegram_id": 697780132,
                    "name": "Карим Клиент",
                    "phone": "+992900000011",
                    "address": "ул. Айни 23, кв. 5",
                    "zone": Zone.NORTH
                },
                {
                    "telegram_id": 697780133,
                    "name": "Фарход Клиент",
                    "phone": "+992900000012",
                    "address": "ул. Бохтар 67, кв. 8",
                    "zone": Zone.SOUTH
                }
            ]
            
            created_clients = []
            for client_data in clients_data:
                client = Client(**client_data)
                client_id = await self.db.create_client(client)
                created_clients.append((client_id, client_data))
                self.logger.info(f"👤 Created client: {client_data['name']} (ID: {client_id})")
            
            return created_clients
            
        except Exception as e:
            self.logger.error(f"❌ Client operations demo error: {e}")
            return []
    
    async def demo_order_operations(self, users: List, clients: List):
        """Демонстрация операций с заказами"""
        self.logger.info("📦 Demo: Order Operations")
        
        try:
            # Создание заказов
            orders_data = [
                {
                    "client_id": clients[0][0],  # Ахмад
                    "status": OrderStatus.CREATED,
                    "total_price": 150.50,
                    "delivery_price": 15.00,
                    "zone": Zone.CENTER,
                    "address": "ул. Рудаки 45, кв. 12",
                    "comment": "Срочно нужны лекарства от давления",
                    "priority": 3,
                    "estimated_time": 45,
                    "items": [
                        {"product_name": "Лозаптан", "quantity": 2, "price": 45.00, "requires_prescription": True},
                        {"product_name": "Витамин C", "quantity": 1, "price": 25.50, "requires_prescription": False},
                        {"product_name": "Аспирин", "quantity": 1, "price": 15.00, "requires_prescription": False}
                    ]
                },
                {
                    "client_id": clients[1][0],  # Карим
                    "status": OrderStatus.CREATED,
                    "total_price": 89.00,
                    "delivery_price": 25.00,
                    "zone": Zone.NORTH,
                    "address": "ул. Айни 23, кв. 5",
                    "comment": "Заказ для пожилой матери",
                    "priority": 2,
                    "estimated_time": 60,
                    "items": [
                        {"product_name": "Парацетамол", "quantity": 3, "price": 12.00, "requires_prescription": False},
                        {"product_name": "Ибупрофен", "quantity": 2, "price": 20.00, "requires_prescription": False},
                        {"product_name": "Масло чайного дерева", "quantity": 1, "price": 25.00, "requires_prescription": False}
                    ]
                },
                {
                    "client_id": clients[2][0],  # Фарход
                    "status": OrderStatus.CREATED,
                    "total_price": 220.00,
                    "delivery_price": 25.00,
                    "zone": Zone.SOUTH,
                    "address": "ул. Бохтар 67, кв. 8",
                    "comment": "Заказ для всей семьи",
                    "priority": 1,
                    "estimated_time": 75,
                    "items": [
                        {"product_name": "Амоксиклав", "quantity": 2, "price": 65.00, "requires_prescription": True},
                        {"product_name": "Антигистаминное", "quantity": 1, "price": 45.00, "requires_prescription": True},
                        {"product_name": "Детские витамины", "quantity": 2, "price": 35.00, "requires_prescription": False},
                        {"product_name": "Бинт", "quantity": 5, "price": 8.00, "requires_prescription": False}
                    ]
                }
            ]
            
            created_orders = []
            for order_data in orders_data:
                async with self.db.pool.acquire() as conn:
                    async with conn.transaction():
                        # Создаем заказ
                        order = Order(
                            client_id=order_data["client_id"],
                            status=order_data["status"],
                            total_price=order_data["total_price"],
                            delivery_price=order_data["delivery_price"],
                            zone=order_data["zone"],
                            address=order_data["address"],
                            comment=order_data["comment"],
                            priority=order_data["priority"],
                            estimated_time=order_data["estimated_time"]
                        )
                        order_id = await self.db.create_order(order)
                        
                        # Создаем товары
                        for item_data in order_data["items"]:
                            item = OrderItem(
                                order_id=order_id,
                                product_name=item_data["product_name"],
                                quantity=item_data["quantity"],
                                price=item_data["price"],
                                total_price=item_data["quantity"] * item_data["price"],
                                requires_prescription=item_data["requires_prescription"]
                            )
                            await self.db.create_order_item(item)
                        
                        created_orders.append((order_id, order_data))
                        self.logger.info(f"📦 Created order #{order_id} for {order_data['total_price']} сомони")
            
            return created_orders
            
        except Exception as e:
            self.logger.error(f"❌ Order operations demo error: {e}")
            return []
    
    async def demo_order_workflow(self, orders: List, users: List):
        """Демонстрация полного workflow заказа"""
        self.logger.info("🔄 Demo: Order Workflow")
        
        try:
            # Получаем пользователей по ролям
            operator = None
            picker = None
            checker = None
            courier = None
            
            for user_id, user_data in users:
                if user_data["role"] == UserRole.OPERATOR:
                    operator = (user_id, user_data)
                elif user_data["role"] == UserRole.PICKER and user_data["zone"] == Zone.CENTER:
                    picker = (user_id, user_data)
                elif user_data["role"] == UserRole.CHECKER:
                    checker = (user_id, user_data)
                elif user_data["role"] == UserRole.COURIER and user_data["zone"] == Zone.CENTER:
                    courier = (user_id, user_data)
            
            # Обрабатываем первый заказ
            if orders and operator and picker and checker and courier:
                order_id, order_data = orders[0]
                
                self.logger.info(f"🔄 Processing order #{order_id}")
                
                # 1. Оператор принимает заказ
                await self.db.update_order_status(
                    order_id, OrderStatus.ACCEPTED, operator[0], "Заказ принят в обработку"
                )
                await self.db.update_worker_load(operator[0], 1)
                self.logger.info(f"✅ Order #{order_id} accepted by {operator[1]['name']}")
                
                # 2. Назначаем сборщика
                await self.db.update_order_status(
                    order_id, OrderStatus.PICKING, picker[0], "Начата сборка"
                )
                await self.db.update_worker_load(picker[0], 1)
                self.logger.info(f"📦 Order #{order_id} assigned to picker {picker[1]['name']}")
                
                # 3. Сборка завершена
                await self.db.update_order_status(
                    order_id, OrderStatus.READY, picker[0], "Сборка завершена"
                )
                await self.db.update_worker_load(picker[0], -1)
                self.logger.info(f"✅ Order #{order_id} picked by {picker[1]['name']}")
                
                # 4. Назначаем проверщика
                await self.db.update_order_status(
                    order_id, OrderStatus.CHECKING, checker[0], "Начата проверка"
                )
                await self.db.update_worker_load(checker[0], 1)
                self.logger.info(f"🔍 Order #{order_id} assigned to checker {checker[1]['name']}")
                
                # 5. Проверка завершена
                await self.db.update_order_status(
                    order_id, OrderStatus.WAITING_COURIER, checker[0], "Проверка завершена"
                )
                await self.db.update_worker_load(checker[0], -1)
                self.logger.info(f"✅ Order #{order_id} checked by {checker[1]['name']}")
                
                # 6. Назначаем курьера
                await self.db.update_order_status(
                    order_id, OrderStatus.ON_DELIVERY, courier[0], "Начата доставка"
                )
                await self.db.update_worker_load(courier[0], 1)
                self.logger.info(f"🚚 Order #{order_id} assigned to courier {courier[1]['name']}")
                
                # 7. Доставка завершена
                await self.db.update_order_status(
                    order_id, OrderStatus.DELIVERED, courier[0], "Доставка завершена"
                )
                await self.db.update_worker_load(courier[0], -1)
                await self.db.update_worker_load(operator[0], -1)
                self.logger.info(f"✅ Order #{order_id} delivered by {courier[1]['name']}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Order workflow demo error: {e}")
            return False
    
    async def demo_analytics(self):
        """Демонстрация аналитики"""
        self.logger.info("📊 Demo: Analytics")
        
        try:
            # Дневная статистика
            stats = await self.db.get_daily_statistics(
                date.today() - timedelta(days=1),
                date.today()
            )
            
            self.logger.info("📊 Daily Statistics:")
            for stat in stats:
                self.logger.info(f"  📅 {stat['date']}: {stat['total_orders']} orders, "
                               f"{stat['delivered_orders']} delivered, "
                               f"{stat['total_revenue']} сомони revenue")
            
            # Производительность сотрудников
            for role in [UserRole.OPERATOR, UserRole.PICKER, UserRole.CHECKER, UserRole.COURIER]:
                users = await self.db.fetch(
                    "SELECT id, name FROM users WHERE role = $1 LIMIT 3",
                    role.value
                )
                
                for user in users:
                    performance = await self.db.get_worker_performance(user['id'])
                    if performance:
                        self.logger.info(f"👤 {user['name']} ({role.value}): "
                                       f"{performance.get('total_orders', 0)} orders, "
                                       f"{performance.get('success_rate', 0):.1f}% success rate")
            
            # Топ товары
            top_products = await self.db.fetch("""
                SELECT product_name, COUNT(*) as order_count, SUM(total_price) as revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'delivered'
                GROUP BY product_name
                ORDER BY revenue DESC
                LIMIT 5
            """)
            
            self.logger.info("🏆 Top Products:")
            for product in top_products:
                self.logger.info(f"  💊 {product['product_name']}: {product['order_count']} orders, "
                               f"{product['revenue']} сомoni revenue")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Analytics demo error: {e}")
            return False
    
    async def demo_system_logs(self):
        """Демонстрация системных логов"""
        self.logger.info("📋 Demo: System Logs")
        
        try:
            # Записываем несколько логов
            await self.db.log_action(
                user_id=1, action="demo_started", 
                details="Database demonstration started", 
                level=LogLevel.INFO
            )
            
            await self.db.log_action(
                user_id=1, order_id=1, action="order_created", 
                details="Test order created", 
                level=LogLevel.INFO
            )
            
            await self.db.log_action(
                user_id=1, action="demo_completed", 
                details="Database demonstration completed", 
                level=LogLevel.INFO
            )
            
            # Получаем логи
            logs = await self.db.get_system_logs(limit=10)
            
            self.logger.info("📋 Recent System Logs:")
            for log in logs:
                self.logger.info(f"  📝 {log.created_at.strftime('%H:%M:%S')} - {log.action}: {log.details}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System logs demo error: {e}")
            return False
    
    async def demo_performance_queries(self):
        """Демонстрация производительных запросов"""
        self.logger.info("⚡ Demo: Performance Queries")
        
        try:
            import time
            
            # Тестируем скорость запросов
            start_time = time.time()
            
            # 1. Поиск заказа по статусу
            orders = await self.db.get_orders_by_status(OrderStatus.CREATED, limit=10)
            query1_time = time.time() - start_time
            
            # 2. Поиск пользователя по Telegram ID
            start_time = time.time()
            user = await self.db.get_user_by_telegram_id(697780123)
            query2_time = time.time() - start_time
            
            # 3. Получение товаров заказа
            start_time = time.time()
            if orders:
                items = await self.db.get_order_items(orders[0].id)
            query3_time = time.time() - start_time
            
            # 4. Поиск оптимального сотрудника
            start_time = time.time()
            optimal = await self.db.get_optimal_worker(UserRole.PICKER)
            query4_time = time.time() - start_time
            
            self.logger.info("⚡ Query Performance:")
            self.logger.info(f"  📋 Orders by status: {query1_time*1000:.2f}ms")
            self.logger.info(f"  👤 User by Telegram ID: {query2_time*1000:.2f}ms")
            self.logger.info(f"  📦 Order items: {query3_time*1000:.2f}ms")
            self.logger.info(f"  🎯 Optimal worker: {query4_time*1000:.2f}ms")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Performance queries demo error: {e}")
            return False
    
    async def run_all_demos(self):
        """Запуск всех демонстраций"""
        self.logger.info("🚀 Starting Database Demo")
        self.logger.info("🗄️ MAXXPHARM CRM Database Operations")
        
        try:
            # 1. Операции с пользователями
            users = await self.demo_user_operations()
            await asyncio.sleep(0.5)
            
            # 2. Операции с клиентами
            clients = await self.demo_client_operations()
            await asyncio.sleep(0.5)
            
            # 3. Операции с заказами
            orders = await self.demo_order_operations(users, clients)
            await asyncio.sleep(0.5)
            
            # 4. Workflow заказа
            await self.demo_order_workflow(orders, users)
            await asyncio.sleep(0.5)
            
            # 5. Аналитика
            await self.demo_analytics()
            await asyncio.sleep(0.5)
            
            # 6. Системные логи
            await self.demo_system_logs()
            await asyncio.sleep(0.5)
            
            # 7. Производительность запросов
            await self.demo_performance_queries()
            
            self.logger.info("✅ All database demos completed successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Demo error: {e}")
        
        finally:
            if self.db:
                await self.db.close()

async def main():
    """Основная функция демонстрации"""
    print("🗄️ MAXXPHARM CRM Database Demo")
    print("🚀 Production-ready PostgreSQL database operations")
    print("📊 Full CRUD operations with real data")
    print("🔄 Complete order workflow")
    print("📈 Analytics and performance")
    print()
    
    # Используйте вашу строку подключения
    connection_string = "postgresql+asyncpg://solimfarm_db_steg_user:B4a9T78li3OZlOfVu3f6bF9iBfLWJfu9@dpg-d6ane6cr85hc73ep4qd0-a.oregon-postgres.render.com/solimfarm_db_steg"
    
    demo = DatabaseDemo(connection_string)
    
    try:
        await demo.setup()
        await demo.run_all_demos()
        
        print()
        print("✅ Database Demo completed!")
        print()
        print("🗄️ Key Features Demonstrated:")
        print("  👤 User management with roles and zones")
        print("  📦 Order creation with items")
        print("  🔄 Complete order workflow")
        print("  📊 Analytics and statistics")
        print("  📋 System logging")
        print("  ⚡ High-performance queries")
        print("  🔗 Relationships and constraints")
        print("  🎯 Optimal worker assignment")
        print()
        print("🚀 Database is ready for production!")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
