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
    database_url: str = "sqlite:///./payment.db"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Redis (for messaging)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # External Services
    inventory_service_url: str = "http://localhost:8000"
    
    # Application
    app_name: str = "Payment Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Order Processing
    order_completion_delay: int = 5  # seconds
    
    # JWT
    JWT_SECRET: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

settings = Settings()

