from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Any
from pydantic import field_validator, ValidationInfo


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cooky"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cooky"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # Si Render envía postgres://..., lo convertimos a postgresql+asyncpg://...
            return v.replace("postgres://", "postgresql+asyncpg://")
        return v

    # Spoonacular
    SPOONACULAR_API_KEY: str = ""

    # Deepl Translation
    DEEPL_API_KEY: str = ""

    # Env
    ENVIRONMENT: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
