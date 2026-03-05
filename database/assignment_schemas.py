"""
🧠 Auto-Assignment SQL Schema - SQL схемы для системы автоматического распределения
"""

# SQL для создания таблиц с поддержкой Auto-Assignment

# Таблица пользователей с полями для распределения
CREATE_USERS_TABLE = """
-- Расширенная таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    role VARCHAR(50) NOT NULL,  -- client, operator, picker, checker, courier, admin, director
    is_active BOOLEAN DEFAULT true,
    is_online BOOLEAN DEFAULT false,
    zone VARCHAR(50),  -- Район работы (центр, север, юг, восток, запад)
    active_orders INTEGER DEFAULT 0,  -- Текущая нагрузка
    max_orders INTEGER DEFAULT 5,  -- Максимальная нагрузка
    last_assigned_at TIMESTAMP,  -- Время последнего назначения
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Индексы для оптимизации
    CONSTRAINT users_role_check CHECK (role IN ('client', 'operator', 'picker', 'checker', 'courier', 'admin', 'director'))
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, is_online);
CREATE INDEX IF NOT EXISTS idx_users_zone ON users(zone);
CREATE INDEX IF NOT EXISTS idx_users_load ON users(active_orders);
CREATE INDEX IF NOT EXISTS idx_users_role_zone_load ON users(role, zone, active_orders);
"""

# Расширенная таблица заказов
CREATE_ORDERS_TABLE = """
-- Расширенная таблица заказов с поддержкой Auto-Assignment
CREATE TABLE IF NOT EXISTS orders (
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
    
    -- Поля для Auto-Assignment
    zone VARCHAR(50),  -- Район доставки
    priority INTEGER DEFAULT 1,  -- Приоритет заказа (1-5)
    
    -- Временные метки назначения
    operator_assigned_at TIMESTAMP,
    picker_assigned_at TIMESTAMP,
    checker_assigned_at TIMESTAMP,
    courier_assigned_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER REFERENCES users(id),
    
    rejection_reason TEXT,
    payment_confirmed_at TIMESTAMP,
    payment_confirmed_by INTEGER REFERENCES users(id),
    
    completed_at TIMESTAMP,  -- Время завершения заказа
    
    CONSTRAINT orders_status_check CHECK (
        status IN ('created', 'waiting_payment', 'accepted', 'processing', 'ready', 'checking', 'waiting_courier', 'on_way', 'delivered', 'cancelled')
    ),
    CONSTRAINT orders_priority_check CHECK (priority BETWEEN 1 AND 5)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
CREATE INDEX IF NOT EXISTS idx_orders_priority ON orders(priority DESC);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_picker_id ON orders(picker_id) WHERE picker_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_checker_id ON orders(checker_id) WHERE checker_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_courier_id ON orders(courier_id) WHERE courier_id IS NOT NULL;
"""

# Таблица истории назначений
CREATE_ASSIGNMENT_HISTORY_TABLE = """
-- История назначений для аналитики
CREATE TABLE IF NOT EXISTS assignment_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    worker_id INTEGER REFERENCES users(id),
    worker_role VARCHAR(50),
    assigned_at TIMESTAMP DEFAULT NOW(),
    released_at TIMESTAMP,
    assignment_duration_minutes INTEGER,  -- Сколько минут работал над заказом
    
    -- Метрики для AI оптимизации
    worker_load_before INTEGER,  -- Нагрузка до назначения
    worker_load_after INTEGER,   -- Нагрузка после назначения
    zone_match BOOLEAN,          -- Совпадение зоны
    auto_assigned BOOLEAN DEFAULT true  -- Автоматически или вручную
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_assignment_history_order_id ON assignment_history(order_id);
CREATE INDEX IF NOT EXISTS idx_assignment_history_worker_id ON assignment_history(worker_id);
CREATE INDEX IF NOT EXISTS idx_assignment_history_assigned_at ON assignment_history(assigned_at);
"""

# Таблица зон доставки
CREATE_ZONES_TABLE = """
-- Зоны доставки для оптимизации
CREATE TABLE IF NOT EXISTS delivery_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- центр, север, юг, восток, запад
    description TEXT,
    base_delivery_time INTEGER DEFAULT 30,  -- Базовое время доставки в минутах
    priority_multiplier DECIMAL(2,1) DEFAULT 1.0,  -- Множитель приоритета
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Заполняем зоны
INSERT INTO delivery_zones (name, description, base_delivery_time) VALUES
('центр', 'Центральный район города', 30),
('север', 'Северный район города', 45),
('юг', 'Южный район города', 40),
('восток', 'Восточный район города', 35),
('запад', 'Западный район города', 35)
ON CONFLICT (name) DO NOTHING;
"""

