from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    port: int = 8080
    
    database_url: str = "sqlite:///database.db"
    
    short_url_base: str = "https://short.io/r"
    
    environment: str = "development"
    
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()