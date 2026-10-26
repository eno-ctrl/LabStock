from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "LabStock Laboratory Inventory"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = (
        "labstock_super_secret_jwt_signing_key_replace_for_production_min_64_chars_len"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Database
    DATABASE_URL: str = "sqlite:///./labstock.db"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://localhost:8550",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8550",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    return [v]
            return v
        raise ValueError(v)

    # Security & Rate Limits
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 20
    IDEMPOTENCY_CACHE_TTL_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
