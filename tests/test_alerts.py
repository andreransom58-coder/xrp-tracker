"""Tests for alert engine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.alerts import AlertEngine
from app.models import AlertRule


class TestAlertEngine:
    """Tests for AlertEngine class."""

    @pytest.fixture
    def alert_engine(self):
        """Create an AlertEngine instance for testing."""
        with patch("app.alerts.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                alert_min_xrp=50.0,
                webhook_url=None,
                smtp_host=None,
                smtp_to=None,
                enable_desktop_notifications=False,
            )
            return AlertEngine()

    def test_matches_rule_amount_threshold(self, alert_engine):
        """Test rule matching with amount threshold."""
        rule = MagicMock(spec=AlertRule)
        rule.min_amount_xrp = 100.0
        rule.direction = None
        rule.counterparty = None
        rule.memo_keyword = None

        # Amount above threshold
        tx_data = {"amount_xrp": 150.0, "direction": "inbound"}
        assert alert_engine._matches_rule(rule, tx_data) is True

        # Amount below threshold
        tx_data = {"amount_xrp": 50.0, "direction": "inbound"}
        assert alert_engine._matches_rule(rule, tx_data) is False

    def test_matches_rule_direction(self, alert_engine):
        """Test rule matching with direction filter."""
        rule = MagicMock(spec=AlertRule)
        rule.min_amount_xrp = None
        rule.direction = "inbound"
        rule.counterparty = None
        rule.memo_keyword = None

        # Matching direction
        tx_data = {"amount_xrp": 100.0, "direction": "inbound"}
        assert alert_engine._matches_rule(rule, tx_data) is True

        # Non-matching direction
        tx_data = {"amount_xrp": 100.0, "direction": "outbound"}
        assert alert_engine._matches_rule(rule, tx_data) is False

    def test_matches_rule_counterparty(self, alert_engine):
        """Test rule matching with counterparty filter."""
        rule = MagicMock(spec=AlertRule)
        rule.min_amount_xrp = None
        rule.direction = None
        rule.counterparty = "rTestAddress"
        rule.memo_keyword = None

        # Matching counterparty
        tx_data = {"amount_xrp": 100.0, "direction": "inbound", "counterparty": "rTestAddress"}
        assert alert_engine._matches_rule(rule, tx_data) is True

        # Non-matching counterparty
        tx_data = {"amount_xrp": 100.0, "direction": "inbound", "counterparty": "rOtherAddress"}
        assert alert_engine._matches_rule(rule, tx_data) is False

    def test_matches_rule_memo_keyword(self, alert_engine):
        """Test rule matching with memo keyword filter."""
        rule = MagicMock(spec=AlertRule)
        rule.min_amount_xrp = None
        rule.direction = None
        rule.counterparty = None
        rule.memo_keyword = "payment"

        # Matching memo (case insensitive)
        tx_data = {"amount_xrp": 100.0, "direction": "inbound", "memo": "Payment for services"}
        assert alert_engine._matches_rule(rule, tx_data) is True

        # Non-matching memo
        tx_data = {"amount_xrp": 100.0, "direction": "inbound", "memo": "Test transaction"}
        assert alert_engine._matches_rule(rule, tx_data) is False

        # No memo
        tx_data = {"amount_xrp": 100.0, "direction": "inbound", "memo": None}
        assert alert_engine._matches_rule(rule, tx_data) is False

    def test_matches_rule_all_filters(self, alert_engine):
        """Test rule matching with all filters combined."""
        rule = MagicMock(spec=AlertRule)
        rule.min_amount_xrp = 50.0
        rule.direction = "inbound"
        rule.counterparty = "rTestAddress"
        rule.memo_keyword = "invoice"

        # All conditions match
        tx_data = {
            "amount_xrp": 100.0,
            "direction": "inbound",
            "counterparty": "rTestAddress",
            "memo": "Invoice #123",
        }
        assert alert_engine._matches_rule(rule, tx_data) is True

        # One condition fails
        tx_data = {
            "amount_xrp": 100.0,
            "direction": "outbound",  # Wrong direction
            "counterparty": "rTestAddress",
            "memo": "Invoice #123",
        }
        assert alert_engine._matches_rule(rule, tx_data) is False


class TestAlertDispatch:
    """Tests for alert dispatch functionality."""

    @pytest.fixture
    def alert_engine_with_webhook(self):
        """Create AlertEngine with webhook configured."""
        with patch("app.alerts.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                alert_min_xrp=50.0,
                webhook_url="https://example.com/webhook",
                smtp_host=None,
                smtp_to=None,
                enable_desktop_notifications=False,
            )
            return AlertEngine()

    @patch("app.alerts.requests.post")
    def test_send_webhook_success(self, mock_post, alert_engine_with_webhook):
        """Test successful webhook dispatch."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()

        alert_engine_with_webhook._send_webhook(1, "Test message", "TX123")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["id"] == 1
        assert call_kwargs["json"]["message"] == "Test message"
        assert call_kwargs["json"]["tx_hash"] == "TX123"

    @patch("app.alerts.requests.post")
    def test_send_webhook_timeout(self, mock_post, alert_engine_with_webhook):
        """Test webhook timeout handling."""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        # Should not raise exception
        alert_engine_with_webhook._send_webhook(1, "Test message", "TX123")

    @patch("app.alerts.requests.post")
    def test_send_webhook_connection_error(self, mock_post, alert_engine_with_webhook):
        """Test webhook connection error handling."""
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError()

        # Should not raise exception
        alert_engine_with_webhook._send_webhook(1, "Test message", "TX123")
