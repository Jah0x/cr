# Backend

1. Скопируйте `.env.example` в `.env` и задайте `DATABASE_URL` (postgresql+asyncpg), `JWT_SECRET`, `JWT_EXPIRES`, `OWNER_EMAIL`, `OWNER_PASSWORD`, `CASH_REGISTER_PROVIDER`.
2. Установите зависимости: `poetry install`.
3. Примените миграции: `poetry run alembic upgrade head`.
4. Стартуйте API: `poetry run uvicorn app.main:app --reload`.

Docker: `docker-compose up --build backend` поднимет Postgres и API, переменные окружения задаются в `.env`.

Bootstrap владельца: при старте приложения, если нет пользователя с ролью owner и заданы `OWNER_EMAIL`/`OWNER_PASSWORD`, создаётся владелец и роль. Повторный запуск не создаёт новых пользователей.

Аутентификация: авторизация обязательна на всех маршрутах кроме `/api/v1/health` и `/healthz`. Получите токен: `curl -X POST http://localhost:8000/api/v1/auth/login -d '{"email":"owner@example.com","password":"..."}' -H 'Content-Type: application/json'`. Используйте заголовок `Authorization: Bearer <token>`.

Продажи: `POST /api/v1/sales` принимает массив позиций `{product_id, qty, unit_price?}`, списывает склад и создаёт чек через выбранный провайдер кассы. `POST /api/v1/sales/{id}/void` доступен ролям owner/admin и возвращает товар на склад.

Модульная касса: провайдер выбирается через `CASH_REGISTER_PROVIDER` (по умолчанию mock) и реализует интерфейс в `app/services/cash_register/base.py`. Добавление нового провайдера: создать класс провайдера и расширить фабрику `get_cash_register`.
