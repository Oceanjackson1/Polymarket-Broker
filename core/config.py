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

    # Data Pipeline
    espn_api_base: str = "https://site.api.espn.com"
    coingecko_api_base: str = "https://api.coingecko.com"
    coingecko_api_key: str = ""
    disable_collectors: bool = False

    # CoinGlass
    coinglass_api_key: str = ""
    coinglass_api_base: str = "https://open-api-v4.coinglass.com"

    # Dome API
    dome_api_keys: str = ""  # comma-separated list of API keys
    dome_api_base: str = "https://api.domeapi.io/v1"
    dome_ws_enabled: bool = True
    dome_ws_key_count: int = 2  # keys reserved for WebSocket connections
    dome_cooldown_seconds: float = 10.0
    tracked_wallets: str = ""  # comma-separated wallet addresses for tracking

    # Open-Meteo
    open_meteo_ensemble_base: str = "https://ensemble-api.open-meteo.com"
    open_meteo_geocoding_base: str = "https://geocoding-api.open-meteo.com"

    # Sports APIs (P00)
    odds_api_key: str = ""  # the-odds-api.com
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    api_football_key: str = ""  # api-sports.io
    api_football_base: str = "https://v3.football.api-sports.io"
    balldontlie_api_key: str = ""  # balldontlie.io
    balldontlie_api_base: str = "https://api.balldontlie.io/v1"
    football_data_key: str = ""  # football-data.org
    football_data_base: str = "https://api.football-data.org/v4"

    # Live Orderbook (Tencent Cloud server)
    live_ob_binance_url: str = ""  # e.g. http://localhost:18080 (via SSH tunnel)
    live_ob_binance_api_key: str = ""
    live_ob_ssh_host: str = ""  # e.g. root@10.193.48.144
    live_ob_ssh_key_path: str = ""  # path to PEM file
    live_ob_polymarket_data_dir: str = "/data/polymarket-agent/output/orderbook"

    # DeepSeek AI
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    analysis_daily_quota_free: int = 10

    # Google OAuth
    google_client_id: str = ""

    # Telegram Bot
    tg_bot_token: str = ""
    tg_webhook_secret: str = ""  # random string to verify webhook origin
    tg_webhook_url: str = ""     # e.g. https://api.polydesk.eu.cc/api/v1/agent/tg-webhook
    tg_admin_chat_ids: str = ""  # comma-separated admin chat IDs
    tg_miniapp_url: str = ""     # e.g. https://polydesk.eu.cc/tg

    # App
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
