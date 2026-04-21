from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app

AUTH_HEADERS = {
    "X-Username": "user",
    "X-Password": "password",
}


def test_board_api_creates_db_and_returns_seeded_board(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    client = TestClient(create_app(db_path))

    response = client.get("/api/board", headers=AUTH_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert db_path.exists()
    assert len(payload["columns"]) == 5
    assert len(payload["cards"]) == 8


def test_board_api_rejects_invalid_credentials(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))

    response = client.get(
        "/api/board",
        headers={"X-Username": "user", "X-Password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials."}


def test_board_api_updates_and_reads_board_state(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))
    original_board = client.get("/api/board", headers=AUTH_HEADERS).json()

    moved_card_id = original_board["columns"][0]["cardIds"].pop(0)
    original_board["columns"][1]["cardIds"].insert(0, moved_card_id)
    original_board["columns"][2]["title"] = "Done"
    original_board["cards"][moved_card_id]["title"] = "Updated via API"
    original_board["cards"]["card-client-new"] = {
        "id": "card-client-new",
        "title": "Brand new",
        "details": "Saved through PUT /api/board",
    }
    original_board["columns"][3]["cardIds"].append("card-client-new")

    save_response = client.put("/api/board", headers=AUTH_HEADERS, json=original_board)

    assert save_response.status_code == 200
    saved_board = save_response.json()
    assert saved_board["columns"][2]["title"] == "Done"
    assert saved_board["cards"][saved_board["columns"][1]["cardIds"][0]]["title"] == "Updated via API"
    assert any(card["title"] == "Brand new" for card in saved_board["cards"].values())

    read_response = client.get("/api/board", headers=AUTH_HEADERS)

    assert read_response.status_code == 200
    assert read_response.json() == saved_board


def test_board_api_rejects_invalid_board_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))

    response = client.put(
        "/api/board",
        headers=AUTH_HEADERS,
        json={
            "columns": [{"id": "col-1", "title": "Backlog", "cardIds": ["card-1"]}],
            "cards": {},
        },
    )

    assert response.status_code == 422
