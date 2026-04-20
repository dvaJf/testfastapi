import pytest

pytestmark = pytest.mark.asyncio

RACE_PAYLOAD = {
    "name": "грани при Монако",
    "race": "монако",
    "about": "о трасе",
    "time": "2025-05-25",
    "maxuser": 5,
    "status": "Регистрация",
}


class TestSubmitReview:
    async def _create_finished_race_with_participant(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        return race_id

    async def test_review_success(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_participant(client, superuser, registered_user)
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": 1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vote"] == 1
        assert data["race_id"] == race_id
        assert "voter_id" in data

    async def test_review_dislike(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_participant(client, superuser, registered_user)
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": -1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["vote"] == -1

    async def test_review_update_existing(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_participant(client, superuser, registered_user)
        await client.post(f"/races/{race_id}/review", json={"vote": 1}, headers=registered_user["headers"])
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": -1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["vote"] == -1

    async def test_review_race_not_finished(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": 1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 400

    async def test_review_own_race(self, client, superuser):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": 1},
            headers=superuser["headers"],
        )
        assert resp.status_code == 400

    async def test_review_not_participant(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": 1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 403

    async def test_review_without_auth(self, client, superuser):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        resp = await client.post(f"/races/{race_id}/review", json={"vote": 1})
        assert resp.status_code == 401

    async def test_review_nonexistent_race(self, client, registered_user):
        resp = await client.post(
            "/races/99999/review",
            json={"vote": 1},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 404

    async def test_review_invalid_vote_value(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_participant(client, superuser, registered_user)
        resp = await client.post(
            f"/races/{race_id}/review",
            json={"vote": 999},
            headers=registered_user["headers"],
        )
        assert resp.status_code in (200, 422)

    async def test_review_affects_organizer_rating(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_participant(client, superuser, registered_user)
        race_before = await client.get(f"/races/{race_id}")
        likes_before = race_before.json()["organizer_likes"]
        await client.post(f"/races/{race_id}/review", json={"vote": 1}, headers=registered_user["headers"])
        race_after = await client.get(f"/races/{race_id}")
        likes_after = race_after.json()["organizer_likes"]
        assert likes_after == likes_before + 1


class TestDeleteReview:
    async def _create_finished_race_with_review(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        await client.post(f"/races/{race_id}/review", json={"vote": 1}, headers=registered_user["headers"])
        return race_id

    async def test_delete_review_not_found(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        resp = await client.delete(f"/races/{race_id}/review", headers=registered_user["headers"])
        assert resp.status_code == 404

    async def test_delete_review_without_auth(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_review(client, superuser, registered_user)
        resp = await client.delete(f"/races/{race_id}/review")
        assert resp.status_code == 401

    async def test_delete_review_rating_decreases(self, client, superuser, registered_user):
        race_id = await self._create_finished_race_with_review(client, superuser, registered_user)
        race_before = await client.get(f"/races/{race_id}")
        likes_before = race_before.json()["organizer_likes"]
        await client.delete(f"/races/{race_id}/review", headers=registered_user["headers"])
        race_after = await client.get(f"/races/{race_id}")
        likes_after = race_after.json()["organizer_likes"]
        assert likes_after == likes_before - 1