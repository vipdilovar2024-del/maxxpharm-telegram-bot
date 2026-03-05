"""
🗄️ Database Migrations - SQL миграции для MAXXPHARM CRM
Production-ready миграции для создания и обновления базы данных
"""

# 🗄️ SQL МИГРАЦИИ ДЛЯ MAXXPHARM CRM
# =====================================

MIGRATION_001_CREATE_TABLES = """
-- 🗄️ МИГРАЦИЯ 001: Создание базовых таблиц
-- Создание основной структуры базы данных

-- 1️⃣ Таблица сотрудников (users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'operator', 'picker', 'checker', 'courier', 'director')),
    zone TEXT CHECK (zone IN ('центр', 'север', 'юг', 'восток', 'запад')),
    is_online BOOLEAN DEFAULT TRUE,
    active_orders INTEGER DEFAULT 0,
    max_orders INTEGER DEFAULT 5,
    performance_score DECIMAL(3,2) DEFAULT 5.0 CHECK (performance_score >= 0 AND performance_score <= 10),
    last_assigned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2️⃣ Таблица клиентов (clients)
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    zone TEXT CHECK (zone IN ('центр', 'север', 'юг', 'восток', 'запад')),
    is_active BOOLEAN DEFAULT TRUE,
    total_orders INTEGER DEFAULT 0,
    total_spent NUMERIC(12,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3️⃣ Таблица заказов (orders)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN (
        'created', 'waiting_payment', 'accepted', 'picking', 'checking', 
        'ready', 'waiting_courier', 'on_delivery', 'delivered', 'rejected', 'cancelled'
    )),
    operator_id INTEGER REFERENCES users(id),
    picker_id INTEGER REFERENCES users(id),
    checker_id INTEGER REFERENCES users(id),
    courier_id INTEGER REFERENCES users(id),
    total_price NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    delivery_price NUMERIC(8,2) DEFAULT 0.00,
    zone TEXT CHECK (zone IN ('центр', 'север', 'юг', 'восток', 'запад')),
    address TEXT NOT NULL,
    comment TEXT,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    estimated_time INTEGER,
    actual_time INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 4️⃣ Таблица товаров в заказах (order_items)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    total_price NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    requires_prescription BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5️⃣ История статусов заказа (order_status_history)
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by INTEGER REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6️⃣ Таблица оплат (payments)
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    method TEXT NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'terminal', 'online', 'crypto')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'failed', 'refunded')),
    proof_photo TEXT,
    transaction_id TEXT,
    confirmed_by INTEGER REFERENCES users(id),
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 7️⃣ Таблица доставки (delivery)
CREATE TABLE IF NOT EXISTS delivery (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    courier_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL CHECK (status IN ('assigned', 'picked_up', 'on_way', 'delivered', 'failed')),
    pickup_time TIMESTAMP,
    delivery_time TIMESTAMP,
    actual_distance NUMERIC(8,2),
    delivery_notes TEXT,
    client_rating INTEGER CHECK (client_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 8️⃣ Таблица логов системы (system_logs)
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    client_id INTEGER REFERENCES clients(id),
    order_id INTEGER REFERENCES orders(id),
    action TEXT NOT NULL,
    details TEXT,
    level TEXT DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9️⃣ Таблица настроек (settings)
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

MIGRATION_002_CREATE_INDEXES = """
-- 🗄️ МИГРАЦИЯ 002: Создание индексов для производительности
-- Оптимизация запросов для высокой нагрузки

-- Индексы для таблицы пользователей
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_role_online ON users(role, is_online);
CREATE INDEX IF NOT EXISTS idx_users_zone_online ON users(zone, is_online);
CREATE INDEX IF NOT EXISTS idx_users_active_orders ON users(active_orders);
CREATE INDEX IF NOT EXISTS idx_users_performance ON users(performance_score DESC);

-- Индексы для таблицы клиентов
CREATE INDEX IF NOT EXISTS idx_clients_telegram_id ON clients(telegram_id);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_clients_zone ON clients(zone);
CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_clients_total_orders ON clients(total_orders DESC);

-- Индексы для таблицы заказов
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_operator_id ON orders(operator_id);
CREATE INDEX IF NOT EXISTS idx_orders_picker_id ON orders(picker_id);
CREATE INDEX IF NOT EXISTS idx_orders_checker_id ON orders(checker_id);
CREATE INDEX IF NOT EXISTS idx_orders_courier_id ON orders(courier_id);
CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_priority ON orders(priority DESC);
CREATE INDEX IF NOT EXISTS idx_orders_total_price ON orders(total_price);

