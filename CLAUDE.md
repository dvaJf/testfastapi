# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI application for F1 race management with user authentication, race registration, results tracking, and organizer reviews. Supports Discord OAuth login.

## Tech Stack

- **Framework**: FastAPI with uvicorn
- **Database**: SQLAlchemy 2.0 (async) with asyncpg (PostgreSQL) or aiosqlite (development)
- **Auth**: fastapi-users with JWT tokens, Discord OAuth support
- **Password hashing**: pwdlib with bcrypt/argon2
- **Testing**: pytest with pytest-asyncio and httpx AsyncClient

## Project Structure

```
src/
├── main.py              # FastAPI app, lifespan, middleware, page routes
├── config.py            # Pydantic Settings (env-based)
├── database.py          # SQLAlchemy async engine, session factory, Base
├── exceptions.py        # Custom HTTP exceptions (NotFound, Forbidden, BadRequest)
├── auth/
│   ├── models.py        # User model (extends SQLAlchemyBaseUserTable)
│   ├── router.py        # Auth routes + Discord OAuth flow
│   ├── schemas.py       # UserRead, UserCreate, UserUpdate
│   ├── service.py       # fastapi-users setup (UserManager, auth_backend)
│   ├── config.py        # JWT secret, token expiry
│   └── utils.py         # create_first_admin helper
├── races/
│   ├── models.py        # Race, RaceResult, OrganizerReview
│   ├── router.py        # /api/races endpoints
│   ├── schemas.py       # Pydantic schemas (RaceCreate, RaceOut, etc.)
│   └── service.py       # Business logic, scoring system
├── news/
│   ├── models.py
│   ├── router.py
│   ├── schemas.py
│   └── service.py
└── leaderboard/
    ├── router.py
    ├── schemas.py
    └── service.py
```

Each feature module follows the same pattern: models (SQLAlchemy) → schemas (Pydantic) → service (business logic) → router (HTTP endpoints).

## Common Commands

```bash
# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
pytest

# Run a single test file
pytest tests/test_races.py

# Run a specific test
pytest tests/test_races.py::test_create_race

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Install dependencies
pip install -r requirements.txt

# Docker build and run
docker build -t f1u .
docker run -p 8000:8000 --env-file .env f1u
```

## Architecture Notes

- **Database sessions**: Use `get_session` dependency (async generator) in routers. Test fixtures override this with `test_session_maker`.
- **Auth**: `fastapi_users.current_user()` dependency for protected routes. Check `user.is_verified` and `user.is_superuser` for permissions.
- **Scoring**: Position-based points in `races/service.py` (1st=60pts, 2nd=55pts... DNF/DNS negative). Scores awarded when `set_results` is called, with rollback support for updates.
- **Race status flow**: "Регистрация" → (active) → "Завершена". Registration/unregistration only in "Регистрация" status.
- **Organizer reviews**: Users who participated can rate organizers (vote=1 like, -1 dislike) after race completes.
- **Frontend**: Static HTML files served from `frontend/` directory. Discord OAuth redirects to frontend with token in URL query param.
- **Environment**: Set `ENVIRONMENT=production` for restricted CORS. Vercel deployment auto-sets `FRONTEND_URL` and `API_BASE_URL` via `VERCEL` env var.

## Test Configuration

- `pytest.ini` sets `asyncio_mode = auto` and `testpaths = tests`
- Tests use SQLite in-memory (`sqlite+aiosqlite:///./test_db.db`) with `autouse` fixtures to create/drop tables and clean between tests
- Key fixtures in `conftest.py`: `client` (httpx AsyncClient), `registered_user`, `verified_user`, `superuser`, `sample_race`
