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
    async def test_register_twice(self, client, sample_race, registered_user):
        await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        resp = await client.post(f"/races/{sample_race['id']}/register", headers=registered_user["headers"])
        assert resp.status_code == 400

    async def test_register_nonexistent_race(self, client, registered_user):
        resp = await client.post("/races/99999/register", headers=registered_user["headers"])
        assert resp.status_code == 404

    async def test_register_when_full(self, client, superuser):
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

    async def test_register_when_closed(self, client, superuser, registered_user):
        race_resp = await client.post(
            "/races/",
            json={**RACE_PAYLOAD, "status": "Завершена"},
            headers=superuser["headers"],
        )
        race_id = race_resp.json()["id"]
        resp = await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        assert resp.status_code == 400

    async def test_register_without_auth(self, client, sample_race):
        resp = await client.post(f"/races/{sample_race['id']}/register")
        assert resp.status_code == 401


class TestUnregisterFromRace:
    async def test_unregister_not_registered(self, client, sample_race, registered_user):
        resp = await client.delete(f"/races/{sample_race['id']}/unregister", headers=registered_user["headers"])
        assert resp.status_code == 400

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

import pytest

pytestmark = pytest.mark.asyncio


class TestRaceResultsPoints:
    """Test that race results correctly award points to users."""

    async def _setup_race_with_results(self, client, superuser, registered_user, position):
        race_resp = await client.post("/races/", json={
            "name": "Points Test",
            "race": "Test",
            "about": "Testing points",
            "time": "2025-05-25",
            "maxuser": 5,
            "status": "Регистрация",
        }, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": position}]},
            headers=superuser["headers"],
        )
        return user_id

    async def test_first_place_points(self, client, superuser, registered_user):
        user_id = await self._setup_race_with_results(client, superuser, registered_user, 1)
        resp = await client.get("/auth/users/leaderboard")
        entry = next(e for e in resp.json() if e["user_id"] == user_id)
        assert entry["score"] == 60

    async def test_tenth_place_points(self, client, superuser, registered_user):
        user_id = await self._setup_race_with_results(client, superuser, registered_user, 10)
        resp = await client.get("/auth/users/leaderboard")
        entry = next(e for e in resp.json() if e["user_id"] == user_id)
        assert entry["score"] == 32

    async def test_twenty_first_place_no_points(self, client, superuser, registered_user):
        user_id = await self._setup_race_with_results(client, superuser, registered_user, 21)
        resp = await client.get("/auth/users/leaderboard")
        entry = next(e for e in resp.json() if e["user_id"] == user_id)
        assert entry["score"] == 0

    async def test_results_idempotency(self, client, superuser, registered_user):
        """Setting results twice should not double-count points."""
        race_resp = await client.post("/races/", json={
            "name": "Idempotency Test",
            "race": "Test",
            "about": "Testing",
            "time": "2025-05-25",
            "maxuser": 5,
            "status": "Регистрация",
        }, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        # Set results first time
        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )

        resp1 = await client.get("/auth/users/leaderboard")
        score1 = next(e for e in resp1.json() if e["user_id"] == user_id)["score"]

        # Set results second time (same position)
        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )

        resp2 = await client.get("/auth/users/leaderboard")
        score2 = next(e for e in resp2.json() if e["user_id"] == user_id)["score"]

        assert score1 == score2 == 60

    async def test_update_results_changes_points(self, client, superuser, registered_user):
        """Changing results should recalculate points correctly."""
        race_resp = await client.post("/races/", json={
            "name": "Update Test",
            "race": "Test",
            "about": "Testing",
            "time": "2025-05-25",
            "maxuser": 5,
            "status": "Регистрация",
        }, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]

        # First place = 60 points
        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )

        resp1 = await client.get("/auth/users/leaderboard")
        score1 = next(e for e in resp1.json() if e["user_id"] == user_id)["score"]
        assert score1 == 60

        # Change to 10th place = 32 points
        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 10}]},
            headers=superuser["headers"],
        )

        resp2 = await client.get("/auth/users/leaderboard")
        score2 = next(e for e in resp2.json() if e["user_id"] == user_id)["score"]
        assert score2 == 32


class TestRaceReviewsEdgeCases:
    """Additional edge cases for race reviews."""

    async def test_multiple_users_review_same_organizer(self, client, superuser):
        # Create multiple regular users
        users = []
        for i in range(3):
            payload = {"email": f"reviewer{i}@example.com", "password": "Pass123!", "score": 0}
            await client.post("/auth/register", json=payload)
            login = await client.post("/auth/login", data={"username": payload["email"], "password": payload["password"]})
            token = login.json()["access_token"]
            users.append({"email": payload["email"], "headers": {"Authorization": f"Bearer {token}"}})

        # Create race and finish it
        race_resp = await client.post("/races/", json={
            "name": "Multi Review Test",
            "race": "Test",
            "about": "Testing",
            "time": "2025-05-25",
            "maxuser": 10,
            "status": "Регистрация",
        }, headers=superuser["headers"])
        race_id = race_resp.json()["id"]

        # Register all users
        for user in users:
            await client.post(f"/races/{race_id}/register", headers=user["headers"])

        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        # All users review positively
        for user in users:
            resp = await client.post(f"/races/{race_id}/review", json={"vote": 1}, headers=user["headers"])
            assert resp.status_code == 200

        # Check organizer rating
        race = await client.get(f"/races/{race_id}")
        assert race.json()["organizer_likes"] == 3
        assert race.json()["organizer_dislikes"] == 0

    async def test_review_then_unregister_impossible(self, client, superuser, registered_user):
        """Cannot unregister from finished race, but review requires finished race."""
        race_resp = await client.post("/races/", json={
            "name": "Review Unregister Test",
            "race": "Test",
            "about": "Testing",
            "time": "2025-05-25",
            "maxuser": 5,
            "status": "Регистрация",
        }, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        # Submit review
        resp = await client.post(f"/races/{race_id}/review", json={"vote": 1}, headers=registered_user["headers"])
        assert resp.status_code == 200

        # Try to unregister (should fail because race is finished)
        resp = await client.delete(f"/races/{race_id}/unregister", headers=registered_user["headers"])
        assert resp.status_code == 400