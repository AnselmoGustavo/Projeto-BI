import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class DbConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "steam_dw")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    schema: str = os.getenv("DB_SCHEMA", "steam_dw")


@dataclass(frozen=True)
class ApiConfig:
    steam_api_base_url: str = os.getenv("STEAM_API_BASE_URL", "https://api.steampowered.com")
    steam_store_base_url: str = os.getenv("STEAM_STORE_BASE_URL", "https://store.steampowered.com")
    request_delay_seconds: float = float(os.getenv("ETL_REQUEST_DELAY", "0.4"))
    timeout_seconds: int = int(os.getenv("ETL_TIMEOUT", "15"))


db_config = DbConfig()
api_config = ApiConfig()
