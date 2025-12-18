# Runbook SafeWorkHub

Документ для дежурных инженеров: как диагностировать и восстанавливать сервис.

## Старт/остановка окружения

- Локально через Docker Compose: `make up` / `make down`.
- Применение миграций: `docker compose exec backend alembic upgrade head`.
- Пересборка образов: `docker compose build backend frontend`.

## Миграции БД

- Применить: `cd backend && .venv/bin/alembic upgrade head` (локально) или `docker compose exec backend alembic upgrade head`.
- Откат на предыдущую версию: `alembic downgrade -1`.
- При ошибке миграции: зафиксировать лог, выполнить `alembic history` и согласовать план отката, восстановить из бэкапа перед повтором.

## Резервное копирование и восстановление PostgreSQL

- Бэкап: `docker compose exec postgres pg_dump -U safeworkhub -d safeworkhub > backup.sql`.
- Восстановление: `cat backup.sql | docker compose exec -T postgres psql -U safeworkhub -d safeworkhub`.
- Для тестовой БД используйте `safeworkhub_test` и отдельные креды из `.env.example`.

## Диагностика

- Health: `GET /api/v1/health` (liveness), `GET /api/v1/ready` (readiness).
- Метрики: `GET /metrics` (Prometheus).
- Проверка авторизации: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh` (cookie httpOnly), `GET /api/v1/users/me`.
- Логи backend: `docker compose logs backend --tail 200`.
- Логи frontend/nginx: `docker compose logs frontend --tail 200`.
- Проверка Redis: `docker compose exec redis redis-cli ping`.
- Проверка БД: `docker compose exec postgres pg_isready -U safeworkhub -d safeworkhub`.

## Типовые инциденты

- **БД недоступна**: проверить health postgres, при необходимости перезапустить контейнер, восстановить из бэкапа, повторить миграции.
- **Проблемы с авторизацией**: очистить cookie refresh (`swh_refresh_token`), повторить логин; убедиться, что SECRET_KEY и домены cookie совпадают с окружением.
- **Ошибки сборки фронтенда**: убедиться, что `VITE_API_URL` указывает на `/api/v1`, заново выполнить `npm ci && npm run build`.
- **Медленные запросы/таймауты**: проверить Redis/БД, метрики `/metrics`, поискать N+1 через логирование SQL (включить `DATABASE_ECHO=true` временно).
- **Неприменённые миграции**: запустить `alembic upgrade head`, сверить версию в таблице `alembic_version`.

## Контакты

- Ответственный: Yan Bubenok (yan@bubenok.com, Telegram: @iBubenok).
