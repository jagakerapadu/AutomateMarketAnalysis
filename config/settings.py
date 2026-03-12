from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application configuration using Pydantic settings"""
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "trading_system"
    DB_USER: str = "trading_user"
    DB_PASSWORD: str
    
    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_DAILY_LOSS: float = 5000.0
    MAX_OPEN_TRADES: int = 5
    ENABLE_LIVE_TRADING: bool = False
    
    # Scheduler Times (IST)
    PRE_MARKET_TIME: str = "08:45"
    MARKET_CLOSE_TIME: str = "15:30"
    POST_MARKET_TIME: str = "16:00"
    
    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    JWT_SECRET: str
    
    # Zerodha
    ZERODHA_API_KEY: Optional[str] = None
    ZERODHA_API_SECRET: Optional[str] = None
    ZERODHA_USER_ID: Optional[str] = None
    ZERODHA_ACCESS_TOKEN: Optional[str] = None
    ZERODHA_REQUEST_TOKEN: Optional[str] = None
    ZERODHA_PASSWORD: Optional[str] = None
    ZERODHA_TOTP_SECRET: Optional[str] = None
    
    # ICICI Breeze
    ICICI_API_KEY: Optional[str] = None
    ICICI_API_SECRET: Optional[str] = None
    ICICI_SESSION_TOKEN: Optional[str] = None
    
    # Dashboard
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

def get_settings() -> Settings:
    """Get fresh settings from .env file (no caching for credentials)"""
    return Settings()
