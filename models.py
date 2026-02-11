from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Link(SQLModel, table=True):
    
    __tablename__ = "links"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    original_url: str = Field(index=False)
    short_name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
            }
        }