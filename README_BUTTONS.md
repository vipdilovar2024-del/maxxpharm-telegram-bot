# 🧭 MAXXPHARM CRM - Готовые кнопки для aiogram 3.4.1

## 📋 Обзор

Это **production-ready набор кнопок** для MAXXPHARM Telegram CRM на **aiogram 3.4.1**. 
Система поддерживает полный цикл заказа: **Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено**.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install aiogram==3.4.1
```

### 2. Импорт компонентов

```python
from keyboards.main_menu import get_main_menu
from keyboards.order_cards_new import format_order_with_buttons
from keyboards.notifications import NotificationService
from handlers.callback_handlers import get_callback_router
```

### 3. Настройка бота

```python
from aiogram import Bot, Dispatcher
from middlewares.role_middleware import RoleMiddleware

bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher()

# Добавляем middleware
dp.message.middleware(RoleMiddleware())
dp.callback_query.middleware(RoleMiddleware())

# Добавляем обработчики
dp.include_router(get_callback_router())
```

### 4. Использование в handlers

```python
@dp.message(Command("start"))
async def cmd_start(message: Message, role: str):
    keyboard = get_main_menu(role)
    await message.answer("Приветствие", reply_markup=keyboard)

@dp.message(F.text == "📦 Сделать заявку")
async def cmd_create_order(message: Message, role: str):
    # Логика создания заказа
    order = {"id": 123, "client_name": "Ахмад", "status": "created"}
    
    text, keyboard = format_order_with_buttons(order, role)
    await message.answer(text, reply_markup=keyboard)
```

## 📁 Структура компонентов

```
keyboards/
├── main_menu.py           # Главные меню по ролям
├── order_cards_new.py     # Карточки заказов с кнопками
└── notifications.py      # Уведомления

handlers/
└── callback_handlers.py  # Обработчики inline кнопок
```

## 🎯 Главное меню (динамическое по роли)

### 📱 Клиент
```
📦 Сделать заявку
📍 Мои заказы
💳 Оплата
📞 Менеджер
ℹ️ Информация
```

### 👨‍💻 Оператор
```
📥 Новые заявки
💳 Подтверждение оплаты
📦 Все заказы
🔎 Найти заказ
📊 Статистика
```

### 📦 Сборщик
```
📦 Заказы на сборку
🔄 В сборке
📊 Моя статистика
```

### 🔍 Проверщик
```
🔍 Заказы на проверке
📊 Моя статистика
```

### 🚚 Курьер
```
🚚 Заказы к доставке
📍 В пути
📊 Моя статистика
```

### 👑 Директор
```
📊 Аналитика
📦 Все заказы
👥 Пользователи
📈 Продажи
⚙️ Настройки
```

## 📦 Карточка заказа

### Формат текста
```
📦 Заказ #245

✅ Статус: Accepted

👤 Клиент: Ахмад
📞 Телефон: +992900000000
📍 Адрес: г. Душанбе, ул. Айни 45

💊 Товары:
• Парацетамол ×2
• Амоксиклав ×1

💰 Сумма: 1450 сомони

🕐 Создан: 05.03.2024 14:30
```

### Кнопки по ролям

#### 👨‍💻 Оператор
```
[✅ Принять] [❌ Отказать]
[📞 Позвонить клиенту]
```

#### 📦 Сборщик
```
[▶ Начать сборку]
[📦 Готово]
```

#### 🔍 Проверщик
```
[❌ Ошибка] [✅ Проверено]
```

#### 🚚 Курьер
```
[🚚 Взять заказ]
[📍 Я в пути]
[✅ Доставлено]
```

#### 📱 Клиент
```
[💳 Оплатить]
[📍 Статус]
```

## 🔔 Уведомления

### Типы уведомлений
- **Изменение статуса заказа**
- **Новый заказ для оператора**
- **Назначение сотрудника**
- **Доставка завершена**
- **Дневные отчеты**

### Использование

```python
from keyboards.notifications import NotificationService

# Создаем сервис
notification_service = NotificationService(bot)

# Отправляем уведомление
await notification_service.notify_client_status_change(
    client_id=12345,
    order_id=245,
    new_status="processing",
    additional_info="Ваш заказ находится в сборке"
)
```

## 🎯 Callback обработчики

### Подключение
```python
from handlers.callback_handlers import get_callback_router

