import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://neondb_owner:npg_FY9xI3DbNnOy@ep-mute-mud-b5m0wtm5-pooler.c-7.us-east-2.aws.neon.tech/neondb?ssl=require"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cmr-secret-jwt-key-python-microservices")
    JWT_ALGORITHM: str = "HS256"
    TOKEN_ENCRYPTION_KEY: str = os.getenv(
        "TOKEN_ENCRYPTION_KEY", 
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    META_WEBHOOK_VERIFY_TOKEN: str = os.getenv(
        "META_WEBHOOK_VERIFY_TOKEN", 
        "centegix_secure_verify_token_2026"
    )
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "105938201928471")
    META_PERMANENT_ACCESS_TOKEN: str = os.getenv("META_PERMANENT_ACCESS_TOKEN", "")

settings = Settings()
