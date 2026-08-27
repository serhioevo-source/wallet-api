# Wallet API

REST API для работы с балансом кошельков пользователей.

Проект реализован в рамках тестового задания на Python Developer.

## Возможности

- получение текущего баланса кошелька;
- пополнение баланса (`DEPOSIT`);
- списание средств (`WITHDRAW`);
- защита от отрицательного баланса;
- корректная обработка конкурентных операций над одним кошельком;
- опциональная идемпотентность через заголовок `Idempotency-Key`;
- сохранение истории операций;
- миграции базы данных;
- автоматические API и concurrency-тесты.

## Стек

- Python 3.13
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2 Async
- asyncpg
- Alembic
- Pydantic
- pytest
- HTTPX
- Ruff
- Docker
- Docker Compose

## Запуск

Создать локальный файл окружения:

    cp .env.example .env

Запустить приложение и PostgreSQL:

    docker compose up --build -d

При старте приложения миграции Alembic применяются автоматически.

Проверить контейнеры:

    docker compose ps

API:

    http://localhost:8000

Swagger UI:

    http://localhost:8000/docs

Health check:

    http://localhost:8000/health

## API

### Получение баланса

    GET /api/v1/wallets/{wallet_uuid}

Пример ответа:

    {
      "wallet_uuid": "7e071d90-87b8-4499-8867-30e05406b418",
      "balance": 10000
    }

### Изменение баланса

    POST /api/v1/wallets/{wallet_uuid}/operation

Пополнение:

    {
      "operation_type": "DEPOSIT",
      "amount": 1000
    }

Списание:

    {
      "operation_type": "WITHDRAW",
      "amount": 500
    }

Дополнительно поддерживается необязательный HTTP-заголовок:

    Idempotency-Key: <unique-key>

Повтор запроса с тем же ключом и теми же параметрами не изменяет баланс повторно.

## Конкурентность

Изменение баланса выполняется внутри транзакции PostgreSQL.

Для конкурентных операций над одним кошельком используется блокировка строки `SELECT ... FOR UPDATE`.

Это предотвращает lost update и некорректное двойное списание при одновременных запросах.

На уровне PostgreSQL дополнительно используются ограничения `CHECK`, `FOREIGN KEY` и `UNIQUE`.

## Миграции

Для управления схемой базы данных используется Alembic.

При старте приложения автоматически выполняется:

    alembic upgrade head

Миграция создаёт таблицы:

- `wallets`
- `wallet_operations`

## Тесты

Запуск:

    docker compose exec app pytest -v

Тесты проверяют:

- получение существующего кошелька;
- отсутствующий кошелёк;
- `DEPOSIT`;
- `WITHDRAW`;
- недостаточный баланс;
- валидацию входных данных;
- последовательную идемпотентность;
- конфликт `Idempotency-Key`;
- конкурентную идемпотентность;
- конкурентные пополнения;
- конкурентные списания без овердрафта.

## Проверка качества кода

    docker compose exec app ruff check .
    docker compose exec app ruff format --check .

## Остановка

    docker compose down

Для удаления также локального Docker volume с базой:

    docker compose down -v
