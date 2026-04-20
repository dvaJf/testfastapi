import pytest

pytestmark = pytest.mark.asyncio


class TestAuthUsersEndpoints:
    """Tests for fastapi-users built-in user management endpoints."""

    async def test_get_current_user(self, client, registered_user):
        resp = await client.get("/auth/users/me", headers=registered_user["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert "id" in data
        assert "score" in data

    async def test_get_current_user_without_auth(self, client):
        resp = await client.get("/auth/users/me")
        assert resp.status_code == 401

    async def test_patch_current_user(self, client, registered_user):
        resp = await client.patch(
            "/auth/users/me",
            json={"email": "updated@example.com"},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@example.com"

    async def test_get_user_by_id(self, client, superuser, registered_user):
        me = await client.get("/auth/users/me", headers=registered_user["headers"])
        user_id = me.json()["id"]

        resp = await client.get(f"/auth/users/{user_id}", headers=superuser["headers"])
        assert resp.status_code == 200
        assert resp.json()["email"] == registered_user["email"]

    async def test_get_user_by_id_as_regular_user(self, client, registered_user):
        me = await client.get("/auth/users/me", headers=registered_user["headers"])
        user_id = me.json()["id"]

        resp = await client.get(f"/auth/users/{user_id}", headers=registered_user["headers"])
        assert resp.status_code in (200, 403)

    async def test_get_nonexistent_user(self, client, superuser):
        resp = await client.get("/auth/users/99999", headers=superuser["headers"])
        assert resp.status_code == 404

    async def test_patch_user_by_id_as_superuser(self, client, superuser, registered_user):
        me = await client.get("/auth/users/me", headers=registered_user["headers"])
        user_id = me.json()["id"]

        resp = await client.patch(
            f"/auth/users/{user_id}",
            json={"is_verified": True},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_verified"] is True

    async def test_delete_user_by_id_as_superuser(self, client, superuser, registered_user):
        me = await client.get("/auth/users/me", headers=registered_user["headers"])
        user_id = me.json()["id"]

        resp = await client.delete(f"/auth/users/{user_id}", headers=superuser["headers"])
        assert resp.status_code == 204
