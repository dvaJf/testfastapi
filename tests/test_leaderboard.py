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


class TestLeaderboard:
    async def test_leaderboard_empty(self, client):
        resp = await client.get("/auth/users/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_leaderboard_shape(self, client):
        resp = await client.get("/auth/users/leaderboard")
        assert resp.status_code == 200
        if resp.json():
            entry = resp.json()[0]
            for field in ("position", "user_id", "email", "score", "races_completed", "best_position"):
                assert field in entry

    async def test_leaderboard_after_race_results(self, client, superuser, registered_user):
        race_resp = await client.post("/races/", json=RACE_PAYLOAD, headers=superuser["headers"])
        race_id = race_resp.json()["id"]
        await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts = await client.get(f"/races/{race_id}/all_users")
        user_id = parts.json()[0]["user_id"]
        await client.post(
            f"/races/{race_id}/results",
            json={"results": [{"user_id": user_id, "position": 1}]},
            headers=superuser["headers"],
        )

        resp = await client.get("/auth/users/leaderboard")
        assert resp.status_code == 200
        data = resp.json()

        user_entry = next((e for e in data if e["user_id"] == user_id), None)
        assert user_entry is not None
        assert user_entry["score"] == 60
        assert user_entry["races_completed"] == 1
        assert user_entry["best_position"] == 1
        assert user_entry["position"] == 1

    async def test_leaderboard_orders_by_score_desc(self, client, superuser):
        user1_payload = {"email": "user1@example.com", "password": "Pass123!", "score": 0}
        user2_payload = {"email": "user2@example.com", "password": "Pass123!", "score": 0}

        await client.post("/auth/register", json=user1_payload)
        await client.post("/auth/register", json=user2_payload)

        login1 = await client.post("/auth/login", data={"username": "user1@example.com", "password": "Pass123!"})
        login2 = await client.post("/auth/login", data={"username": "user2@example.com", "password": "Pass123!"})

        token1 = login1.json()["access_token"]
        token2 = login2.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        race_resp = await client.post("/races/", json={**RACE_PAYLOAD, "maxuser": 10}, headers=superuser["headers"])
        race_id = race_resp.json()["id"]

        await client.post(f"/races/{race_id}/register", headers=headers1)
        await client.post(f"/races/{race_id}/register", headers=headers2)
        await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts = await client.get(f"/races/{race_id}/all_users")
        users = parts.json()
        user1_id = next(u["user_id"] for u in users if u["username"] == "user1@example.com")
        user2_id = next(u["user_id"] for u in users if u["username"] == "user2@example.com")

        await client.post(
            f"/races/{race_id}/results",
            json={"results": [
                {"user_id": user1_id, "position": 1},
                {"user_id": user2_id, "position": 2},
            ]},
            headers=superuser["headers"],
        )

        resp = await client.get("/auth/users/leaderboard")
        data = resp.json()

        user1_entry = next(e for e in data if e["user_id"] == user1_id)
        user2_entry = next(e for e in data if e["user_id"] == user2_id)

        assert user1_entry["score"] == 60
        assert user2_entry["score"] == 55
        assert user1_entry["position"] < user2_entry["position"]

    async def test_leaderboard_no_auth_required(self, client):
        resp = await client.get("/auth/users/leaderboard")
        assert resp.status_code == 200

    async def test_leaderboard_races_completed_count(self, client, superuser, registered_user):
        for i in range(2):
            race_resp = await client.post("/races/", json={**RACE_PAYLOAD, "name": f"Race {i}"}, headers=superuser["headers"])
            race_id = race_resp.json()["id"]
            await client.post(f"/races/{race_id}/register", headers=registered_user["headers"])
            await client.patch(f"/races/{race_id}", json={"status": "Завершена"}, headers=superuser["headers"])

            parts = await client.get(f"/races/{race_id}/all_users")
            user_id = parts.json()[0]["user_id"]
            await client.post(
                f"/races/{race_id}/results",
                json={"results": [{"user_id": user_id, "position": 3}]},
                headers=superuser["headers"],
            )

        resp = await client.get("/auth/users/leaderboard")
        data = resp.json()
        user_entry = next(e for e in data if e["user_id"] == user_id)
        assert user_entry["races_completed"] == 2

    async def test_leaderboard_best_position(self, client, superuser, registered_user):
        race_resp1 = await client.post("/races/", json={**RACE_PAYLOAD, "name": "Race 1"}, headers=superuser["headers"])
        race_id1 = race_resp1.json()["id"]
        await client.post(f"/races/{race_id1}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id1}", json={"status": "Завершена"}, headers=superuser["headers"])

        race_resp2 = await client.post("/races/", json={**RACE_PAYLOAD, "name": "Race 2"}, headers=superuser["headers"])
        race_id2 = race_resp2.json()["id"]
        await client.post(f"/races/{race_id2}/register", headers=registered_user["headers"])
        await client.patch(f"/races/{race_id2}", json={"status": "Завершена"}, headers=superuser["headers"])

        parts1 = await client.get(f"/races/{race_id1}/all_users")
        user_id = parts1.json()[0]["user_id"]

        await client.post(
            f"/races/{race_id1}/results",
            json={"results": [{"user_id": user_id, "position": 5}]},
            headers=superuser["headers"],
        )
        await client.post(
            f"/races/{race_id2}/results",
            json={"results": [{"user_id": user_id, "position": 2}]},
            headers=superuser["headers"],
        )

        resp = await client.get("/auth/users/leaderboard")
        data = resp.json()
        user_entry = next(e for e in data if e["user_id"] == user_id)
        assert user_entry["best_position"] == 2