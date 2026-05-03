"""
Improved testing examples using existing fixtures.
"""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test that the health endpoint works."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_and_get_race(client, superuser):
    """Test race creation and retrieval."""
    race_data = {
        "name": "Test Race",
        "race": "Test Type",
        "about": "A test race",
        "time": "2025-05-25T14:00:00",
        "maxuser": 5,
        "status": "Регистрация",
    }
    create_resp = await client.post("/api/races/", json=race_data, headers=superuser["headers"])
    assert create_resp.status_code == 201
    race_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/races/{race_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Test Race"


@pytest.mark.asyncio
async def test_race_results_workflow(client, superuser, registered_user):
    """Test complete race results workflow."""
    # Create race
    race_data = {
        "name": "Results Test Race",
        "race": "Test",
        "about": "Testing results",
        "time": "2025-05-25T14:00:00",
        "maxuser": 5,
        "status": "Регистрация",
    }
    create_resp = await client.post("/api/races/", json=race_data, headers=superuser["headers"])
    assert create_resp.status_code == 201
    race_id = create_resp.json()["id"]

    # Register user (use registered_user fixture)
    register_resp = await client.post(
        f"/api/races/{race_id}/register",
        headers=registered_user["headers"]
    )
    assert register_resp.status_code == 200

    # Finish the race
    finish_resp = await client.patch(
        f"/api/races/{race_id}",
        json={"status": "Завершена"},
        headers=superuser["headers"]
    )
    assert finish_resp.status_code == 200

    # Set results
    results_data = [{"user_id": registered_user["id"], "position": 1}]
    results_resp = await client.post(
        f"/api/races/{race_id}/results",
        json={"results": results_data},
        headers=superuser["headers"]
    )
    assert results_resp.status_code == 200

    # Check leaderboard update
    lb_resp = await client.get("/api/auth/users/leaderboard")
    assert lb_resp.status_code == 200
