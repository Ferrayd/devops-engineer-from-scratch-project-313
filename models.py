from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):

    __tablename__ = "links"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
                "created_at": "2024-01-15T10:30:00",
            }
        }
    )

    id: int | None = Field(default=None, primary_key=True)
    original_url: str = Field(index=False, description="Оригинальный URL")
    short_name: str = Field(
        unique=True,
        index=True,
        description="Уникальное короткое имя"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Дата создания"
    )
