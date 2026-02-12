import json
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    port: int = Field(default=8080, description="Порт сервера")
    environment: str = Field(default="development", description="Окружение")
    
    database_url: str = Field(
        default="sqlite:///./database.db",
        description="URL подключения к БД"
    )
    
    short_url_base: str = Field(
        default="http://localhost:8080/r",
        description="Базовый URL для коротких ссылок"
    )
    
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8080",
        ],
        description="Допустимые origins для CORS"
    )
    cors_credentials: bool = Field(default=True)
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    cors_headers: List[str] = Field(default=["*"])
    
    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.cors_origins, str):
            try:
                self.cors_origins = json.loads(self.cors_origins)
            except json.JSONDecodeError:
                self.cors_origins = [
                    "http://localhost:5173",
                    "http://localhost:8080",
                ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()