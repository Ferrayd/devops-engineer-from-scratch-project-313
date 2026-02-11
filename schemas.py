from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class LinkCreate(BaseModel):
    
    original_url: HttpUrl
    short_name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
            }
        }


class LinkResponse(BaseModel):
    
    id: int
    original_url: str
    short_name: str
    short_url: str
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
                "short_url": "https://short.io/r/exmpl",
            }
        }


class PaginationParams(BaseModel):
    
    start: int = 0
    end: int = 10
    
    class Config:
        json_schema_extra = {
            "example": {
                "start": 0,
                "end": 10,
            }
        }
    
    def validate(self):
        if self.start < 0:
            self.start = 0
        if self.end <= self.start:
            self.end = self.start + 10
        return self


class PaginatedResponse(BaseModel):
    
    items: list[LinkResponse]
    total: int
    start: int
    end: int
    
    @property
    def content_range(self) -> str:
        return f"links {self.start}-{self.end - 1}/{self.total}"