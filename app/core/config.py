import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLAUDE_API_KEY: str
    JWT_SECRET: str = "your-256-bit-secret-key-here"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
