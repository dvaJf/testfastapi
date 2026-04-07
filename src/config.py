from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    SECRET: str = "secret"
    SECRET_REFRESH: str = "secret_refresh"
    FIRST_ADMIN_EMAIL: str | None = None
    class Config:
        env_file = ".env"


settings = Settings()