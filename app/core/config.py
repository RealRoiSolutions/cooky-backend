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
            # Limpiamos cualquier esquema sync que pueda venir
            # 1. Si viene "postgres://", lo cambiamos
            # 2. Si viene "postgresql://", tambien lo cambiamos
            # Para estar 100% seguros, forzamos el prefijo.
            
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Spoonacular
    SPOONACULAR_API_KEY: str = ""
    
    # DeepL Translation
    DEEPL_API_KEY: str = ""
    
    # Env
    ENVIRONMENT: str = "dev"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
