from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ShortenedLink(SQLModel, table=True):
    __tablename__ = "shortened_links"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    short_code: str = Field(index=True, unique=True, min_length=1, max_length=10)
    original_url: str = Field(min_length=1, max_length=2048)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __repr__(self):
        return f"<ShortenedLink(id={self.id}, short_code={self.short_code})>"