from pathlib import Path
import sqlite3

import pytest

from backend.app.db import (
    deserialize_metadata,
    get_connection,
    initialize_database,
    serialize_metadata,
)


def test_serialize_and_deserialize_metadata_round_trip() -> None:
    metadata = {"color": "yellow", "ai": {"source": "chat"}, "priority": 2}

    serialized = serialize_metadata(metadata)

    assert serialized == '{"ai":{"source":"chat"},"color":"yellow","priority":2}'
    assert deserialize_metadata(serialized) == metadata


def test_deserialize_metadata_requires_json_object() -> None:
    with pytest.raises(ValueError):
        deserialize_metadata('["not","an","object"]')


def test_initialize_database_creates_schema_on_empty_path(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "pm.db"

    created_path = initialize_database(db_path)

    assert created_path == db_path
    assert db_path.exists()

    with get_connection(db_path) as connection:
        table_names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"users", "boards", "columns", "cards"}.issubset(table_names)

        boards_columns = {
            row["name"]: row["type"]
            for row in connection.execute("PRAGMA table_info(boards)").fetchall()
        }
        cards_columns = {
            row["name"]: row["type"]
            for row in connection.execute("PRAGMA table_info(cards)").fetchall()
        }

        assert boards_columns["metadata_json"] == "TEXT"
        assert cards_columns["metadata_json"] == "TEXT"


def test_board_schema_enforces_one_board_per_user(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / "pm.db")

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("user", "password"),
        )
        user_id = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            ("user",),
        ).fetchone()["id"]
        connection.execute(
            "INSERT INTO boards (user_id, title, metadata_json) VALUES (?, ?, ?)",
            (user_id, "Primary Board", serialize_metadata({"theme": "default"})),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO boards (user_id, title, metadata_json) VALUES (?, ?, ?)",
                (user_id, "Second Board", serialize_metadata()),
            )


def test_json_constraint_rejects_invalid_metadata(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / "pm.db")

    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("user", "password"),
        )
        user_id = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            ("user",),
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO boards (user_id, title, metadata_json) VALUES (?, ?, ?)",
                (user_id, "Broken Board", "{not valid json}"),
            )
