-- Инициализация базы данных SafeWorkHub
-- Выполняется при первом запуске контейнера PostgreSQL

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Создаём конфигурацию полнотекстового поиска для русского языка
-- (используется встроенная russian конфигурация)

-- Примечание: основные таблицы создаются через Alembic миграции.
-- Этот файл используется только для начальной настройки расширений
-- и любых специфичных конфигураций PostgreSQL.

-- Создаём функцию для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Примечание: триггеры для таблиц создаются в миграциях Alembic
