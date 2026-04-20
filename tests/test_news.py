import pytest

pytestmark = pytest.mark.asyncio

NEWS_PAYLOAD = {
    "title": "Тестовая новость",
    "content": "Содержание тестовой новости",
    "summary": "Краткое содержание",
    "image_url": "https://example.com/image.jpg",
}


class TestListNews:
    async def test_list_empty(self, client):
        resp = await client.get("/news/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_returns_created_news(self, client, superuser):
        await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        resp = await client.get("/news/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == NEWS_PAYLOAD["title"]

    async def test_list_news_shape(self, client, superuser):
        await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        resp = await client.get("/news/")
        news = resp.json()[0]
        for field in ("id", "title", "summary", "image_url", "created_at"):
            assert field in news
        assert "content" not in news

    async def test_list_ordered_by_created_desc(self, client, superuser):
        await client.post("/news/", json={**NEWS_PAYLOAD, "title": "First"}, headers=superuser["headers"])
        await client.post("/news/", json={**NEWS_PAYLOAD, "title": "Second"}, headers=superuser["headers"])
        resp = await client.get("/news/")
        titles = [n["title"] for n in resp.json()]
        assert titles == ["Second", "First"]


class TestGetNews:
    async def test_get_existing(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.get(f"/news/{news_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == news_id
        assert resp.json()["content"] == NEWS_PAYLOAD["content"]

    async def test_get_nonexistent(self, client):
        resp = await client.get("/news/99999")
        assert resp.status_code == 404

    async def test_get_news_has_all_fields(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.get(f"/news/{news_id}")
        data = resp.json()
        for field in ("id", "title", "summary", "content", "image_url", "created_at", "updated_at", "created_by"):
            assert field in data


class TestCreateNews:
    async def test_create_as_superuser(self, client, superuser):
        resp = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == NEWS_PAYLOAD["title"]
        assert "created_at" in data

    async def test_create_as_regular_user(self, client, registered_user):
        resp = await client.post("/news/", json=NEWS_PAYLOAD, headers=registered_user["headers"])
        assert resp.status_code == 403

    async def test_create_as_verified_user(self, client, verified_user):
        resp = await client.post("/news/", json=NEWS_PAYLOAD, headers=verified_user["headers"])
        assert resp.status_code == 403

    async def test_create_without_auth(self, client):
        resp = await client.post("/news/", json=NEWS_PAYLOAD)
        assert resp.status_code == 401

    async def test_create_missing_required_field(self, client, superuser):
        bad = {k: v for k, v in NEWS_PAYLOAD.items() if k != "title"}
        resp = await client.post("/news/", json=bad, headers=superuser["headers"])
        assert resp.status_code == 422

    async def test_create_missing_content(self, client, superuser):
        bad = {k: v for k, v in NEWS_PAYLOAD.items() if k != "content"}
        resp = await client.post("/news/", json=bad, headers=superuser["headers"])
        assert resp.status_code == 422

    async def test_create_without_optional_fields(self, client, superuser):
        minimal = {
            "title": "Minimal",
            "content": "Content only",
        }
        resp = await client.post("/news/", json=minimal, headers=superuser["headers"])
        assert resp.status_code == 201
        assert resp.json()["summary"] is None
        assert resp.json()["image_url"] is None


class TestUpdateNews:
    async def test_update_as_superuser(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.patch(
            f"/news/{news_id}",
            json={"title": "Updated Title"},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    async def test_update_as_regular_user(self, client, superuser, registered_user):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.patch(
            f"/news/{news_id}",
            json={"title": "Hack"},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 403

    async def test_update_nonexistent_news(self, client, superuser):
        resp = await client.patch(
            "/news/99999",
            json={"title": "Update"},
            headers=superuser["headers"],
        )
        assert resp.status_code == 404

    async def test_update_partial_fields(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.patch(
            f"/news/{news_id}",
            json={"summary": "New summary"},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["summary"] == "New summary"
        assert resp.json()["title"] == NEWS_PAYLOAD["title"]

    async def test_update_without_auth(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.patch(f"/news/{news_id}", json={"title": "Update"})
        assert resp.status_code == 401

    async def test_update_all_fields(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        update_data = {
            "title": "All New",
            "content": "All New Content",
            "summary": "All New Summary",
            "image_url": "https://new.com/img.jpg",
        }
        resp = await client.patch(f"/news/{news_id}", json=update_data, headers=superuser["headers"])
        assert resp.status_code == 200
        for field, value in update_data.items():
            assert resp.json()[field] == value


class TestDeleteNews:
    async def test_delete_as_superuser(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.delete(f"/news/{news_id}", headers=superuser["headers"])
        assert resp.status_code == 204
        get_resp = await client.get(f"/news/{news_id}")
        assert get_resp.status_code == 404

    async def test_delete_as_regular_user(self, client, superuser, registered_user):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.delete(f"/news/{news_id}", headers=registered_user["headers"])
        assert resp.status_code == 403

    async def test_delete_nonexistent_news(self, client, superuser):
        resp = await client.delete("/news/99999", headers=superuser["headers"])
        assert resp.status_code == 404

    async def test_delete_without_auth(self, client, superuser):
        created = await client.post("/news/", json=NEWS_PAYLOAD, headers=superuser["headers"])
        news_id = created.json()["id"]
        resp = await client.delete(f"/news/{news_id}")
        assert resp.status_code == 401