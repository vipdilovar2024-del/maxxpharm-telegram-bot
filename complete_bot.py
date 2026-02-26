#!/usr/bin/env python3
"""
ПОЛНОФУНКЦИОНАЛЬНЫЙ ТЕЛЕГРАМ БОТ - МАКСИМАЛЬНЫЙ ПРОЕКТ
"""
import urllib.request
import urllib.parse
import json
import os
import time
import sqlite3
import hashlib
import datetime
from typing import Dict, List, Optional

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN не найден!")
    exit(1)

# URL Telegram API
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.db_path = "bot.db"
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                customer_email TEXT,
                products TEXT,
                total_amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица отчетов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                report_data TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, telegram_id: str) -> Optional[Dict]:
        """Получить пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ? AND is_active = 1",
            (telegram_id,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'telegram_id': user[1],
                'username': user[2],
                'full_name': user[3],
                'phone': user[4],
                'email': user[5],
                'role': user[6],
                'is_active': user[7],
                'created_at': user[8],
                'updated_at': user[9]
            }
        return None
    
    def create_user(self, telegram_id: str, username: str, full_name: str, 
                   phone: str = None, email: str = None, role: str = 'user') -> bool:
        """Создать пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users 
                   (telegram_id, username, full_name, phone, email, role, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (telegram_id, username, full_name, phone, email, role)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_user_role(self, telegram_id: str, role: str) -> bool:
        """Обновить роль пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (role, telegram_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at")
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': user[0],
                'telegram_id': user[1],
                'username': user[2],
                'full_name': user[3],
                'phone': user[4],
                'email': user[5],
                'role': user[6],
                'is_active': user[7],
                'created_at': user[8],
                'updated_at': user[9]
            }
            for user in users
        ]
    
    def create_order(self, order_number: str, customer_name: str, 
                    customer_phone: str, customer_email: str, 
                    products: str, total_amount: float) -> bool:
        """Создать заказ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO orders 
                   (order_number, customer_name, customer_phone, customer_email, products, total_amount, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
                (order_number, customer_name, customer_phone, customer_email, products, total_amount)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_orders(self) -> List[Dict]:
        """Получить все заказы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': order[0],
                'order_number': order[1],
                'customer_name': order[2],
                'customer_phone': order[3],
                'customer_email': order[4],
                'products': order[5],
                'total_amount': order[6],
                'status': order[7],
                'created_at': order[8],
                'updated_at': order[9]
            }
            for order in orders
        ]
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, order_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def create_report(self, report_type: str, report_data: str, generated_by: str) -> bool:
        """Создать отчет"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (report_type, report_data, generated_by) VALUES (?, ?, ?)",
            (report_type, report_data, generated_by)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_reports(self) -> List[Dict]:
        """Получить отчеты"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports ORDER BY generated_at DESC")
        reports = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': report[0],
                'report_type': report[1],
                'report_data': report[2],
                'generated_at': report[3],
                'generated_by': report[4]
            }
            for report in reports
        ]

class TelegramBot:
    """Основной класс бота"""
    
    def __init__(self):
        self.db = Database()
        self.offset = None
        self.admin_id = "697780123"
    
    def send_message(self, chat_id: int, text: str, keyboard=None) -> bool:
        """Отправить сообщение"""
        url = f"{TELEGRAM_API}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if keyboard:
            data['reply_markup'] = json.dumps({
                'inline_keyboard': keyboard
            })
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                url,
                data=encoded_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def answer_callback(self, callback_id: str, text: str) -> bool:
        """Ответить на callback"""
        url = f"{TELEGRAM_API}/answerCallbackQuery"
        
        data = {
            'callback_query_id': callback_id,
            'text': text
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                url,
                data=encoded_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            urllib.request.urlopen(req)
            return True
        except Exception as e:
            print(f"Error answering callback: {e}")
            return False
    
    def get_updates(self):
        """Получить обновления"""
        url = f"{TELEGRAM_API}/getUpdates"
        
        data = {'timeout': 10}
        if self.offset:
            data['offset'] = self.offset
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                url,
                data=encoded_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('result', [])
        except Exception as e:
            print(f"Error getting updates: {e}")
            return []
    
    def handle_start(self, message):
        """Обработчик команды /start"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        user_info = message['from']
        
        print(f"Получен /start от {user_id}")
        
        # Создаем или обновляем пользователя
        user = self.db.get_user(str(user_id))
        
        if not user:
            # Создаем нового пользователя
            self.db.create_user(
                str(user_id),
                user_info.get('username', ''),
                user_info.get('full_name', ''),
                user_info.get('phone', ''),
                user_info.get('email', ''),
                'user'
            )
        
        # Проверяем админа
        if str(user_id) == self.admin_id:
            print(f"Администратор {user_id} вошел в систему")
            
            # Обновляем роль администратора
            self.db.update_user_role(str(user_id), 'admin')
            
            keyboard = [
                [{'text': '👥 Управление пользователями', 'callback_data': 'users'}],
                [{'text': '📦 Управление заказами', 'callback_data': 'orders'}],
                [{'text': '📊 Отчеты', 'callback_data': 'reports'}],
                [{'text': '⚙️ Настройки', 'callback_data': 'settings'}],
                [{'text': '📈 Статистика', 'callback_data': 'stats'}],
                [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
            ]
            
            text = (
                f"👋 Добро пожаловать, {user_info.get('full_name', 'Пользователь')}!\n\n"
                f"🔐 Роль: АДМИНИСТРАТОР\n"
                f"🟢 Доступ: РАЗРЕШЕН\n"
                f"📊 ID: {user_id}\n\n"
                f"📅 Всего пользователей: {len(self.db.get_all_users())}\n"
                f"📦 Всего заказов: {len(self.db.get_all_orders())}\n\n"
                "Выберите действие:"
            )
            
            return self.send_message(chat_id, text, keyboard)
        
        else:
            # Обычный пользователь
            keyboard = [
                [{'text': '📞 Связаться с поддержкой', 'callback_data': 'support'}],
                [{'text': '📋 Мои заказы', 'callback_data': 'my_orders'}]
            ]
            
            text = (
                f"👋 Добро пожаловать, {user_info.get('full_name', 'Пользователь')}!\n\n"
                f"🔐 Роль: ПОЛЬЗОВАТЕЛЬ\n"
                f"🟢 Доступ: РАЗРЕШЕН\n\n"
                "Выберите действие:"
            )
            
            return self.send_message(chat_id, text, keyboard)
    
    def handle_users_menu(self, callback):
        """Обработчик меню пользователей"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        if str(user_id) != self.admin_id:
            self.answer_callback(callback['id'], "Доступ запрещен")
            return
        
        if data == 'users':
            users = self.db.get_all_users()
            
            if not users:
                return self.send_message(chat_id, "📋 Пользователей пока нет")
            
            text = "👥 **Список пользователей:**\n\n"
            
            for user in users:
                status = "🟢" if user['is_active'] else "🔴"
                role_emoji = "👑" if user['role'] == 'admin' else "👤"
                
                text += f"{status} {role_emoji} {user['full_name']}\n"
                text += f"📱 @{user.get('username', 'N/A')}\n"
                text += f"📞 {user.get('phone', 'N/A')}\n"
                text += f"📧 {user.get('email', 'N/A')}\n"
                text += f"🔑 {user['role']}\n"
                text += f"📅 {user['created_at']}\n\n"
            
            keyboard = [
                [{'text': '➕ Добавить пользователя', 'callback_data': 'add_user'}],
                [{'text': '✏️ Изменить роль', 'callback_data': 'edit_role'}],
                [{'text': '🗑️ Деактивировать', 'callback_data': 'deactivate_user'}],
                [{'text': '🔙 Назад', 'callback_data': 'main'}]
            ]
            
            self.answer_callback(callback['id'], "Пользователи")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'add_user':
            text = (
                "➕ **Добавление пользователя**\n\n"
                "Для добавления пользователя, пожалуйста, отправьте данные в формате:\n\n"
                "📝 `add_user: <telegram_id> <username> <full_name> <phone> <email> <role>`\n\n"
                "Пример:\n"
                "`add_user: 123456789 username Full Name +79912345678 user@example.com user`\n\n"
                "⚠️ Все поля обязательны, кроме телефона и email"
            )
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'users'}]
            ]
            
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'edit_role':
            text = (
                "✏️ **Изменение роли пользователя**\n\n"
                "Для изменения роли пользователя, отправьте:\n\n"
                "📝 `edit_role: <telegram_id> <new_role>`\n\n"
                "Доступные роли:\n"
                "• `admin` - Администратор\n"
                "• `manager` - Менеджер\n"
                "• `user` - Пользователь\n\n"
                "Пример:\n"
                "`edit_role: 123456789 admin`"
            )
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'users'}]
            ]
            
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'deactivate_user':
            text = (
                "🗑️ **Деактивация пользователя**\n\n"
                "Для деактивации пользователя, отправьте:\n\n"
                "📝 `deactivate: <telegram_id>`\n\n"
                "⚠️ Пользователь потеряет доступ к системе"
            )
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'users'}]
            ]
            
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'main':
            return self.handle_start({'chat': {'id': chat_id}, 'from': {'id': user_id}})
        
        else:
            return self.handle_users_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': data})
    
    def handle_orders_menu(self, callback):
        """Обработчик меню заказов"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        if str(user_id) != self.admin_id:
            self.answer_callback(callback['id'], "Доступ запрещен")
            return
        
        if data == 'orders':
            orders = self.db.get_all_orders()
            
            if not orders:
                return self.send_message(chat_id, "📦 Заказов пока нет")
            
            text = "📦 **Список заказов:**\n\n"
            
            for order in orders:
                status_emoji = {
                    'pending': '⏳️',
                    'confirmed': '✅',
                    'preparing': '🔄',
                    'ready': '🚚',
                    'delivered': '✅',
                    'cancelled': '❌'
                }
                
                text += f"📄 Заказ: {order['order_number']}\n"
                text += f"👤 Клиент: {order['customer_name']}\n"
                text += f"📞 Телефон: {order['customer_phone']}\n"
                text += f"📧 Email: {order['customer_email']}\n"
                text += f"📦 Товары: {order['products']}\n"
                text += f"💰 Сумма: {order['total_amount']} руб.\n"
                text += f"{status_emoji.get(order['status'], '❓')} Статус: {order['status']}\n"
                text += f"📅 Создан: {order['created_at']}\n\n"
            
            keyboard = [
                [{'text': '➕ Создать заказ', 'callback_data': 'create_order'}],
                [{'text': '✏️ Изменить статус', 'callback_data': 'update_status'}],
                [{'text': '🔙 Назад', 'callback_data': 'main'}]
            ]
            
            self.answer_callback(callback['id'], "Заказы")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'create_order':
            text = (
                "➕ **Создание заказа**\n\n"
                "Для создания заказа, отправьте данные в формате:\n\n"
                "📝 `order: <order_number> <customer_name> <customer_phone> <customer_email> <products> <total_amount>`\n\n"
                "Пример:\n"
                "`order: ORD-001 Иванов Иван +79912345678 ivan@example.com Товар1,Товар2 15000.50`\n\n"
                "⚠️ Все поля обязательны"
            )
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'orders'}]
            ]
            
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'update_status':
            text = (
                "✏️ **Изменение статуса заказа**\n\n"
                "Для изменения статуса заказа, отправьте:\n\n"
                "📝 `status: <order_id> <new_status>`\n\n"
                "Доступные статусы:\n"
                "• `pending` - В ожидании\n"
                "• `confirmed` - Подтвержден\n"
                "• `preparing` - Готовится\n"
                "• `ready` - Готов\n"
                "• `delivered` - Доставлен\n"
                "• `cancelled` - Отменен\n\n"
                "Пример:\n"
                "`status: 1 confirmed`"
            )
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'orders'}]
            ]
            
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'main':
            return self.handle_start({'chat': {'id': chat_id}, 'from': {'id': user_id}})
        
        else:
            return self.handle_orders_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': data})
    
    def handle_reports_menu(self, callback):
        """Обработчик меню отчетов"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        if str(user_id) != self.admin_id:
            self.answer_callback(callback['id'], "Доступ запрещен")
            return
        
        if data == 'reports':
            reports = self.db.get_reports()
            
            if not reports:
                return self.send_message(chat_id, "📊 Отчетов пока нет")
            
            text = "📊 **Список отчетов:**\n\n"
            
            for report in reports:
                text += f"📄 Тип: {report['report_type']}\n"
                text += f"👤 Создал: {report['generated_by']}\n"
                text += f"📅 Создан: {report['generated_at']}\n"
                text += f"📋 Данные: {report['report_data']}\n\n"
            
            keyboard = [
                [{'text': '📊 Пользователи', 'callback_data': 'report_users'}],
                [{'text': '📦 Заказы', 'callback_data': 'report_orders'}],
                [{'text': '💰 Финансы', 'callback_data': 'report_finances'}],
                [{'text': '📈 Статистика', 'callback_data': 'report_stats'}],
                [{'text': '🔙 Назад', 'callback_data': 'main'}]
            ]
            
            self.answer_callback(callback['id'], "Отчеты")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'report_users':
            users = self.db.get_all_users()
            
            total_users = len(users)
            active_users = len([u for u in users if u['is_active']])
            admins = len([u for u in users if u['role'] == 'admin'])
            regular_users = len([u for u in users if u['role'] == 'user'])
            
            report_data = f"Всего пользователей: {total_users}\n"
            report_data += f"Активных: {active_users}\n"
            report_data += f"Администраторов: {admins}\n"
            report_data += f"Обычных пользователей: {regular_users}\n\n"
            
            for user in users[:10]:
                report_data += f"• {user['full_name']} (@{user.get('username', 'N/A')}) - {user['role']}\n"
            
            if len(users) > 10:
                report_data += f"... и еще {len(users) - 10} пользователей"
            
            self.db.create_report('users', report_data, str(user_id))
            
            text = f"📊 **Отчет по пользователям**\n\n{report_data}"
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'reports'}]
            ]
            
            self.answer_callback(callback['id'], "Отчет создан")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'report_orders':
            orders = self.db.get_all_orders()
            
            total_orders = len(orders)
            pending_orders = len([o for o in orders if o['status'] == 'pending'])
            confirmed_orders = len([o for o in orders if o['status'] == 'confirmed'])
            total_amount = sum(o['total_amount'] for o in orders)
            
            report_data = f"Всего заказов: {total_orders}\n"
            report_data += f"В ожидании: {pending_orders}\n"
            report_data += f"Подтвержденных: {confirmed_orders}\n"
            report_data += f"Общая сумма: {total_amount:.2f} руб.\n\n"
            
            for order in orders[:10]:
                report_data += f"• Заказ {order['order_number']} - {order['customer_name']} - {order['total_amount']:.2f} руб. ({order['status']})\n"
            
            if len(orders) > 10:
                report_data += f"... и еще {len(orders) - 10} заказов"
            
            self.db.create_report('orders', report_data, str(user_id))
            
            text = f"📊 **Отчет по заказам**\n\n{report_data}"
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'reports'}]
            ]
            
            self.answer_callback(callback['id'], "Отчет создан")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'report_finances':
            orders = self.db.get_all_orders()
            
            total_amount = sum(o['total_amount'] for o in orders)
            
            status_amounts = {}
            for order in orders:
                status = order['status']
                if status not in status_amounts:
                    status_amounts[status] = 0
                status_amounts[status] += order['total_amount']
            
            report_data = f"Общая сумма всех заказов: {total_amount:.2f} руб.\n\n"
            report_data += "По статусам:\n"
            
            for status, amount in status_amounts.items():
                status_emoji = {
                    'pending': '⏳️',
                    'confirmed': '✅',
                    'preparing': '🔄',
                    'ready': '🚚',
                    'delivered': '✅',
                    'cancelled': '❌'
                }
                
                report_data += f"{status_emoji.get(status, '❓')} {status}: {amount:.2f} руб.\n"
            
            self.db.create_report('finances', report_data, str(user_id))
            
            text = f"💰 **Финансовый отчет**\n\n{report_data}"
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'reports'}]
            ]
            
            self.answer_callback(callback['id'], "Отчет создан")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'report_stats':
            users = self.db.get_all_users()
            orders = self.db.get_all_orders()
            reports = self.db.get_reports()
            
            stats_text = f"📈 **Общая статистика**\n\n"
            stats_text += f"👥 Пользователей: {len(users)}\n"
            stats_text += f"📦 Заказов: {len(orders)}\n"
            stats_text += f"📊 Отчетов: {len(reports)}\n"
            stats_text += f"💰 Общая сумма заказов: {sum(o['total_amount'] for o in orders):.2f} руб.\n"
            stats_text += f"🤖 Время работы: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            self.db.create_report('stats', stats_text, str(user_id))
            
            keyboard = [
                [{'text': '🔙 Назад', 'callback_data': 'reports'}]
            ]
            
            self.answer_callback(callback['id'], "Статистика собрана")
            return self.send_message(chat_id, stats_text, keyboard)
        
        elif data == 'main':
            return self.handle_start({'chat': {'id': chat_id}, 'from': {'id': user_id}})
        
        else:
            return self.handle_reports_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': data})
    
    def handle_settings_menu(self, callback):
        """Обработчик меню настроек"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        if str(user_id) != self.admin_id:
            self.answer_callback(callback['id'], "Доступ запрещен")
            return
        
        if data == 'settings':
            text = (
                "⚙️ **Настройки администратора**\n\n"
                "🔧 **Доступные команды:**\n\n"
                "📝 `add_user: <telegram_id> <username> <full_name> <phone> <email> <role>`\n"
                "📝 `edit_role: <telegram_id> <new_role>`\n"
                "📝 `deactivate: <telegram_id>`\n"
                "📝 `order: <order_number> <customer_name> <customer_phone> <customer_email> <products> <total_amount>`\n"
                "📝 `status: <order_id> <new_status>`\n"
                "📝 `report: <type>` (users/orders/finances/stats)\n\n"
                "🔐 **ID администратора:** " + self.admin_id + "\n"
                "🤖 **Бот работает стабильно**\n"
                "📊 **База данных:** SQLite\n"
                "📅 **Время работы:** " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            keyboard = [
                [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
            ]
            
            self.answer_callback(callback['id'], "Настройки")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'main':
            return self.handle_start({'chat': {'id': chat_id}, 'from': {'id': user_id}})
        
        else:
            return self.handle_settings_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': data})
    
    def handle_stats_menu(self, callback):
        """Обработчик меню статистики"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        if str(user_id) != self.admin_id:
            self.answer_callback(callback['id'], "Доступ запрещен")
            return
        
        if data == 'stats':
            users = self.db.get_all_users()
            orders = self.db.get_all_orders()
            reports = self.db.get_reports()
            
            text = "📈 **Статистика системы**\n\n"
            text += f"👥 Пользователей: {len(users)}\n"
            text += f"📦 Заказов: {len(orders)}\n"
            text += f"📊 Отчетов: {len(reports)}\n"
            text += f"💰 Общая сумма: {sum(o['total_amount'] for o in orders):.2f} руб.\n"
            text += f"🤖 Время работы: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            admin_count = len([u for u in users if u['role'] == 'admin'])
            user_count = len([u for u in users if u['role'] == 'user'])
            
            text += "📊 **Распределение по ролям:**\n"
            text += f"👑 Администраторы: {admin_count}\n"
            text += f"👤 Пользователи: {user_count}\n\n"
            
            status_counts = {}
            for order in orders:
                status = order['status']
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
            
            text += "📦 **Заказы по статусам:**\n"
            for status, count in status_counts.items():
                status_emoji = {
                    'pending': '⏳️',
                    'confirmed': '✅',
                    'preparing': '🔄',
                    'ready': '🚚',
                    'delivered': '✅',
                    'cancelled': '❌'
                }
                
                text += f"{status_emoji.get(status, '❓')} {status}: {count}\n"
            
            keyboard = [
                [{'text': '📊 Создать отчет', 'callback_data': 'reports'}],
                [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
            ]
            
            self.answer_callback(callback['id'], "Статистика")
            return self.send_message(chat_id, text, keyboard)
        
        elif data == 'main':
            return self.handle_start({'chat': {'id': chat_id}, 'from': {'id': user_id}})
        
        else:
            return self.handle_stats_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': data})
    
    def handle_text_message(self, message):
        """Обработчик текстовых сообщений"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        text = message.get('text', '')
        
        print(f"Текстовое сообщение от {user_id}: {text}")
        
        # Проверяем команды администратора
        if str(user_id) == self.admin_id:
            if text.startswith('add_user:'):
                try:
                    parts = text.split(' ', 6)
                    telegram_id = parts[1]
                    username = parts[2]
                    full_name = parts[3]
                    phone = parts[4] if len(parts) > 4 else None
                    email = parts[5] if len(parts) > 5 else None
                    role = parts[6] if len(parts) > 6 else 'user'
                    
                    if self.db.create_user(telegram_id, username, full_name, phone, email, role):
                        self.send_message(chat_id, f"✅ Пользователь {full_name} успешно добавлен")
                    else:
                        self.send_message(chat_id, "❌ Ошибка: пользователь с таким ID уже существует")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            elif text.startswith('edit_role:'):
                try:
                    parts = text.split(' ', 2)
                    telegram_id = parts[1]
                    new_role = parts[2]
                    
                    if self.db.update_user_role(telegram_id, new_role):
                        self.send_message(chat_id, f"✅ Роль пользователя {telegram_id} изменена на {new_role}")
                    else:
                        self.send_message(chat_id, "❌ Ошибка: пользователь не найден")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            elif text.startswith('deactivate:'):
                try:
                    telegram_id = text.split(' ', 1)[1]
                    
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET is_active = 0 WHERE telegram_id = ?",
                        (telegram_id,)
                    )
                    conn.commit()
                    conn.close()
                    
                    self.send_message(chat_id, f"✅ Пользователь {telegram_id} деактивирован")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            elif text.startswith('order:'):
                try:
                    parts = text.split(' ', 6)
                    order_number = parts[1]
                    customer_name = parts[2]
                    customer_phone = parts[3]
                    customer_email = parts[4]
                    products = parts[5]
                    total_amount = float(parts[6])
                    
                    if self.db.create_order(order_number, customer_name, customer_phone, customer_email, products, total_amount):
                        self.send_message(chat_id, f"✅ Заказ {order_number} успешно создан")
                    else:
                        self.send_message(chat_id, "❌ Ошибка: заказ с таким номером уже существует")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            elif text.startswith('status:'):
                try:
                    parts = text.split(' ', 2)
                    order_id = int(parts[1])
                    new_status = parts[2]
                    
                    if self.db.update_order_status(order_id, new_status):
                        self.send_message(chat_id, f"✅ Статус заказа {order_id} изменен на {new_status}")
                    else:
                        self.send_message(chat_id, "❌ Ошибка: заказ не найден")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            elif text.startswith('report:'):
                try:
                    report_type = text.split(' ', 1)[1]
                    
                    if report_type == 'users':
                        return self.handle_reports_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': 'report_users'})
                    elif report_type == 'orders':
                        return self.handle_reports_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': 'report_orders'})
                    elif report_type == 'finances':
                        return self.handle_reports_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': 'report_finances'})
                    elif report_type == 'stats':
                        return self.handle_reports_menu({'message': callback['message'], 'from': {'id': user_id}, 'data': 'report_stats'})
                    else:
                        self.send_message(chat_id, "❌ Неизвестный тип отчета")
                except:
                    self.send_message(chat_id, "❌ Ошибка: неверный формат команды")
            
            else:
                self.send_message(chat_id, "❌ Неизвестная команда. Используйте меню.")
        
        else:
            # Обычный пользователь
            keyboard = [
                [{'text': '📞 Связаться с поддержкой', 'callback_data': 'support'}],
                [{'text': '📋 Мои заказы', 'callback_data': 'my_orders'}]
            ]
            
            self.send_message(chat_id, "Для получения помощи, свяжитесь с поддержкой.", keyboard)
    
    def handle_support(self, callback):
        """Обработчик поддержки"""
        chat_id = callback['message']['chat']['id']
        
        text = (
            "📞 **Служба поддержки**\n\n"
            "Для получения помощи, пожалуйста:\n\n"
            "📧 Напишите на почту: support@example.com\n"
            "📞 Позвоните: +7 (XXX) XXX-XX-XX\n"
            "💬 Напишите в Telegram: @admin\n\n"
            "Мы свяжемся с вами в ближайшее время!"
        )
        
        keyboard = [
            [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
        ]
        
        self.answer_callback(callback['id'], "Поддержка")
        return self.send_message(chat_id, text, keyboard)
    
    def handle_my_orders(self, callback):
        """Обработчик моих заказов"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        
        user = self.db.get_user(str(user_id))
        if not user:
            return self.send_message(chat_id, "❌ Сначала зарегистрируйтесь через /start")
        
        text = "📋 **Мои заказы**\n\n"
        text += "К сожалению, функция поиска заказов по пользователю пока не реализована.\n"
        text += "Свяжитесь с администратором для получения информации о ваших заказах.\n\n"
        text += f"📧 Ваш email: {user.get('email', 'Не указан')}\n"
        text += f"📞 Ваш телефон: {user.get('phone', 'Не указан')}"
        
        keyboard = [
            [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
        ]
        
        self.answer_callback(callback['id'], "Мои заказы")
        return self.send_message(chat_id, text, keyboard)
    
    def handle_callback(self, callback):
        """Обработчик callback"""
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        data = callback['data']
        
        print(f"Callback от {user_id}: {data}")
        
        # Маршрутизация
        if data in ['users', 'add_user', 'edit_role', 'deactivate_user', 'main']:
            return self.handle_users_menu(callback)
        elif data in ['orders', 'create_order', 'update_status', 'main']:
            return self.handle_orders_menu(callback)
        elif data in ['reports', 'report_users', 'report_orders', 'report_finances', 'report_stats', 'main']:
            return self.handle_reports_menu(callback)
        elif data in ['settings', 'stats', 'main']:
            return self.handle_settings_menu(callback)
        elif data == 'support':
            return self.handle_support(callback)
        elif data == 'my_orders':
            return self.handle_my_orders(callback)
        else:
            return self.answer_callback(callback['id'], "Неизвестное действие")
    
    def handle_message(self, message):
        """Обработчик сообщений"""
        if 'text' in message:
            return self.handle_text_message(message)
        else:
            return self.handle_start(message)
    
    def run(self):
        """Основной цикл бота"""
        print("=" * 50)
        print("ПОЛНОФУНКЦИОНАЛЬНЫЙ ТЕЛЕГРАМ БОТ ЗАПУСКАЕТСЯ...")
        print("=" * 50)
        print(f"🤖 Админ ID: {self.admin_id}")
        print(f"📊 База данных: {self.db.db_path}")
        print(f"🕐 API: {TELEGRAM_API}")
        print("=" * 50)
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    if 'message' in update:
                        self.handle_message(update['message'])
                    elif 'callback_query' in update:
                        self.handle_callback(update['callback_query'])
                    
                    self.offset = update['update_id'] + 1
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("Бот остановлен")
                break
            except Exception as e:
                print(f"Ошибка в главном цикле: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
