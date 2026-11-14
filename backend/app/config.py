import json
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "ClaimResolve AI"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "supersecretdevkeyclaimresolveai2025replaceinproduction32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # Database: Supports PostgreSQL+pgvector and SQLite async fallback
    DATABASE_URL: str = "sqlite+aiosqlite:///./claimresolve_local.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str) and v:
            # Render and Heroku provide postgres:// or postgresql://; convert to asyncpg
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # File Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # AI Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "anthropic"
    EMBEDDING_PROVIDER: str = "mock"  # "mock", "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