-- Частичные индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_orders_status_created_partial ON orders(created_at) 
WHERE status IN ('created', 'waiting_payment', 'accepted');

CREATE INDEX IF NOT EXISTS idx_orders_worker_partial ON orders(picker_id) 
WHERE status IN ('picking', 'checking', 'ready');

-- Индексы для таблицы товаров в заказах
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_name ON order_items(product_name);
CREATE INDEX IF NOT EXISTS idx_order_items_requires_prescription ON order_items(requires_prescription);

-- Индексы для истории статусов
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_created_at ON order_status_history(created_at);
CREATE INDEX IF NOT EXISTS idx_order_status_history_changed_by ON order_status_history(changed_by);

-- Индексы для таблицы оплат
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(method);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);

-- Индексы для таблицы доставки
CREATE INDEX IF NOT EXISTS idx_delivery_order_id ON delivery(order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_courier_id ON delivery(courier_id);
CREATE INDEX IF NOT EXISTS idx_delivery_status ON delivery(status);
CREATE INDEX IF NOT EXISTS idx_delivery_created_at ON delivery(created_at);

-- Индексы для таблицы логов
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_client_id ON system_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_order_id ON system_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_action ON system_logs(action);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- Индексы для таблицы настроек
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
CREATE INDEX IF NOT EXISTS idx_settings_active ON settings(is_active);
"""

MIGRATION_003_CREATE_TRIGGERS = """
-- 🗄️ МИГРАЦИЯ 003: Создание триггеров для автоматического обновления
-- Автоматическое обновление временных меток

-- Функция для обновления updated_at в orders
CREATE OR REPLACE FUNCTION update_orders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Если статус изменился на delivered, устанавливаем completed_at
    IF OLD.status != 'delivered' AND NEW.status = 'delivered' THEN
        NEW.completed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы заказов
CREATE TRIGGER trigger_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();

-- Функция для обновления updated_at в users
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы пользователей
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Функция для обновления updated_at в clients
CREATE OR REPLACE FUNCTION update_clients_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы клиентов
CREATE TRIGGER trigger_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_clients_updated_at();

-- Функция для обновления updated_at в payments
CREATE OR REPLACE FUNCTION update_payments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы оплат
CREATE TRIGGER trigger_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_payments_updated_at();

-- Функция для обновления updated_at в delivery
CREATE OR REPLACE FUNCTION update_delivery_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы доставки
CREATE TRIGGER trigger_delivery_updated_at
    BEFORE UPDATE ON delivery
    FOR EACH ROW
    EXECUTE FUNCTION update_delivery_updated_at();

-- Функция для обновления updated_at в settings
CREATE OR REPLACE FUNCTION update_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для таблицы настроек
CREATE TRIGGER trigger_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_settings_updated_at();
"""

MIGRATION_004_CREATE_FUNCTIONS = """
-- 🗄️ МИГРАЦИЯ 004: Создание бизнес-функций
-- Функции для автоматического назначения сотрудников и аналитики

-- Функция для получения оптимального сотрудника
CREATE OR REPLACE FUNCTION get_optimal_worker(
    p_role TEXT,
    p_zone TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    telegram_id BIGINT,
    name TEXT,
    active_orders INTEGER,
    performance_score DECIMAL(3,2),
    zone TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.telegram_id,
        u.name,
        u.active_orders,
        u.performance_score,
        u.zone
    FROM users u
    WHERE u.role = p_role
    AND u.is_online = TRUE
    AND u.active_orders < u.max_orders
    AND (p_zone IS NULL OR u.zone = p_zone)
    ORDER BY 
        (u.active_orders * 2.0 - u.performance_score) ASC,
        u.last_assigned_at ASC NULLS LAST
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления нагрузки сотрудника
CREATE OR REPLACE FUNCTION update_worker_load(
    p_user_id INTEGER,
    p_delta INTEGER
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users 
    SET active_orders = GREATEST(active_orders + p_delta, 0),
        last_assigned_at = CASE 
            WHEN p_delta > 0 THEN NOW()
            ELSE last_assigned_at
        END
    WHERE id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Функция для создания заказа
CREATE OR REPLACE FUNCTION create_order(
    p_client_id INTEGER,
    p_total_price NUMERIC,
    p_zone TEXT,
    p_address TEXT,
    p_comment TEXT DEFAULT NULL,
    p_priority INTEGER DEFAULT 1
)
RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
BEGIN
    INSERT INTO orders (
        client_id, total_price, zone, address, comment, priority
    ) VALUES (
        p_client_id, p_total_price, p_zone, p_address, p_comment, p_priority
    ) RETURNING id INTO v_order_id;
    
    -- Обновляем статистику клиента
    UPDATE clients 
    SET total_orders = total_orders + 1,
        total_spent = total_spent + p_total_price
    WHERE id = p_client_id;
    
    -- Записываем в лог
    INSERT INTO system_logs (client_id, order_id, action, details)
    VALUES (p_client_id, v_order_id, 'order_created', 
            format('Order created with price %s', p_total_price));
    
    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления статуса заказа
CREATE OR REPLACE FUNCTION update_order_status(
    p_order_id INTEGER,
    p_new_status TEXT,
    p_changed_by INTEGER DEFAULT NULL,
    p_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_status TEXT;
    v_client_id INTEGER;
BEGIN
    -- Получаем текущий статус
    SELECT status, client_id INTO v_old_status, v_client_id
    FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Обновляем статус
    UPDATE orders 
    SET status = p_new_status
    WHERE id = p_order_id;
    
    -- Записываем в историю
    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, reason)
    VALUES (p_order_id, v_old_status, p_new_status, p_changed_by, p_reason);
    
    -- Записываем в лог
    INSERT INTO system_logs (user_id, client_id, order_id, action, details)
    VALUES (p_changed_by, v_client_id, p_order_id, 'status_changed', 
            format('Status changed from %s to %s', v_old_status, p_new_status));
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения статистики заказов
CREATE OR REPLACE FUNCTION get_order_statistics(
    p_date_from DATE DEFAULT CURRENT_DATE,
    p_date_to DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    date DATE,
    total_orders INTEGER,
    delivered_orders INTEGER,
    cancelled_orders INTEGER,
    total_revenue NUMERIC(12,2),
    avg_order_value NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(o.created_at) as date,
        COUNT(*) as total_orders,
        COUNT(*) FILTER (WHERE o.status = 'delivered') as delivered_orders,
        COUNT(*) FILTER (WHERE o.status IN ('rejected', 'cancelled')) as cancelled_orders,
        COALESCE(SUM(o.total_price), 0) as total_revenue,
        COALESCE(AVG(o.total_price), 0) as avg_order_value
    FROM orders o
    WHERE DATE(o.created_at) BETWEEN p_date_from AND p_date_to
    GROUP BY DATE(o.created_at)
    ORDER BY date;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения производительности сотрудника
CREATE OR REPLACE FUNCTION get_worker_performance(
    p_user_id INTEGER,
    p_date_from DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_date_to DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    total_orders INTEGER,
    completed_orders INTEGER,
    avg_completion_time_minutes NUMERIC,
    success_rate NUMERIC,
    total_revenue NUMERIC
) AS $$
DECLARE
    v_user_role TEXT;
BEGIN
    -- Получаем роль пользователя
    SELECT role INTO v_user_role FROM users WHERE id = p_user_id;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    RETURN QUERY
    SELECT 
        COUNT(*) as total_orders,
        COUNT(*) FILTER (WHERE o.status = 'delivered') as completed_orders,
        AVG(EXTRACT(EPOCH FROM (o.completed_at - o.created_at)) / 60) as avg_completion_time_minutes,
        (COUNT(*) FILTER (WHERE o.status = 'delivered')::NUMERIC / NULLIF(COUNT(*), 0)) * 100 as success_rate,
        COALESCE(SUM(o.total_price), 0) as total_revenue
    FROM orders o
    WHERE (
        (v_user_role = 'operator' AND o.operator_id = p_user_id) OR
        (v_user_role = 'picker' AND o.picker_id = p_user_id) OR
        (v_user_role = 'checker' AND o.checker_id = p_user_id) OR
        (v_user_role = 'courier' AND o.courier_id = p_user_id)
    )
    AND DATE(o.created_at) BETWEEN p_date_from AND p_date_to;
END;
$$ LANGUAGE plpgsql;
"""

MIGRATION_005_CREATE_VIEWS = """
-- 🗄️ МИГРАЦИЯ 005: Создание представлений для аналитики
-- Вью для удобного получения данных

-- Вью для активных заказов
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.id,
    o.client_id,
    c.name as client_name,
    c.phone as client_phone,
    c.telegram_id as client_telegram_id,
    o.status,
    o.total_price,
    o.delivery_price,
    o.zone,
    o.address,
    o.comment,
    o.priority,
    o.created_at,
    o.updated_at,
    o.estimated_time,
    o.actual_time,
    CASE 
        WHEN o.operator_id IS NOT NULL THEN u_op.name
        ELSE NULL
    END as operator_name,
    CASE 
        WHEN o.picker_id IS NOT NULL THEN u_pi.name
        ELSE NULL
    END as picker_name,
    CASE 
        WHEN o.checker_id IS NOT NULL THEN u_ch.name
        ELSE NULL
    END as checker_name,
    CASE 
        WHEN o.courier_id IS NOT NULL THEN u_co.name
        ELSE NULL
    END as courier_name
FROM orders o
LEFT JOIN clients c ON o.client_id = c.id
LEFT JOIN users u_op ON o.operator_id = u_op.id
LEFT JOIN users u_pi ON o.picker_id = u_pi.id
LEFT JOIN users u_ch ON o.checker_id = u_ch.id
LEFT JOIN users u_co ON o.courier_id = u_co.id
WHERE o.status NOT IN ('delivered', 'rejected', 'cancelled');

-- Вью для статистики сотрудников
CREATE OR REPLACE VIEW worker_performance AS
SELECT 
    u.id,
    u.name,
    u.role,
    u.zone,
    u.is_online,
    u.active_orders,
    u.max_orders,
    u.performance_score,
    u.last_assigned_at,
    COUNT(o.id) as total_orders,
    COUNT(o.id) FILTER (WHERE o.status = 'delivered') as delivered_orders,
    COUNT(o.id) FILTER (WHERE o.status IN ('rejected', 'cancelled')) as cancelled_orders,
    AVG(EXTRACT(EPOCH FROM (o.completed_at - o.created_at)) / 60) as avg_completion_time_minutes,
    (COUNT(*) FILTER (WHERE o.status = 'delivered')::NUMERIC / NULLIF(COUNT(*), 0)) * 100 as success_rate,
    COALESCE(SUM(o.total_price), 0) as total_revenue
FROM users u
LEFT JOIN orders o ON (
    (u.role = 'operator' AND o.operator_id = u.id) OR
    (u.role = 'picker' AND o.picker_id = u.id) OR
    (u.role = 'checker' AND o.checker_id = u.id) OR
    (u.role = 'courier' AND o.courier_id = u.id)
)
WHERE u.is_active = TRUE
GROUP BY u.id, u.name, u.role, u.zone, u.is_online, u.active_orders, u.max_orders, u.performance_score, u.last_assigned_at;

-- Вью для ежедневной статистики
CREATE OR REPLACE VIEW daily_statistics AS
SELECT 
    DATE(o.created_at) as date,
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE o.status = 'delivered') as delivered_orders,
    COUNT(*) FILTER (WHERE o.status IN ('rejected', 'cancelled')) as cancelled_orders,
    COUNT(*) FILTER (WHERE o.status = 'created') as created_orders,
    COUNT(*) FILTER (WHERE o.status = 'accepted') as accepted_orders,
    COUNT(*) FILTER (WHERE o.status = 'picking') as picking_orders,
    COUNT(*) FILTER (WHERE o.status = 'checking') as checking_orders,
    COUNT(*) FILTER (WHERE o.status = 'ready') as ready_orders,
    COUNT(*) FILTER (WHERE o.status = 'waiting_courier') as waiting_courier_orders,
    COUNT(*) FILTER (WHERE o.status = 'on_delivery') as on_delivery_orders,
    COALESCE(SUM(o.total_price), 0) as total_revenue,
    COALESCE(AVG(o.total_price), 0) as avg_order_value,
    COALESCE(AVG(o.actual_time), 0) as avg_completion_time_minutes
FROM orders o
GROUP BY DATE(o.created_at)
ORDER BY date DESC;

-- Вью для топ товаров
CREATE OR REPLACE VIEW top_products AS
SELECT 
    oi.product_name,
    COUNT(*) as order_count,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.total_price) as total_revenue,
    AVG(oi.price) as avg_price
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'delivered'
GROUP BY oi.product_name
ORDER BY total_revenue DESC;

-- Вью для статистики по зонам
CREATE OR REPLACE VIEW zone_statistics AS
SELECT 
    o.zone,
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE o.status = 'delivered') as delivered_orders,
    COUNT(*) FILTER (WHERE o.status IN ('rejected', 'cancelled')) as cancelled_orders,
    COALESCE(SUM(o.total_price), 0) as total_revenue,
    COALESCE(AVG(o.total_price), 0) as avg_order_value,
    COALESCE(AVG(o.actual_time), 0) as avg_completion_time_minutes
FROM orders o
GROUP BY o.zone
ORDER BY total_revenue DESC;
"""

MIGRATION_006_INSERT_INITIAL_DATA = """
-- 🗄️ МИГРАЦИЯ 006: Вставка начальных данных
-- Базовые настройки и демо-данные

-- Вставка базовых настроек
INSERT INTO settings (key, value, description) VALUES
('delivery_price_center', '15.00', 'Базовая цена доставки в центр'),
('delivery_price_other', '25.00', 'Базовая цена доставки в другие районы'),
('free_delivery_threshold', '100.00', 'Бесплатная доставка от суммы'),
('max_orders_per_worker', '5', 'Максимум заказов на сотрудника'),
('auto_assignment_enabled', 'true', 'Автоматическое назначение сотрудников'),
('notification_enabled', 'true', 'Уведомления включены'),
('business_hours_start', '09:00', 'Начало рабочего времени'),
('business_hours_end', '21:00', 'Конец рабочего времени'),
('currency', 'сомони', 'Валюта системы'),
('timezone', 'Asia/Dushanbe', 'Часовой пояс')
ON CONFLICT (key) DO NOTHING;

-- Вставка демо-сотрудников (если их нет)
INSERT INTO users (telegram_id, name, role, phone, zone, is_online, active_orders, max_orders, performance_score) VALUES
(697780123, 'Мухаммадмуссо', 'director', '+992900000001', 'центр', TRUE, 0, 10, 9.5),
(697780124, 'Али Оператор', 'operator', '+992900000002', 'центр', TRUE, 0, 5, 8.5),
(697780125, 'Рустам Сборщик', 'picker', '+992900000003', 'центр', TRUE, 0, 5, 9.0),
(697780126, 'Карим Сборщик', 'picker', '+992900000004', 'север', TRUE, 0, 5, 8.8),
(697780127, 'Бекзод Курьер', 'courier', '+992900000005', 'центр', TRUE, 0, 5, 9.2),
(697780128, 'Фарход Курьер', 'courier', '+992900000006', 'юг', TRUE, 0, 5, 8.7),
(697780129, 'Камол Проверщик', 'checker', '+992900000007', 'центр', TRUE, 0, 5, 9.1),
(697780130, 'Сардор Проверщик', 'checker', '+992900000008', 'восток', TRUE, 0, 5, 8.9)
ON CONFLICT (telegram_id) DO NOTHING;

-- Вставка демо-клиентов
INSERT INTO clients (telegram_id, name, phone, address, zone, is_active, total_orders, total_spent) VALUES
(697780131, 'Ахмад Клиент', '+992900000010', 'ул. Рудаки 45', 'центр', TRUE, 0, 0.00),
(697780132, 'Карим Клиент', '+992900000011', 'ул. Айни 12', 'север', TRUE, 0, 0.00),
(697780133, 'Фарход Клиент', '+992900000012', 'ул. Бохтар 23', 'юг', TRUE, 0, 0.00)
ON CONFLICT (telegram_id) DO NOTHING;

-- Запись в системный лог о миграции
INSERT INTO system_logs (action, details, level) VALUES
('migration_completed', 'Database schema migration 001-006 completed successfully', 'info');
"""

# Список всех миграций
MIGRATIONS = [
    MIGRATION_001_CREATE_TABLES,
    MIGRATION_002_CREATE_INDEXES,
    MIGRATION_003_CREATE_TRIGGERS,
    MIGRATION_004_CREATE_FUNCTIONS,
    MIGRATION_005_CREATE_VIEWS,
    MIGRATION_006_INSERT_INITIAL_DATA
]

def get_migration_sql(migration_number: int = None) -> str:
    """Получение SQL для конкретной миграции или всех миграций"""
    if migration_number:
        if 1 <= migration_number <= len(MIGRATIONS):
            return MIGRATIONS[migration_number - 1]
        else:
            raise ValueError(f"Migration number {migration_number} not found")
    else:
        return "\n".join(MIGRATIONS)

def print_all_migrations():
    """Вывод всех миграций"""
    print("🗄️ MAXXPHARM CRM DATABASE MIGRATIONS")
    print("=" * 60)
    
    for i, migration in enumerate(MIGRATIONS, 1):
        print(f"\n📋 МИГРАЦИЯ 00{i}:")
        print(migration)
        print("\n" + "-" * 60)

if __name__ == "__main__":
    print_all_migrations()
