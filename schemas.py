from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, Field


class LinkCreate(BaseModel):
    original_url: HttpUrl = Field(
        ..., 
        description="Оригинальный URL (должен быть валидным)"
    )
    short_name: str = Field(
        ..., 
        min_length=1,
        max_length=255,
        description="Уникальное короткое имя ссылки"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
            }
        }


class LinkResponse(BaseModel):    
    id: int = Field(..., description="Уникальный идентификатор")
    original_url: str = Field(..., description="Оригинальный URL")
    short_name: str = Field(..., description="Уникальное короткое имя")
    short_url: str = Field(..., description="Полный короткий URL")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "original_url": "https://example.com/long-url",
                "short_name": "exmpl",
                "short_url": "http://localhost:8080/r/exmpl",
                "created_at": "2024-01-15T10:30:00",
            }
        }