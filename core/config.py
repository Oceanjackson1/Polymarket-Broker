import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


def _env_file() -> str:
    """Allow ENV_FILE env var to override which .env file to load.
    Enables: ENV_FILE=.env.test pytest ...
    """
    return os.getenv("ENV_FILE", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file(), extra="ignore")

    # Database
    database_url: str
    redis_url: str

    # Security
    secret_key: str
    fernet_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Polymarket
    polymarket_clob_host: str = "https://clob.polymarket.com"
    polymarket_gamma_host: str = "https://gamma-api.polymarket.com"
    polymarket_private_key: str = ""
    polymarket_api_key: str = ""
    polymarket_chain_id: int = 137
    polymarket_rpc_url: str = "https://polygon-rpc.com/"
    polymarket_fee_address: str = ""

    # App
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
