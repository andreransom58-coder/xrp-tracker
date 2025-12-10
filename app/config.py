"""Application configuration management using Pydantic settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

load_dotenv()


class Settings(BaseModel):
    """
    Application settings loaded from environment variables.

    All settings can be configured via environment variables with the same name
    (case-insensitive). For example, `XRPL_WS_URL` maps to `xrpl_ws_url`.
    """

    model_config = ConfigDict(populate_by_name=True, frozen=False)

    # XRPL Connection Settings
    xrpl_ws_url: str = Field(
        default="wss://s1.ripple.com/",
        alias="XRPL_WS_URL",
        description="WebSocket URL for XRPL node connection",
    )
    xrpl_rpc_url: str = Field(
        default="https://s2.ripple.com:51234/",
        alias="XRPL_RPC_URL",
        description="JSON-RPC URL for XRPL node connection",
    )
    xrpl_account_addresses: list[str] = Field(
        default_factory=list,
        alias="XRPL_ACCOUNT_ADDRESSES",
        description="Comma-separated list of XRP wallet addresses to monitor",
    )

    # Database Settings
    db_path: Path = Field(
        default=Path("data/xrp_monitor.db"),
        alias="DB_PATH",
        description="Path to SQLite database file",
    )

    # API Settings
    api_key: str = Field(
        default="change-me",
        alias="API_KEY",
        description="API key for authenticating requests",
        min_length=8,
    )

    # Alert Settings
    alert_min_xrp: float = Field(
        default=50.0,
        alias="ALERT_MIN_XRP",
        description="Minimum XRP amount to trigger an alert",
        ge=0.0,
    )
    webhook_url: str | None = Field(
        default=None,
        alias="WEBHOOK_URL",
        description="Webhook URL for alert notifications",
    )

    # SMTP Settings
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT", ge=1, le=65535)
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_to: str | None = Field(default=None, alias="SMTP_TO")

    # Notification Settings
    enable_desktop_notifications: bool = Field(
        default=False,
        alias="ENABLE_DESKTOP_NOTIFICATIONS",
        description="Enable desktop notifications for alerts",
    )

    # Class-level constants
    VALID_DIRECTIONS: ClassVar[set[str]] = {"inbound", "outbound"}

    @field_validator("xrpl_account_addresses", mode="before")
    @classmethod
    def parse_addresses(cls, value: str | list[str] | None) -> list[str]:
        """Parse comma-separated addresses into a list."""
        if not value:
            return []
        if isinstance(value, list):
            return [addr.strip() for addr in value if addr.strip()]
        return [addr.strip() for addr in value.split(",") if addr.strip()]

    @field_validator("webhook_url", mode="after")
    @classmethod
    def validate_webhook_url(cls, url: str | None) -> str | None:
        """Validate webhook URL format."""
        if url and not url.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return url

    @classmethod
    def model_validate_env(cls) -> Settings:
        """Create Settings instance from environment variables."""
        raw = {k: v for k, v in os.environ.items()}
        return cls.model_validate(raw)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: The application settings loaded from environment variables.
    """
    return Settings.model_validate_env()
