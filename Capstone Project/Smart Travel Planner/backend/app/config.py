"""
Application configuration management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "Smart Travel Planner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Keys
    GOOGLE_MAPS_API_KEY: str = ""
    
    # CORS - Don't read from .env, use defaults
    # If you need to override, do it in code, not .env
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [
            "http://localhost:8501",
            "http://localhost:3000"
        ]
    
    # Paths - Use absolute paths
    BASE_DIR: Path = Path(__file__).parent.parent
    
    @property
    def CHROMADB_PATH(self) -> str:
        return str(self.BASE_DIR.parent / "data" / "chromadb")
    
    @property
    def TOURISM_DATA_PATH(self) -> str:
        return str(self.BASE_DIR.parent / "data" / "tourism_content")
    
    @property
    def CACHE_PATH(self) -> str:
        return str(self.BASE_DIR.parent / "data" / "cache")
    
    # Constraints Defaults
    DEFAULT_START_TIME: str = "09:00"
    DEFAULT_END_TIME: str = "21:00"
    DEFAULT_MAX_DAILY_DISTANCE: float = 50.0
    
    # RAG Settings
    EMBEDDING_MODEL: str = "chromadb_default"
    RAG_TOP_K: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )


# Global settings instance
settings = Settings()

# Create necessary directories
Path(settings.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.TOURISM_DATA_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.CACHE_PATH).mkdir(parents=True, exist_ok=True)