# Таблица производительности работников
CREATE_WORKER_PERFORMANCE_TABLE = """
-- Таблица производительности работников для AI оптимизации
CREATE TABLE IF NOT EXISTS worker_performance (
    id SERIAL PRIMARY KEY,
    worker_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    role VARCHAR(50) NOT NULL,
    
    -- Метрики производительности
    orders_completed INTEGER DEFAULT 0,
    avg_order_time_minutes DECIMAL(8,2),  -- Среднее время на заказ
    total_revenue DECIMAL(12,2),  -- Общая выручка
    
    -- Метрики качества
    quality_score DECIMAL(3,2) DEFAULT 5.0,  -- Оценка качества (1-10)
    customer_rating DECIMAL(3,2) DEFAULT 5.0,  -- Оценка клиентов
    
    -- Эффективность
    efficiency_score DECIMAL(5,2),  -- Рассчитанный показатель эффективности
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(worker_id, date, role)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_worker_performance_worker_id ON worker_performance(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_performance_date ON worker_performance(date);
CREATE INDEX IF NOT EXISTS idx_worker_performance_efficiency ON worker_performance(efficiency_score DESC);
"""

# Представление для быстрого получения оптимальных работников
CREATE_OPTIMAL_WORKERS_VIEW = """
-- Представление для получения оптимальных работников
CREATE OR REPLACE VIEW optimal_workers AS
SELECT 
    u.id,
    u.telegram_id,
    u.name,
    u.role,
    u.zone,
    u.active_orders,
    u.max_orders,
    u.is_online,
    u.last_assigned_at,
    
    -- Рассчитываем score (чем меньше, тем лучше)
    CASE 
        WHEN u.last_assigned_at IS NULL THEN 0
        ELSE (u.active_orders * 2) - (EXTRACT(EPOCH FROM (NOW() - u.last_assigned_at)) / 60)
    END as assignment_score,
    
    -- Доступность (true если есть место для новых заказов)
    (u.active_orders < u.max_orders) as is_available,
    
    -- Время с последнего назначения в минутах
    CASE 
        WHEN u.last_assigned_at IS NULL THEN 999
        ELSE EXTRACT(EPOCH FROM (NOW() - u.last_assigned_at)) / 60
    END as minutes_since_last_assignment
    
FROM users u
WHERE u.is_active = true
AND u.is_online = true
AND u.role IN ('picker', 'checker', 'courier')
ORDER BY assignment_score ASC, minutes_since_last_assignment DESC;
"""

