from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="allow")

    port: int = 8080
    environment: str = "development"

    database_url: str = "sqlite:///./database.db"

    short_url_base: str = "http://localhost:8080/r"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    cors_credentials: bool = True
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["*"]


settings = Settings()
