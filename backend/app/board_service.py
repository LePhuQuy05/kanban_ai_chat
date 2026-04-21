from __future__ import annotations

import re
from pathlib import Path

from backend.app.db import get_connection, initialize_database, serialize_metadata
from backend.app.schemas import BoardPayload, CardPayload, ColumnPayload

DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"
BOARD_TITLE = "Kanban Studio"

_BACKEND_ID_PATTERN = re.compile(r"^(?P<prefix>col|card)-(?P<value>\d+)$")

DEFAULT_BOARD_TEMPLATE = [
    (
        "Backlog",
        [
            ("Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
            ("Gather customer signals", "Review support tags, sales notes, and churn feedback."),
        ],
    ),
    (
        "Discovery",
        [
            ("Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
        ],
    ),
    (
        "In Progress",
        [
            ("Refine status language", "Standardize column labels and tone across the board."),
            ("Design card layout", "Add hierarchy and spacing for scanning dense lists."),
        ],
    ),
    (
        "Review",
        [
            ("QA micro-interactions", "Verify hover, focus, and loading states."),
        ],
    ),
    (
        "Done",
        [
            ("Ship marketing page", "Final copy approved and asset pack delivered."),
            ("Close onboarding sprint", "Document release notes and share internally."),
        ],
    ),
]


class InvalidCredentialsError(ValueError):
    pass


class BoardWriteError(ValueError):
    pass


def _parse_backend_id(identifier: str, expected_prefix: str) -> int | None:
    match = _BACKEND_ID_PATTERN.match(identifier)
    if not match or match.group("prefix") != expected_prefix:
        return None
    return int(match.group("value"))


def _ensure_demo_user(connection, username: str, password: str) -> int:
    if username != DEMO_USERNAME or password != DEMO_PASSWORD:
        raise InvalidCredentialsError("Invalid credentials.")

    user_row = connection.execute(
        "SELECT id, password FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if user_row is None:
        cursor = connection.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        return int(cursor.lastrowid)

    if user_row["password"] != password:
        raise InvalidCredentialsError("Invalid credentials.")

    return int(user_row["id"])


def _seed_default_board(connection, user_id: int) -> int:
    board_cursor = connection.execute(
        "INSERT INTO boards (user_id, title, metadata_json) VALUES (?, ?, ?)",
        (user_id, BOARD_TITLE, serialize_metadata()),
    )
    board_id = int(board_cursor.lastrowid)

    for column_position, (column_title, cards) in enumerate(DEFAULT_BOARD_TEMPLATE):
        column_cursor = connection.execute(
            """
            INSERT INTO columns (board_id, name, position)
            VALUES (?, ?, ?)
            """,
            (board_id, column_title, column_position),
        )
        column_id = int(column_cursor.lastrowid)

        for card_position, (card_title, card_details) in enumerate(cards):
            connection.execute(
                """
                INSERT INTO cards (column_id, title, details, position, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    column_id,
                    card_title,
                    card_details,
                    card_position,
                    serialize_metadata(),
                ),
            )

    return board_id


def _get_or_create_board_id(connection, user_id: int) -> int:
    board_row = connection.execute(
        "SELECT id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if board_row is not None:
        return int(board_row["id"])

    return _seed_default_board(connection, user_id)


def _load_board_payload(connection, board_id: int) -> BoardPayload:
    column_rows = connection.execute(
        """
        SELECT id, name, position
        FROM columns
        WHERE board_id = ?
        ORDER BY position ASC, id ASC
        """,
        (board_id,),
    ).fetchall()

    cards_by_id: dict[str, CardPayload] = {}
    columns: list[ColumnPayload] = []

    for column_row in column_rows:
        column_identifier = f"col-{column_row['id']}"
        card_rows = connection.execute(
            """
            SELECT id, title, details
            FROM cards
            WHERE column_id = ?
            ORDER BY position ASC, id ASC
            """,
            (column_row["id"],),
        ).fetchall()

        card_ids: list[str] = []
        for card_row in card_rows:
            card_identifier = f"card-{card_row['id']}"
            cards_by_id[card_identifier] = CardPayload(
                id=card_identifier,
                title=card_row["title"],
                details=card_row["details"],
            )
            card_ids.append(card_identifier)

        columns.append(
            ColumnPayload(
                id=column_identifier,
                title=column_row["name"],
                cardIds=card_ids,
            )
        )

    return BoardPayload(columns=columns, cards=cards_by_id)


def get_board_for_user(db_path: str | Path, username: str, password: str) -> BoardPayload:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        user_id = _ensure_demo_user(connection, username, password)
        board_id = _get_or_create_board_id(connection, user_id)
        connection.commit()
        return _load_board_payload(connection, board_id)


def update_board_for_user(
    db_path: str | Path,
    username: str,
    password: str,
    board: BoardPayload,
) -> BoardPayload:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        user_id = _ensure_demo_user(connection, username, password)
        board_id = _get_or_create_board_id(connection, user_id)

        existing_columns = connection.execute(
            """
            SELECT id, position
            FROM columns
            WHERE board_id = ?
            ORDER BY position ASC, id ASC
            """,
            (board_id,),
        ).fetchall()

        if len(existing_columns) != len(board.columns):
            raise BoardWriteError("Board must keep the fixed column count.")

        existing_column_ids = {int(row["id"]) for row in existing_columns}
        position_to_column_id = {
            index: int(row["id"]) for index, row in enumerate(existing_columns)
        }

        resolved_column_ids: list[int] = []
        for index, column in enumerate(board.columns):
            parsed_column_id = _parse_backend_id(column.id, "col")
            if parsed_column_id in existing_column_ids:
                resolved_column_ids.append(parsed_column_id)
            else:
                resolved_column_ids.append(position_to_column_id[index])

        seen_column_ids = set()
        for column_id in resolved_column_ids:
            if column_id in seen_column_ids:
                raise BoardWriteError("Column ids must resolve uniquely.")
            seen_column_ids.add(column_id)

        for position, column in enumerate(board.columns):
            column_id = resolved_column_ids[position]
            connection.execute(
                """
                UPDATE columns
                SET name = ?, position = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (column.title, position, column_id, board_id),
            )

        existing_card_rows = connection.execute(
            """
            SELECT cards.id, cards.column_id
            FROM cards
            JOIN columns ON columns.id = cards.column_id
            WHERE columns.board_id = ?
            """,
            (board_id,),
        ).fetchall()
        existing_card_ids = {int(row["id"]) for row in existing_card_rows}

        if existing_card_ids:
            placeholders = ",".join("?" for _ in existing_card_ids)
            connection.execute(
                f"""
                UPDATE cards
                SET position = -id, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                """,
                tuple(existing_card_ids),
            )

        seen_existing_card_ids: set[int] = set()

        for column_position, column in enumerate(board.columns):
            column_id = resolved_column_ids[column_position]
            for card_position, card_identifier in enumerate(column.cardIds):
                card = board.cards[card_identifier]
                parsed_card_id = _parse_backend_id(card_identifier, "card")

                if parsed_card_id in existing_card_ids:
                    connection.execute(
                        """
                        UPDATE cards
                        SET column_id = ?, title = ?, details = ?, position = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (
                            column_id,
                            card.title,
                            card.details,
                            card_position,
                            parsed_card_id,
                        ),
                    )
                    seen_existing_card_ids.add(parsed_card_id)
                else:
                    connection.execute(
                        """
                        INSERT INTO cards (column_id, title, details, position, metadata_json)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            column_id,
                            card.title,
                            card.details,
                            card_position,
                            serialize_metadata(),
                        ),
                    )

            connection.execute(
                """
                UPDATE boards
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (board_id,),
            )

        stale_card_ids = existing_card_ids - seen_existing_card_ids
        if stale_card_ids:
            placeholders = ",".join("?" for _ in stale_card_ids)
            connection.execute(
                f"DELETE FROM cards WHERE id IN ({placeholders})",
                tuple(stale_card_ids),
            )

        connection.commit()
        return _load_board_payload(connection, board_id)
