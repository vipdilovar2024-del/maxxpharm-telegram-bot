# 🏗️ MAXXPHARM CRM - Production Structure

## 📋 Обзор

Это production-структура для MAXXPHARM Telegram CRM на **aiogram 3.4.1**. 
Система поддерживает полный цикл заказа: **Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставлено**.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install aiogram==3.4.1 asyncpg python-dotenv
```

### 2. Настройка переменных окружения

```bash
# .env файл
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@localhost/crm
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_key
ADMIN_ID=your_admin_id
```

### 3. Создание базы данных

```sql
-- Создание таблиц
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    name VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id),
    operator_id INTEGER REFERENCES users(id),
    picker_id INTEGER REFERENCES users(id),
    checker_id INTEGER REFERENCES users(id),
    courier_id INTEGER REFERENCES users(id),
    comment TEXT,
    amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'created',
    message_type VARCHAR(20),
    photo_file_id TEXT,
    voice_file_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER,
    rejection_reason TEXT,
    payment_confirmed_at TIMESTAMP,
    payment_confirmed_by INTEGER
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_id INTEGER REFERENCES orders(id),
    type VARCHAR(50),
    message TEXT,
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Запуск бота

```bash
python bot/main.py
```

## 📁 Структура проекта

```
project/
├── bot/                    # Основные файлы бота
│   ├── main.py             # Главный файл запуска
│   ├── config.py           # Конфигурация
│   └── dispatcher.py       # Настройка диспетчера
├── handlers/               # Обработчики сообщений
│   ├── client.py          # Клиентские обработчики
│   ├── operator.py        # Обработчики оператора
│   ├── picker.py          # Обработчики сборщика
│   ├── checker.py         # Обработчики проверщика
│   ├── courier.py         # Обработчики курьера
│   └── admin.py           # Обработчики администратора
├── keyboards/             # Клавиатуры и карточки
│   ├── client_menu.py     # Меню клиента
│   ├── operator_menu.py   # Меню оператора
│   ├── picker_menu.py     # Меню сборщика
│   ├── checker_menu.py    # Меню проверщика
│   ├── courier_menu.py    # Меню курьера
│   └── order_cards.py     # Карточки заказов
├── services/              # Бизнес-логика
│   ├── order_service.py    # Сервис заказов
│   ├── payment_service.py  # Сервис платежей
│   ├── delivery_service.py # Сервис доставки
│   ├── assignment_service.py # Распределение
│   └── notification_service.py # Уведомления
├── database/              # Работа с базой данных
│   ├── db.py              # Подключение к БД
│   ├── models.py          # Модели данных
│   └── queries.py         # SQL запросы
├── middlewares/            # Middleware
│   ├── role_middleware.py # Определение ролей
│   └── logging_middleware.py # Логирование
├── ai/                    # AI функционал
│   ├── ai_reports.py      # AI отчеты
│   └── ai_monitor.py      # AI мониторинг
└── monitor/               # Мониторинг
    ├── health_check.py     # Проверка здоровья
    └── restart_guard.py    # Защита от падений
```

## 🔄 Процесс заказа

### 1. Клиент создает заявку
- Отправляет текст/фото/голос
- Заказ создается со статусом `created`
- Оператор получает уведомление

### 2. Оператор обрабатывает
- Просматривает новые заявки
- Принимает или отклоняет
- Подтверждает оплату
- Автоматически назначается сборщик

### 3. Сборщик собирает заказ
- Начинает сборку (status: `processing`)
- Завершает сборку (status: `ready`)
- Автоматически назначается проверщик

### 4. Проверщик проверяет
- Проверяет качество (status: `checking`)
- Подтвердает или находит ошибку
- Автоматически назначается курьер

### 5. Курьер доставляет
- Забирает заказ (status: `waiting_courier`)
- В пути (status: `on_way`)
- Доставляет (status: `delivered`)

## 👤 Роли пользователей

- **client** - Клиент (создает заказы)
- **operator** - Оператор (обрабатывает заявки)
- **picker** - Сборщик (собирает заказы)
- **checker** - Проверщик (проверяет качество)
- **courier** - Курьер (доставляет заказы)
- **admin** - Администратор (управление системой)
- **director** - Директор (аналитика и отчеты)

## 🔧 Интеграция в существующий бот

### Шаг 1: Добавьте папки
Скопируйте структуру папок в ваш проект.

### Шаг 2: Установите зависимости
```bash
pip install aiogram==3.4.1 asyncpg python-dotenv
```

### Шаг 3: Импортируйте в main.py
```python
from bot.dispatcher import setup_dispatcher
from middlewares.role_middleware import RoleMiddleware
```

### Шаг 4: Настройте диспетчер
```python
dp = Dispatcher()
await setup_dispatcher(dp)
dp.message.middleware(RoleMiddleware())
```

### Шаг 5: Добавьте базу данных
Создайте таблицы из SQL примера выше.

### Шаг 6: Настройте .env
Добавьте переменные окружения.

## 📊 Особенности

### ✅ Автоматическое распределение
- Least-load алгоритм для сотрудников
- Автоматическое назначение при смене статуса
- Отслеживание нагрузки работников

### ✅ Уведомления
- Клиент получает уведомления на каждом этапе
- Сотрудники получают уведомления о новых задачах
- Поддержка разных типов уведомлений

### ✅ Статистика
- Дневная статистика заказов
- Аналитика по сотрудникам
- AI отчеты для директора

### ✅ Надежность
- Middleware для определения ролей
- Логирование всех действий
- Обработка ошибок
- Health checks

## 🧪 Тестирование

### Тестовые пользователи
```python
# ID для тестирования
ADMIN_ID = 697780123  # Директор
CLIENT_ID = 697780128  # Клиент
OPERATOR_ID = 697780124  # Оператор
```

### Команды
- `/start` - запуск бота
- `/test_order` - тестовый заказ
- `/stats` - статистика (для директора)

## 🚀 Развертывание

### Render.com
1. Подключите репозиторий
2. Настройте переменные окружения
3. Запустите сервис

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot/main.py"]
```

## 📞 Поддержка

Если у вас есть вопросы по интеграции:
- 📧 Email: support@maxxpharm.com
- 💬 Telegram: @maxxpharm_support
- 📱 Телефон: +998 90 123 45 67

## 📄 Лицензия

MIT License - можете использовать в коммерческих проектах.
