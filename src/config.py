from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET: str
    SECRET_REFRESH: str
    FIRST_ADMIN_EMAIL: str
    FIRST_ADMIN_PASSWORD: str
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str
    FRONTEND_URL: str = "http://127.0.0.1:8000"
    API_BASE_URL: str = "http://127.0.0.1:8000/api"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

if os.getenv("VERCEL"):
    settings.FRONTEND_URL = "https://f1u.vercel.app/"
    settings.API_BASE_URL = "https://f1u.vercel.app/api"