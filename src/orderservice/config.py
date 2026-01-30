import logging
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "APP_"


settings = Settings()


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)