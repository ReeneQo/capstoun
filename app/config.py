from functools import lru_cache

from psycopg.conninfo import make_conninfo
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    app_version: str = "dev"
    greeting: str = "Добро пожаловать в гостевую книгу!"

    @property
    def database_conninfo(self) -> str:
        return make_conninfo(
            user=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            dbname=self.postgres_db,
            host=self.postgres_host,
            port=self.postgres_port,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
