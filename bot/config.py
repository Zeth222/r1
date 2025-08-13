"""Configuration management using pydantic."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, field_validator
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    MODE: Literal["viewer", "active"] = "viewer"
    NETWORK: str = "arbitrum"
    UNISWAP_SUBGRAPH_URL: AnyUrl = "https://example.com"
    WALLET_ADDRESS: str = "0x0"
    PRIVATE_KEY: str | None = None
    HL_API_KEY: str | None = None
    HL_API_SECRET: str | None = None
    TELEGRAM_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    PAIR: str = "WETH/USDC"
    BASE_TOKEN: str = "WETH"
    QUOTE_TOKEN: str = "USDC"
    HEDGE_LEVERAGE_TARGET: float = 2.0
    DELTA_TOLERANCE_PCT: float = 0.005
    COOLDOWN_SEC: int = 15
    FUNDING_ALERT_PCT: float = 0.15
    DAILY_REPORT_HOUR: int = 20
    WEEKLY_REPORT_DOW: int = 7  # 1=Monday, 7=Sunday
    TZ: str = "America/Sao_Paulo"
    ENABLE_LP_EXECUTIONS: bool = False
    MAX_SLIPPAGE_BPS: int = 20
    MAX_RETRY: int = 5
    RETRY_BACKOFF_SEC: float = 2.0
    MIN_MARGIN_BUFFER_PCT: float = 0.25
    ATR_LOOKBACK_MIN: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("MODE", mode="before")
    def _lower_mode(cls, v: str) -> str:  # noqa: D401
        """Normalize mode to lowercase."""
        return v.lower()

    @field_validator("WEEKLY_REPORT_DOW")
    def _normalize_weekly_report_dow(cls, v: int) -> int:
        """Ensure 1-7 input and convert to 0-6 for CronTrigger."""
        if not 1 <= v <= 7:
            raise ValueError("WEEKLY_REPORT_DOW must be between 1 and 7")
        return (v - 1) % 7


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
