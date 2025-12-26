"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_prefix = "",
        env_file=".env",
        case_sensitive=False
    )
    
    # Database
    database_url: str = "sqlite:///./user.db"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Redis (for messaging)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # Application
    app_name: str = "User Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # JWT
    JWT_SECRET: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60


settings = Settings()

