import pytest

pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "Pass123!", "score": 0},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["score"] == 0
        assert "password" not in data

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "Pass123!", "score": 0}
        await client.post("/auth/register", json=payload)
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 400

    async def test_register_invalid_email(self, client):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "Pass123!", "score": 0},
        )
        assert resp.status_code == 422



class TestLogin:
    async def test_login_success(self, client, registered_user):
        resp = await client.post(
            "/auth/login",
            data={"username": registered_user["email"], "password": "Password123!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client, registered_user):
        resp = await client.post(
            "/auth/login",
            data={"username": registered_user["email"], "password": "WrongPass!"},
        )
        assert resp.status_code == 400

    async def test_login_unknown_email(self, client):
        resp = await client.post(
            "/auth/login",
            data={"username": "ghost@example.com", "password": "Pass123!"},
        )
        assert resp.status_code == 400

    async def test_login_returns_bearer_token(self, client, registered_user):
        resp = await client.post(
            "/auth/login",
            data={"username": registered_user["email"], "password": "Password123!"},
        )
        data = resp.json()
        assert data.get("token_type", "").lower() == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20


class TestProtectedRoutes:
    async def test_access_without_token(self, client, sample_race):
        resp = await client.post(f"/races/{sample_race['id']}/register")
        assert resp.status_code == 401

    async def test_access_with_invalid_token(self, client, sample_race):
        resp = await client.post(
            f"/races/{sample_race['id']}/register",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401