-- ===============================
-- TELEGRAM PHARMA CRM DATABASE
-- MAXXPHARM Telegram CRM - Production Ready
-- aiogram + PostgreSQL + Render Compatible
-- Workflow: Клиент → Оператор → Сборщик → Проверщик → Курьер → Доставка
-- ===============================

-- Создание базы данных (если нужно)
-- CREATE DATABASE pharma_crm;
-- \c pharma_crm;

-- ===============================
-- 1️⃣ USERS (Сотрудники)
-- ===============================
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
    performance_score DECIMAL(3,2) DEFAULT 5.0,
    last_assigned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- 2️⃣ CLIENTS (Клиенты)
-- ===============================
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

-- ===============================
-- 3️⃣ ORDERS (Заказы - главная таблица)
-- ===============================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'created' CHECK (status IN (
        'created',           -- Создан
        'waiting_payment',  -- Ожидает оплаты
        'accepted',         -- Принят оператором
        'picking',          -- В сборке
        'checking',         -- На проверке
        'ready',            -- Готов
        'waiting_courier', -- Ожидает курьера
        'on_delivery',      -- В доставке
        'delivered',        -- Доставлен
        'rejected',         -- Отклонен
        'cancelled'         -- Отменен
    )),
    operator_id INTEGER REFERENCES users(id),
    picker_id INTEGER REFERENCES users(id),
    checker_id INTEGER REFERENCES users(id),
    courier_id INTEGER REFERENCES users(id),
    zone TEXT CHECK (zone IN ('центр', 'север', 'юг', 'восток', 'запад')),
    address TEXT NOT NULL,
    total_price NUMERIC(12,2) DEFAULT 0.00,
    delivery_price NUMERIC(8,2) DEFAULT 0.00,
    comment TEXT,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    estimated_time INTEGER, -- в минутах
    actual_time INTEGER, -- в минутах
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- ===============================
-- 4️⃣ ORDER_ITEMS (Товары в заказах)
-- ===============================
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

-- ===============================
-- 5️⃣ ORDER_STATUS_HISTORY (История статусов заказа)
-- ===============================
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by INTEGER REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- 6️⃣ PAYMENTS (Оплаты)
-- ===============================
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    method TEXT NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'terminal', 'online', 'crypto')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'failed', 'refunded')),
    proof_photo TEXT, -- file_id фото чека
    transaction_id TEXT,
    confirmed_by INTEGER REFERENCES users(id),
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- 7️⃣ DELIVERY (Доставка)
-- ===============================
CREATE TABLE IF NOT EXISTS delivery (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    courier_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL CHECK (status IN ('assigned', 'picked_up', 'on_way', 'delivered', 'failed')),
    pickup_time TIMESTAMP,
    delivery_time TIMESTAMP,
    actual_distance NUMERIC(8,2), -- в километрах
    delivery_notes TEXT,
    client_rating INTEGER CHECK (client_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- 8️⃣ SYSTEM_LOGS (Системные логи)
-- ===============================
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

-- ===============================
-- 9️⃣ SETTINGS (Настройки системы)
-- ===============================
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- 🔥 INDEXES FOR PERFORMANCE
-- ===============================

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_role_online ON users(role, is_online);
CREATE INDEX IF NOT EXISTS idx_users_zone_online ON users(zone, is_online);
CREATE INDEX IF NOT EXISTS idx_users_active_orders ON users(active_orders);

-- Индексы для clients
CREATE INDEX IF NOT EXISTS idx_clients_telegram_id ON clients(telegram_id);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_clients_zone ON clients(zone);
CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active);

-- Индексы для orders
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_operator_id ON orders(operator_id);
CREATE INDEX IF NOT EXISTS idx_orders_picker_id ON orders(picker_id);
CREATE INDEX IF NOT EXISTS idx_orders_checker_id ON orders(checker_id);
CREATE INDEX IF NOT EXISTS idx_orders_courier_id ON orders(courier_id);
CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);

-- Индексы для order_items
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_name ON order_items(product_name);

-- Индексы для order_status_history
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_created_at ON order_status_history(created_at);

-- Индексы для payments
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(method);

-- Индексы для delivery
CREATE INDEX IF NOT EXISTS idx_delivery_order_id ON delivery(order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_courier_id ON delivery(courier_id);
CREATE INDEX IF NOT EXISTS idx_delivery_status ON delivery(status);

-- Индексы для system_logs
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_client_id ON system_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_order_id ON system_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_action ON system_logs(action);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- Индексы для settings
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
CREATE INDEX IF NOT EXISTS idx_settings_active ON settings(is_active);

-- ===============================
-- 🧠 TRIGGERS FOR AUTOMATIC UPDATES
-- ===============================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для всех таблиц с updated_at
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_delivery_updated_at
    BEFORE UPDATE ON delivery
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===============================
-- 🔧 USEFUL FUNCTIONS
-- ===============================

-- Функция для получения оптимального сотрудника
CREATE OR REPLACE FUNCTION get_optimal_worker(p_role TEXT, p_zone TEXT DEFAULT NULL)
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
CREATE OR REPLACE FUNCTION update_worker_load(p_user_id INTEGER, p_delta INTEGER)
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

-- ===============================
-- 📊 VIEWS FOR ANALYTICS
-- ===============================

-- Вью для активных заказов
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.id,
    o.client_id,
    c.name as client_name,
    c.phone as client_phone,
    o.status,
    o.total_price,
    o.zone,
    o.address,
    o.created_at,
    o.updated_at,
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

-- ===============================
-- 📋 DEFAULT DATA
-- ===============================

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

-- Вставка директора (если его нет)
INSERT INTO users (telegram_id, name, role, phone, zone, is_online, active_orders, max_orders, performance_score) VALUES
(697780123, 'Мухаммадмуссо', 'director', '+992900000001', 'центр', TRUE, 0, 10, 9.5)
ON CONFLICT (telegram_id) DO NOTHING;

-- ===============================
-- ✅ COMPLETION MESSAGE
-- ===============================

-- Вывод сообщения о завершении
DO $$
BEGIN
    RAISE NOTICE '✅ MAXXPHARM CRM Database created successfully!';
    RAISE NOTICE '📊 Tables: users, clients, orders, order_items, order_status_history, payments, delivery, system_logs, settings';
    RAISE NOTICE '🔥 Indexes created for performance';
    RAISE NOTICE '🧠 Triggers and functions ready';
    RAISE NOTICE '📋 Default data inserted';
    RAISE NOTICE '🚀 Database ready for aiogram bot!';
END $$;
