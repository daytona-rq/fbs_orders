from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: int  # Порт лучше хранить как int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    database_url: Optional[str]  # Может быть пустым, так как будет динамически генерироваться
    redis_url: str

    class Config:
        env_file = ".env"

    @property
    def DATABASE_URL_asyncpg(self):
        """Строка подключения для asyncpg"""
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

# Инициализация настроек
settings = Settings()
