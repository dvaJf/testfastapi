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

class TestListRaces:
    async def test_list_empty(self, client):
        resp = await client.get("/races/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_returns_created_race(self, client, sample_race):
        resp = await client.get("/races/")
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert sample_race["id"] in ids

    async def test_list_race_shape(self, client, sample_race):
        resp = await client.get("/races/")
        race = next(r for r in resp.json() if r["id"] == sample_race["id"])
        for field in ("id", "name", "race", "time", "status", "maxuser", "users"):
            assert field in race


class TestGetRace:
    async def test_get_existing(self, client, sample_race):
        resp = await client.get(f"/races/{sample_race['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sample_race["id"]
        assert resp.json()["about"] is not None

    async def test_get_nonexistent(self, client):
        resp = await client.get("/races/99999")
        assert resp.status_code == 404


class TestCreateRace:
    async def test_create_as_superuser(self, client, superuser):
        resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == RACE_PAYLOAD["name"]
        assert data["users"] == 0

    async def test_create_as_unverified_user(self, client, registered_user):
        resp = await client.post("/races/", json=RACE_PAYLOAD, headers=registered_user["headers"])
        assert resp.status_code == 403

    async def test_create_as_verified_user(self, client, verified_user):
        resp = await client.post("/races/", json=RACE_PAYLOAD, headers=verified_user["headers"])
        assert resp.status_code == 201

    async def test_create_without_auth(self, client):
        resp = await client.post("/races/", json=RACE_PAYLOAD)
        assert resp.status_code == 401

    async def test_create_missing_required_field(self, client, superuser):
        bad = {k: v for k, v in RACE_PAYLOAD.items() if k != "name"}
        resp = await client.post("/races/", json=bad, headers=superuser["headers"])
        assert resp.status_code == 422


class TestUpdateRace:
    async def test_update_as_creator(self, client, verified_user):
        created = await client.post("/races/", json=RACE_PAYLOAD, headers=verified_user["headers"])
        race_id = created.json()["id"]
        resp = await client.patch(
            f"/races/{race_id}",
            json={"name": "Новое название"},
            headers=verified_user["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Новое название"

    async def test_update_as_non_creator(self, client, superuser, verified_user):
        created = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = created.json()["id"]
        resp = await client.patch(
            f"/races/{race_id}",
            json={"name": "Hack"},
            headers=verified_user["headers"],
        )
        assert resp.status_code == 403

    async def test_update_as_superuser(self, client, superuser, verified_user):
        created = await client.post("/races/", json=RACE_PAYLOAD, headers=verified_user["headers"])
        race_id = created.json()["id"]
        resp = await client.patch(
            f"/races/{race_id}",
            json={"status": "Завершена"},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Завершена"

    async def test_update_partial_fields(self, client, superuser):
        created = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = created.json()["id"]
        resp = await client.patch(
            f"/races/{race_id}",
            json={"maxuser": 30},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["maxuser"] == 30
        assert resp.json()["name"] == RACE_PAYLOAD["name"]

class TestRegisterForRace:
    async def test_register_success(self, client, sample_race, registered_user):
        resp = await client.post(
            f"/races/{sample_race['id']}/register",
            headers=registered_user["headers"],
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "registered"

    async def test_register_twice(self, client, sample_race, registered_user):
        await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        resp = await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        assert resp.status_code == 400
        assert "Already registered" in resp.json()["detail"]

    async def test_register_nonexistent_race(self, client, registered_user):
        resp = await client.post("/races/99999/register", headers=registered_user["headers"])
        assert resp.status_code == 404

    async def test_register_when_full(self, client, superuser):
        """Create a race with maxuser=1, fill it, then check the next user gets 400."""
        race_resp = await client.post(
            "/races/",
            json={**RACE_PAYLOAD, "maxuser": 1},
            headers=superuser["headers"],
        )
        race_id = race_resp.json()["id"]

        await client.post(f"/races/{race_id}/register", headers=superuser["headers"])

        await client.post(
            "/auth/register",
            json={"email": "user2@example.com", "password": "Pass123!", "score": 0},
        )
        login = await client.post(
            "/auth/login", data={"username": "user2@example.com", "password": "Pass123!"}
        )
        token2 = login.json()["access_token"]
        resp = await client.post(
            f"/races/{race_id}/register",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 400
        assert "full" in resp.json()["detail"].lower()

    async def test_register_when_closed(self, client, superuser, registered_user):
        race_resp = await client.post(
            "/races/",
            json={**RACE_PAYLOAD, "status": "Завершена"},
            headers=superuser["headers"],
        )
        race_id = race_resp.json()["id"]
        resp = await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        assert resp.status_code == 400
        assert "closed" in resp.json()["detail"].lower()

    async def test_register_without_auth(self, client, sample_race):
        resp = await client.post(f"/races/{sample_race['id']}/register")
        assert resp.status_code == 401


class TestUnregisterFromRace:
    async def test_unregister_success(self, client, sample_race, registered_user):
        await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        resp = await client.delete(f"/races/{sample_race['id']}/unregister", headers=registered_user["headers"])
        assert resp.status_code == 204

    async def test_unregister_not_registered(self, client, sample_race, registered_user):
        resp = await client.delete(f"/races/{sample_race['id']}/unregister", headers=registered_user["headers"])
        assert resp.status_code == 400
        assert "Not registered" in resp.json()["detail"]

    async def test_unregister_when_closed(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        # Close the race
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        resp = await client.delete(f"/races/{race_id}/unregister", headers=registered_user["headers"])
        assert resp.status_code == 400

class TestParticipants:
    async def test_get_participants_empty(self, client, sample_race):
        resp = await client.get(f"/races/{sample_race['id']}/all_users")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_participants_after_register(self, client, sample_race, registered_user):
        await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        resp = await client.get(f"/races/{sample_race['id']}/all_users")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["username"] == registered_user["email"]

    async def test_participant_count_in_race(self, client, sample_race, registered_user):
        await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        race = await client.get(f"/races/{sample_race['id']}")
        assert race.json()["users"] == 1


class TestResults:
    async def _finish_race_with_user(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        return race_id

    async def test_get_results_empty(self, client, sample_race):
        resp = await client.get(f"/races/{sample_race['id']}/results")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    async def test_set_results_success(self, client, superuser, registered_user):
        race_id = await self._finish_race_with_user(client, superuser, registered_user)
        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        resp = await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )
        assert resp.status_code == 200

    async def test_get_results_after_set(self, client, superuser, registered_user):
        race_id = await self._finish_race_with_user(client, superuser, registered_user)
        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )
        resp = await client.get(f"/races/{race_id}/results")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["position"] == 1

    async def test_set_results_race_not_finished(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        resp = await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )
        assert resp.status_code == 400

    async def test_set_results_duplicate_positions(self, client, superuser, registered_user):
        """Two users can't share the same position."""
        race_resp = await client.post(
            "/races/", json={**RACE_PAYLOAD, "maxuser": 10}, headers=superuser["headers"]
        )
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.post(f"/races/{race_id}/register", headers=superuser["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])
        parts = await client.get(f"/races/{race_id}/all_users")
        ids = [p["user_id"] for p in parts.json()]

        resp = await client.post(
            f"/races/{race_id}/results",
            json={"results": [
                {"user_id": ids[0], "position": 1},
                {"user_id": ids[1], "position": 1},
            ]},
            headers=superuser["headers"],
        )
        assert resp.status_code == 400

    async def test_set_results_non_participant(self, client, superuser, registered_user):
        race_id = await self._finish_race_with_user(client, superuser, registered_user)
        resp = await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": 99999, "position": 1}]},
            headers=superuser["headers"],
        )
        assert resp.status_code == 400

    async def test_set_results_forbidden_for_stranger(self, client, superuser, registered_user):
        race_id = await self._finish_race_with_user(client, superuser, registered_user)
        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        resp = await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 403