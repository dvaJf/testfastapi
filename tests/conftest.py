import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.database import Base, get_session
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_session():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    payload = {"email": "user@example.com", "password": "Password123!", "score": 0}
    await client.post("/auth/register", json=payload)
    login = await client.post("/auth/login", data={"username": "user@example.com", "password": "Password123!"})
    token = login.json()["access_token"]
    return {"email": "user@example.com", "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def verified_user(registered_user):
    """Manually flip is_verified in the DB for the registered user."""
    async with test_session_maker() as session:
        from sqlalchemy import update
        from src.auth.models import User
        await session.execute(update(User).where(User.email == registered_user["email"]).values(is_verified=True))
        await session.commit()
    return registered_user


@pytest_asyncio.fixture
async def superuser(client):
    payload = {"email": "admin@example.com", "password": "Admin123!", "score": 0}
    await client.post("/auth/register", json=payload)
    async with test_session_maker() as session:
        from sqlalchemy import update
        from src.auth.models import User
        await session.execute(
            update(User).where(User.email == "admin@example.com").values(is_superuser=True, is_verified=True)
        )
        await session.commit()
    login = await client.post("/auth/login", data={"username": "admin@example.com", "password": "Admin123!"})
    token = login.json()["access_token"]
    return {"email": "admin@example.com", "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def sample_race(client, superuser):
    payload = {
        "name": "Гран-при Монако",
        "race": "Monaco",
        "about": "Самая красивая трасса",
        "time": "2025-05-25T14:00:00",
        "maxuser": 5,
        "status": "Регистрация",
    }
    resp = await client.post("/races/", json=payload, headers=superuser["headers"])
    assert resp.status_code == 201
    return resp.json()