# Функция для автоматического распределения
CREATE_AUTO_ASSIGN_FUNCTION = """
-- Функция для автоматического распределения заказа
CREATE OR REPLACE FUNCTION auto_assign_order(p_order_id INTEGER, p_zone VARCHAR(50) DEFAULT NULL)
RETURNS BOOLEAN AS $$
DECLARE
    v_order_status VARCHAR(50);
    v_assigned_worker_id INTEGER;
    v_assigned_worker_role VARCHAR(50);
    v_success BOOLEAN := FALSE;
BEGIN
    -- Получаем статус заказа
    SELECT status INTO v_order_status FROM orders WHERE id = p_order_id;
    
    IF v_order_status = 'accepted' THEN
        -- Назначаем сборщика
        SELECT id INTO v_assigned_worker_id
        FROM optimal_workers
        WHERE role = 'picker'
        AND (zone = p_zone OR p_zone IS NULL)
        AND is_available = true
        LIMIT 1;
        
        IF v_assigned_worker_id IS NOT NULL THEN
            UPDATE orders 
            SET picker_id = v_assigned_worker_id,
                status = 'processing',
                picker_assigned_at = NOW(),
                updated_at = NOW()
            WHERE id = p_order_id;
            
            -- Увеличиваем нагрузку
            UPDATE users 
            SET active_orders = active_orders + 1,
                last_assigned_at = NOW()
            WHERE id = v_assigned_worker_id;
            
            -- Записываем в историю
            INSERT INTO assignment_history (order_id, worker_id, worker_role, auto_assigned)
            VALUES (p_order_id, v_assigned_worker_id, 'picker', true);
            
            v_success := TRUE;
            v_assigned_worker_role := 'picker';
        END IF;
        
    ELSIF v_order_status = 'ready' THEN
        -- Назначаем проверщика
        SELECT id INTO v_assigned_worker_id
        FROM optimal_workers
        WHERE role = 'checker'
        AND is_available = true
        LIMIT 1;
        
        IF v_assigned_worker_id IS NOT NULL THEN
            UPDATE orders 
            SET checker_id = v_assigned_worker_id,
                status = 'checking',
                checker_assigned_at = NOW(),
                updated_at = NOW()
            WHERE id = p_order_id;
            
            -- Увеличиваем нагрузку
            UPDATE users 
            SET active_orders = active_orders + 1,
                last_assigned_at = NOW()
            WHERE id = v_assigned_worker_id;
            
            -- Записываем в историю
            INSERT INTO assignment_history (order_id, worker_id, worker_role, auto_assigned)
            VALUES (p_order_id, v_assigned_worker_id, 'checker', true);
            
            v_success := TRUE;
            v_assigned_worker_role := 'checker';
        END IF;
        
    ELSIF v_order_status = 'waiting_courier' THEN
        -- Назначаем курьера
        SELECT id INTO v_assigned_worker_id
        FROM optimal_workers
        WHERE role = 'courier'
        AND (zone = p_zone OR p_zone IS NULL)
        AND is_available = true
        LIMIT 1;
        
        IF v_assigned_worker_id IS NOT NULL THEN
            UPDATE orders 
            SET courier_id = v_assigned_worker_id,
                status = 'on_way',
                courier_assigned_at = NOW(),
                updated_at = NOW()
            WHERE id = p_order_id;
            
            -- Увеличиваем нагрузку
            UPDATE users 
            SET active_orders = active_orders + 1,
                last_assigned_at = NOW()
            WHERE id = v_assigned_worker_id;
            
            -- Записываем в историю
            INSERT INTO assignment_history (order_id, worker_id, worker_role, auto_assigned)
            VALUES (p_order_id, v_assigned_worker_id, 'courier', true);
            
            v_success := TRUE;
            v_assigned_worker_role := 'courier';
        END IF;
    END IF;
    
    RETURN v_success;
END;
$$ LANGUAGE plpgsql;
"""

# Функция для освобождения работника
CREATE_RELEASE_WORKER_FUNCTION = """
-- Функция для освобождения работника от нагрузки
CREATE OR REPLACE FUNCTION release_worker(p_worker_id INTEGER, p_role VARCHAR(50))
RETURNS VOID AS $$
BEGIN
    -- Уменьшаем нагрузку
    UPDATE users 
    SET active_orders = GREATEST(active_orders - 1, 0)
    WHERE id = p_worker_id AND role = p_role;
    
    -- Завершаем последнюю запись в истории
    UPDATE assignment_history 
    SET released_at = NOW(),
        assignment_duration_minutes = EXTRACT(EPOCH FROM (NOW() - assigned_at)) / 60
    WHERE worker_id = p_worker_id
    AND worker_role = p_role
    AND released_at IS NULL
    ORDER BY assigned_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
"""

# Триггер для автоматического распределения
CREATE_AUTO_ASSIGN_TRIGGER = """
-- Триггер для автоматического распределения при изменении статуса
CREATE OR REPLACE FUNCTION trigger_auto_assign()
RETURNS TRIGGER AS $$
BEGIN
    -- Если статус изменился на тот, который требует назначения
    IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        IF NEW.status = 'accepted' OR NEW.status = 'ready' OR NEW.status = 'waiting_courier' THEN
            PERFORM auto_assign_order(NEW.id, NEW.zone);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер
DROP TRIGGER IF EXISTS auto_assign_trigger ON orders;
CREATE TRIGGER auto_assign_trigger
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION trigger_auto_assign();
"""

# Все SQL схемы вместе
ALL_SQL_SCHEMAS = [
    CREATE_USERS_TABLE,
    CREATE_ORDERS_TABLE,
    CREATE_ASSIGNMENT_HISTORY_TABLE,
    CREATE_ZONES_TABLE,
    CREATE_WORKER_PERFORMANCE_TABLE,
    CREATE_OPTIMAL_WORKERS_VIEW,
    CREATE_AUTO_ASSIGN_FUNCTION,
    CREATE_RELEASE_WORKER_FUNCTION,
    CREATE_AUTO_ASSIGN_TRIGGER
]
