# гоночный сайт по Формуле 1

## Стек

- **FastAPI** + Uvicorn — веб-фреймворк
- **SQLAlchemy 2.0** (async) + Alembic — ORM и миграции
- **PostgreSQL** через asyncpg / aiosqlite для тестов
- **fastapi-users** — регистрация и JWT-авторизация
- **Pydantic v2** + pydantic-settings — валидация и конфигурация
- **pytest** + pytest-asyncio + pytest-cov — тесты с покрытием
- **Sentry SDK** — мониторинг ошибок

## Структура

```
testfastapi/
├── api/           # роутеры
├── src/           # модели, сервисы, бизнес-логика
├── migrations/    # alembic-миграции
├── tests/         # тесты
├── index.html     # фронтенд
├── alembic.ini
└── requirements.txt
```

## Установка

```bash
pip install -r requirements.txt
```

Создай `.env` в корне и укажи переменные окружения:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET=your_secret_key
```

## Миграции

```bash
alembic upgrade head
```

## Запуск

```bash
uvicorn src.main:app --reload
```

После старта документация доступна по адресу `http://localhost:8000/docs`.

## Тесты

```bash
pytest --cov=src tests/
```

## API

Авторизация реализована через fastapi-users, основные маршруты:

- `POST /auth/register` — регистрация
- `POST /auth/jwt/login` — вход, возвращает JWT
- `POST /auth/jwt/logout` — выход
