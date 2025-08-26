-- psql -U ecom_superadmin -d ml_db -h localhost -f tools/init_schema.sql

-- tools/init_schema.sql

-- Таблица продаж
CREATE TABLE IF NOT EXISTS sales (
    order_id    INT,
    customer_id INT,
    order_date  TEXT,
    amount      DOUBLE PRECISION
);

-- Таблица клиентов/стран
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    country     TEXT
);

-- Таблица метрик отчётов
CREATE TABLE IF NOT EXISTS report_metrics (
    metric TEXT,
    value  TEXT
);

-- Индексы для ускорения join/агрегации
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_customers_country   ON customers(country);

-- ML метрики
CREATE TABLE IF NOT EXISTS ml_metrics (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ML модели (метаданные)
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT,
    artifact_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
