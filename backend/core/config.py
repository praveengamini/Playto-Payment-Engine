from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/playto"


    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"


    APP_ENV: str = "development"
    SECRET_KEY: str = "changeme"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"


    IDEMPOTENCY_TTL_SECONDS: int = 86400


    PAYOUT_SUCCESS_RATE: float = 0.70
    PAYOUT_FAIL_RATE: float = 0.20



    PAYOUT_PROCESSING_TIMEOUT_SECONDS: int = 30
    PAYOUT_MAX_RETRIES: int = 3


settings = Settings()