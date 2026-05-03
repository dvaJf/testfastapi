import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC


@pytest_asyncio.fixture
async def sample_bet(client, superuser):
    payload = {
        "title": "Кто выиграет гонку?",
        "description": "Ставка на победителя",
        "closes_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "options": [
            {"label": "Хэмилтон"},
            {"label": "Ферстаппен"},
            {"label": "Леклер"},
        ],
    }
    resp = await client.post("/api/bets/", json=payload, headers=superuser["headers"])
    assert resp.status_code == 201
    return resp.json()


async def test_list_bets(client, sample_bet):
    resp = await client.get("/api/bets/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_get_bet(client, sample_bet, verified_user):
    bet_id = sample_bet["id"]
    resp = await client.get(f"/api/bets/{bet_id}", headers=verified_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == bet_id
    assert "options" in data


async def test_place_bet(client, sample_bet, verified_user):
    bet_id = sample_bet["id"]
    option_id = sample_bet["options"][0]["id"]
    payload = {"option_id": option_id, "stake": 10}
    resp = await client.post(f"/api/bets/{bet_id}/bet", json=payload, headers=verified_user["headers"])
    assert resp.status_code == 201


async def test_my_bets(client, sample_bet, verified_user):
    # Сначала поставим
    bet_id = sample_bet["id"]
    option_id = sample_bet["options"][0]["id"]
    payload = {"option_id": option_id, "stake": 10}
    await client.post(f"/api/bets/{bet_id}/bet", json=payload, headers=verified_user["headers"])

    resp = await client.get("/api/bets/user/my-bets", headers=verified_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_resolve_bet(client, sample_bet, superuser):
    bet_id = sample_bet["id"]
    option_id = sample_bet["options"][0]["id"]
    payload = {"winning_option_id": option_id}
    resp = await client.post(f"/api/bets/{bet_id}/resolve", json=payload, headers=superuser["headers"])
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_edit_bet_title(client, sample_bet, superuser):
    """Test editing bet title."""
    bet_id = sample_bet["id"]
    resp = await client.patch(
        f"/api/bets/{bet_id}",
        json={"title": "Updated Title"},
        headers=superuser["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_edit_bet_add_option(client, sample_bet, superuser):
    """Test adding a new option to existing bet."""
    bet_id = sample_bet["id"]
    # Get current options
    get_resp = await client.get(f"/api/bets/{bet_id}", headers=superuser["headers"])
    current_options = get_resp.json()["options"]
    # Add a new option
    new_option = {"label": "New Option"}
    updated_options = [{"id": opt["id"], "label": opt["label"]} for opt in current_options] + [new_option]
    resp = await client.patch(
        f"/api/bets/{bet_id}",
        json={"options": updated_options},
        headers=superuser["headers"]
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["options"]) == len(current_options) + 1


@pytest.mark.asyncio
async def test_delete_bet(client, superuser):
    """Test deleting a bet."""
    # Create a bet
    payload = {
        "title": "To Delete",
        "closes_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "options": [{"label": "A"}, {"label": "B"}],
    }
    create_resp = await client.post("/api/bets/", json=payload, headers=superuser["headers"])
    assert create_resp.status_code == 201
    bet_id = create_resp.json()["id"]
    # Delete
    del_resp = await client.delete(f"/api/bets/{bet_id}", headers=superuser["headers"])
    assert del_resp.status_code == 204
    # Verify deleted
    get_resp = await client.get(f"/api/bets/{bet_id}", headers=superuser["headers"])
    assert get_resp.status_code == 404
