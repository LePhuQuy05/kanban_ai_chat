from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pm.db"

SCHEMA_STATEMENTS = (
    """
    PRAGMA foreign_keys = ON;
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS boards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        title TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS columns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        position INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
        UNIQUE (board_id, position)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        column_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '',
        position INTEGER NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
        UNIQUE (column_id, position)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
    """,
)


def serialize_metadata(metadata: dict[str, Any] | None = None) -> str:
    if metadata is None:
        metadata = {}
    return json.dumps(metadata, separators=(",", ":"), sort_keys=True)


def deserialize_metadata(metadata_json: str | None) -> dict[str, Any]:
    if not metadata_json:
        return {}

    parsed = json.loads(metadata_json)
    if not isinstance(parsed, dict):
        raise ValueError("Metadata JSON must decode to an object.")
    return parsed


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    resolved_path = Path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(resolved_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()

    return resolved_path
