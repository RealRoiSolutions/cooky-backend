from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cooky"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cooky"
    
    # Spoonacular
    SPOONACULAR_API_KEY: str
    
    # DeepL Translation
    DEEPL_API_KEY: str = ""
    
    # Env
    ENVIRONMENT: str = "dev"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
