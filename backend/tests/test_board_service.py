from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.board_service import (
    BoardWriteError,
    DEMO_PASSWORD,
    DEMO_USERNAME,
    get_board_for_user,
    update_board_for_user,
)
from backend.app.schemas import BoardPayload, CardPayload, ColumnPayload


def test_get_board_for_user_seeds_default_board(tmp_path: Path) -> None:
    board = get_board_for_user(tmp_path / "pm.db", DEMO_USERNAME, DEMO_PASSWORD)

    assert len(board.columns) == 5
    assert len(board.cards) == 8
    assert board.columns[0].title == "Backlog"


def test_board_payload_validation_rejects_unreferenced_cards() -> None:
    with pytest.raises(ValidationError):
        BoardPayload(
            columns=[ColumnPayload(id="col-1", title="Backlog", cardIds=[])],
            cards={"card-1": CardPayload(id="card-1", title="Card", details="")},
        )


def test_update_board_for_user_persists_changes(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    board = get_board_for_user(db_path, DEMO_USERNAME, DEMO_PASSWORD)

    updated_board = board.model_copy(deep=True)
    updated_board.columns[0].title = "Ideas"
    moved_card_id = updated_board.columns[0].cardIds.pop(0)
    updated_board.columns[1].cardIds.insert(0, moved_card_id)
    updated_board.cards[moved_card_id].title = "Updated title"
    updated_board.cards["card-new"] = CardPayload(
        id="card-new",
        title="New API card",
        details="Created in a unit test.",
    )
    updated_board.columns[2].cardIds.append("card-new")

    saved_board = update_board_for_user(db_path, DEMO_USERNAME, DEMO_PASSWORD, updated_board)

    assert saved_board.columns[0].title == "Ideas"
    assert saved_board.columns[1].cardIds[0].startswith("card-")
    assert saved_board.cards[saved_board.columns[1].cardIds[0]].title == "Updated title"
    assert any(card.title == "New API card" for card in saved_board.cards.values())


def test_update_board_for_user_rejects_column_count_changes(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    board = get_board_for_user(db_path, DEMO_USERNAME, DEMO_PASSWORD)
    invalid_board = BoardPayload(
        columns=board.columns[:-1],
        cards={
            card_id: board.cards[card_id]
            for column in board.columns[:-1]
            for card_id in column.cardIds
        },
    )

    with pytest.raises(BoardWriteError):
        update_board_for_user(db_path, DEMO_USERNAME, DEMO_PASSWORD, invalid_board)