dp.include_router(get_callback_router())
```

### Поддерживаемые действия
- `accept_order_{id}` - принять заказ
- `reject_order_{id}` - отклонить заказ
- `start_pick_{id}` - начать сборку
- `picked_{id}` - завершить сборку
- `check_error_{id}` - ошибка проверки
- `checked_{id}` - проверено
- `take_delivery_{id}` - взять на доставку
- `on_way_{id}` - в пути
- `delivered_{id}` - доставлено

## 🧪 Демонстрация

### Запуск демо
```bash
python demo_buttons.py
```

### Демо команды
- `/start` - запуск бота с определением роли
- `/demo_order` - демонстрация карточки заказа
- `/demo_list` - демонстрация списка заказов
- `/demo_notification` - демонстрация уведомлений

### Тестовые пользователи
```
697780123 - Директор (Мухаммадмуссо)
697780124 - Оператор (Оператор Али)
697780125 - Сборщик (Сборщик Рустам)
697780126 - Проверщик (Проверщик Камол)
697780127 - Курьер (Курьер Бекзод)
697780128 - Клиент (Клиент Ахмад)
```

## 🔧 Интеграция в существующий бот

### Шаг 1: Скопируйте файлы
Скопируйте папки `keyboards/` и `handlers/` в ваш проект.

### Шаг 2: Добавьте импорты
```python
from keyboards.main_menu import get_main_menu
from keyboards.order_cards_new import format_order_with_buttons
from handlers.callback_handlers import get_callback_router
```

### Шаг 3: Настройте диспетчер
```python
dp.include_router(get_callback_router())
dp.message.middleware(RoleMiddleware())
```

### Шаг 4: Используйте в handlers
```python
@dp.message(Command("start"))
async def cmd_start(message: Message, role: str):
    keyboard = get_main_menu(role)
    await message.answer("Приветствие", reply_markup=keyboard)
```

## 📊 Особенности

### ✅ aiogram 3.4.1 совместимость
- Современные фильтры и типы
- Правильная работа с callback
- Async/await паттерны

### ✅ Production-ready
- Обработка ошибок
- Логирование
- Валидация данных
- Оптимизированные запросы

### ✅ Масштабируемость
- Модульная архитектура
- Легкое добавление новых ролей
- Гибкая настройка кнопок
- Расширяемая система уведомлений

### ✅ UX оптимизация
- Понятные эмодзи для статусов
- Удобная навигация
- Информативные карточки
- Быстрые действия

## 🔄 Процесс заказа

### 1. Клиент создает заявку
- Отправляет текст/фото/голос
- Заказ создается со статусом `created`
- Оператор получает уведомление

### 2. Оператор обрабатывает
- Нажимает "✅ Принять"
- Статус меняется на `accepted`
- Автоматически назначается сборщик

### 3. Сборщик собирает
- Нажимает "▶ Начать сборку"
- Статус `processing`
- Нажимает "📦 Готово"
- Статус `ready`
- Автоматически назначается проверщик

### 4. Проверщик проверяет
- Нажимает "✅ Проверено"
- Статус `checking` → `waiting_courier`
- Автоматически назначается курьер

### 5. Курьер доставляет
- Нажимает "🚚 Взять заказ"
- Статус `on_way`
- Нажимает "✅ Доставлено"
- Статус `delivered`

## 📞 Поддержка

Если у вас есть вопросы:
- 📧 Email: support@maxxpharm.com
- 💬 Telegram: @maxxpharm_support
- 📱 Телефон: +998 90 123 45 67

## 📄 Лицензия

MIT License - можете использовать в коммерческих проектах.

---

## 🎉 Результат

После внедрения этих кнопок ваш бот станет **полноценной Telegram CRM системой**:

✅ **Принимает заказы** - через удобный интерфейс
✅ **Управляет оплатой** - с подтверждением и уведомлениями
✅ **Управляет складом** - с автоматическим распределением
✅ **Управляет доставкой** - с трекингом и статусами
✅ **Анализирует бизнес** - с отчетами и статистикой

**Все это внутри Telegram!** 🚀
