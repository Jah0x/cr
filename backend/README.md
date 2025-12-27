# Backend

1. Скопируйте `.env.example` в `.env` и задайте минимум `DATABASE_URL` (postgresql+asyncpg), `JWT_SECRET`, `JWT_EXPIRES`, `FIRST_OWNER_EMAIL`, `FIRST_OWNER_PASSWORD`, `CASH_REGISTER_PROVIDER`.
2. Установите зависимости: `poetry install`.
3. Примените миграции: `poetry run alembic upgrade head`.
4. Стартуйте API: `poetry run uvicorn app.main:app --reload`.

Docker: `docker-compose up --build backend` поднимет Postgres и API, переменные окружения задаются в `.env`.

Bootstrap владельца: при старте приложения, если таблица пользователей пуста и заданы `FIRST_OWNER_EMAIL`/`FIRST_OWNER_PASSWORD`, создаётся владелец и роли. Повторный запуск не создаёт новых пользователей. Одновременно создаётся активная касса типа `CASH_REGISTER_PROVIDER`, если касс ещё нет.

Аутентификация: обязательна на всех маршрутах кроме `/api/v1/health` и `/healthz`. Получите токен: `curl -X POST http://localhost:8000/api/v1/auth/login -d '{"email":"owner@example.com","password":"..."}' -H 'Content-Type: application/json'`. Используйте заголовок `Authorization: Bearer <token>`.

Роли и права: owner управляет пользователями и кассами; admin отвечает за каталог, склад, закупки; cashier проводит продажи. Маршруты валидируются через `require_roles` в `app/core/deps.py`.

Продажи: `POST /api/v1/sales` принимает позиции и платежи, списывает склад, фиксирует платежи и создаёт чек через выбранный провайдер кассы. `POST /api/v1/sales/{id}/refunds` оформляет возвраты, `POST /api/v1/sales/{id}/void` возвращает товар на склад и помечает продажу void.

Модульная касса: провайдер выбирается через `CASH_REGISTER_PROVIDER` или активную запись `cash_registers`. Добавление нового провайдера: реализовать интерфейс в `app/services/cash_register/base.py` и расширить фабрику `get_cash_register`.
