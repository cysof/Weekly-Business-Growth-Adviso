import os
import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Weekly-Biness-Growth-Advisor"
    PROJECT_VERSION: str = "0.0.1"
    PROJECT_DESCRIPTION: str = "API for generating business growth insights"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEBUG: bool = False
    TESTING: bool = False
    Tick_URL: str = os.getenv("Tick_URL", "")
    TARGET_URL: str = os.getenv("TARGET_URL", "")
    TELEX_WEBHOOK_URL: str = os.getenv("TELEX_WEBHOOK_URL", "")
    
settings = Settings()
