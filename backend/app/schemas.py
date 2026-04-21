from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CardPayload(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class ColumnPayload(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cardIds: list[str] = Field(default_factory=list)


class BoardPayload(BaseModel):
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_board_links(self) -> "BoardPayload":
        column_ids = [column.id for column in self.columns]
        if len(column_ids) != len(set(column_ids)):
            raise ValueError("Column ids must be unique.")

        if set(self.cards.keys()) != {card.id for card in self.cards.values()}:
            raise ValueError("Card map keys must match each card id.")

        referenced_card_ids = [card_id for column in self.columns for card_id in column.cardIds]
        if len(referenced_card_ids) != len(set(referenced_card_ids)):
            raise ValueError("Each card must appear in only one column.")

        if set(referenced_card_ids) != set(self.cards.keys()):
            raise ValueError("Columns must reference every card exactly once.")

        return self
