import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Flyyy Privacy-Preserving Customer Data Platform"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flyyy_cdp.db")
    
    # Cryptographic keys
    # Default 32-byte hex keys (64 hex characters)
    FPE_KEY: str = os.getenv("FPE_KEY", "2b7e151628aed2a6abf7158809cf4f3c2b7e151628aed2a6abf7158809cf4f3c")
    VAULT_AES_KEY: str = os.getenv("VAULT_AES_KEY", "603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4")
    TOKEN_SECRET_SALT: str = os.getenv("TOKEN_SECRET_SALT", "flyyy_cdp_super_secret_deterministic_token_salt_2026")
    
    # Mailpit
    MAIL_HOST: str = os.getenv("MAIL_HOST", "localhost")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_API_URL: str = os.getenv("MAIL_API_URL", "http://localhost:8025/api/v1")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
