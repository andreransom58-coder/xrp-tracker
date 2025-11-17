from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict

load_dotenv()


class Settings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    xrpl_ws_url: str = Field(
        default="wss://s1.ripple.com/",
        alias="XRPL_WS_URL",
    )
    xrpl_rpc_url: str = Field(
        default="https://s2.ripple.com:51234/",
        alias="XRPL_RPC_URL",
    )
    xrpl_account_addresses: List[str] = Field(
        default_factory=list,
        alias="XRPL_ACCOUNT_ADDRESSES",
    )
    db_path: Path = Field(default=Path("data/xrp_monitor.db"), alias="DB_PATH")
    api_key: str = Field(default="change-me", alias="API_KEY")
    alert_min_xrp: float = Field(default=50.0, alias="ALERT_MIN_XRP")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_to: str | None = Field(default=None, alias="SMTP_TO")
    enable_desktop_notifications: bool = Field(
        default=False, alias="ENABLE_DESKTOP_NOTIFICATIONS"
    )

    @classmethod
    def parse_addresses(cls, value: str | List[str] | None) -> List[str]:
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [addr.strip() for addr in value.split(",") if addr.strip()]

    @classmethod
    def model_validate_env(cls) -> "Settings":
        raw = {k: v for k, v in os.environ.items()}
        if "XRPL_ACCOUNT_ADDRESSES" in raw:
            raw["XRPL_ACCOUNT_ADDRESSES"] = cls.parse_addresses(
                raw["XRPL_ACCOUNT_ADDRESSES"]
            )
        return cls.model_validate(raw)


@lru_cache
def get_settings() -> Settings:
    return Settings.model_validate_env()
