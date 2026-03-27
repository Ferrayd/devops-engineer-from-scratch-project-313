from datetime import datetime

from sqlmodel import Field, SQLModel


class ShortenedLink(SQLModel, table=True):
    __tablename__ = "links"

    id: int | None = Field(default=None, primary_key=True)
    short_name: str = Field(index=True, unique=True, min_length=1, max_length=10)
    original_url: str = Field(min_length=1, max_length=2048)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<Link(id={self.id}, short_name={self.short_name})>"
