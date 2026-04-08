import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str
    DATABASE_NAME: str = "explainshield"
    
    # Security Configuration
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI/ML Configuration
    OLLAMA_URL: str = "http://localhost:11434"
    
    # Encryption Configuration (CSFLE)
    # This should be a 32-character string which we'll derive a 96-byte key from for local KMS
    ENCRYPTION_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global instance
settings = Settings()
