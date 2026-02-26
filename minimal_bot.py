#!/usr/bin/env python3
"""
МИНИМАЛЬНЫЙ БОТ - без зависимостей
"""
import urllib.request
import urllib.parse
import json
import os
import time

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN не найден!")
    exit(1)

# URL Telegram API
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, keyboard=None):
    """Отправка сообщения"""
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

def get_updates(offset=None):
    """Получение обновлений"""
    url = f"{TELEGRAM_API}/getUpdates"
    
    data = {'timeout': 10}
    if offset:
        data['offset'] = offset
    
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

def handle_message(message):
    """Обработка сообщения"""
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_id = message['from']['id']
    
    print(f"Получено сообщение от {user_id}: {text}")
    
    # ПРЯМАЯ ПРОВЕРКА ID
    if str(user_id) == "697780123":
        print(f"Доступ разрешен для {user_id}")
        
        # Создаем клавиатуру
        keyboard = [
            [{'text': '👥 Управление пользователями', 'callback_data': 'users'}],
            [{'text': '📦 Управление заказами', 'callback_data': 'orders'}],
            [{'text': '📊 Отчеты', 'callback_data': 'reports'}],
            [{'text': '⚙️ Настройки', 'callback_data': 'settings'}],
            [{'text': '🔙 Главное меню', 'callback_data': 'main'}]
        ]
        
        response_text = (
            "👋 Добро пожаловать, VIP Dilovar!\n\n"
            "🔐 Роль: АДМИНИСТРАТОР\n"
            "🟢 Доступ: РАЗРЕШЕН\n\n"
            "Выберите действие:"
        )
        
        return send_message(chat_id, response_text, keyboard)
    
    else:
        print(f"Доступ запрещен для {user_id}")
        response_text = (
            "❌ Доступ запрещен. Ваш Telegram ID не найден в системе.\n"
            f"Ваш ID: {user_id}\n"
            "Свяжитесь с администратором для получения доступа."
        )
        
        return send_message(chat_id, response_text)

def handle_callback(callback):
    """Обработка callback"""
    chat_id = callback['message']['chat']['id']
    user_id = callback['from']['id']
    data = callback['data']
    
    print(f"Нажата кнопка: {data} от {user_id}")
    
    if str(user_id) == "697780123":
        # Отвечаем на callback
        answer_text = f"Вы выбрали: {data}"
        send_message(chat_id, answer_text)
        
        # Отвечаем на callback query
        callback_url = f"{TELEGRAM_API}/answerCallbackQuery"
        callback_data = {
            'callback_query_id': callback['id'],
            'text': f"Выбрано: {data}"
        }
        
        encoded_data = urllib.parse.urlencode(callback_data).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                callback_url,
                data=encoded_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Error answering callback: {e}")

def main():
    """Главная функция"""
    print("=" * 50)
    print("МИНИМАЛЬНЫЙ БОТ ЗАПУСКАЕТСЯ...")
    print("=" * 50)
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            for update in updates:
                if 'message' in update:
                    handle_message(update['message'])
                elif 'callback_query' in update:
                    handle_callback(update['callback_query'])
                
                offset = update['update_id'] + 1
            
            # Небольшая задержка чтобы не нагружать API
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("Бот остановлен")
            break
        except Exception as e:
            print(f"Ошибка в главном цикле: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
