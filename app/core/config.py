from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # API Configuration
    aqniet_api_url: str = "https://aqniet.site/api"
    aqniet_api_token: str
    madlen_api_url: str = "https://madlen.space/api"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Cache Configuration
    cache_ttl: int = 1800  # 30 minutes
    
    # API Timeout
    api_timeout: float = 30.0
    
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()