import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLAUDE_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
