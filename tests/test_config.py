"""Tests for configuration module."""

from __future__ import annotations

import pytest

from app.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_parse_addresses_list(self):
        """Test parsing addresses from a list."""
        settings = Settings(
            XRPL_WS_URL="wss://test.example.com",
            XRPL_RPC_URL="https://test.example.com",
            XRPL_ACCOUNT_ADDRESSES=["rAddr1", "rAddr2"],
            DB_PATH=":memory:",
            API_KEY="test-key-12345",
        )
        assert settings.xrpl_account_addresses == ["rAddr1", "rAddr2"]

    def test_parse_addresses_string(self):
        """Test parsing addresses from comma-separated string."""
        settings = Settings(
            XRPL_WS_URL="wss://test.example.com",
            XRPL_RPC_URL="https://test.example.com",
            XRPL_ACCOUNT_ADDRESSES="rAddr1, rAddr2, rAddr3",
            DB_PATH=":memory:",
            API_KEY="test-key-12345",
        )
        assert settings.xrpl_account_addresses == ["rAddr1", "rAddr2", "rAddr3"]

    def test_parse_addresses_empty(self):
        """Test parsing empty addresses."""
        settings = Settings(
            XRPL_WS_URL="wss://test.example.com",
            XRPL_RPC_URL="https://test.example.com",
            XRPL_ACCOUNT_ADDRESSES="",
            DB_PATH=":memory:",
            API_KEY="test-key-12345",
        )
        assert settings.xrpl_account_addresses == []

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.xrpl_ws_url == "wss://s1.ripple.com/"
        assert settings.smtp_port == 587
        assert settings.alert_min_xrp == 50.0
        assert settings.enable_desktop_notifications is False

    def test_webhook_url_validation_valid(self):
        """Test valid webhook URL validation."""
        settings = Settings(
            API_KEY="test-key-12345",
            webhook_url="https://example.com/webhook",
        )
        assert settings.webhook_url == "https://example.com/webhook"

    def test_webhook_url_validation_invalid(self):
        """Test invalid webhook URL validation."""
        with pytest.raises(ValueError, match="Webhook URL must start with"):
            Settings(
                API_KEY="test-key-12345",
                webhook_url="ftp://invalid.com",
            )

    def test_smtp_port_bounds(self):
        """Test SMTP port validation."""
        # Valid port
        settings = Settings(API_KEY="test-key-12345", smtp_port=25)
        assert settings.smtp_port == 25

        # Invalid port (too low)
        with pytest.raises(ValueError):
            Settings(API_KEY="test-key-12345", smtp_port=0)

        # Invalid port (too high)
        with pytest.raises(ValueError):
            Settings(API_KEY="test-key-12345", smtp_port=70000)

    def test_alert_min_xrp_non_negative(self):
        """Test alert_min_xrp must be non-negative."""
        with pytest.raises(ValueError):
            Settings(API_KEY="test-key-12345", alert_min_xrp=-10.0)

    def test_api_key_min_length(self):
        """Test API key minimum length."""
        with pytest.raises(ValueError):
            Settings(api_key="short")
