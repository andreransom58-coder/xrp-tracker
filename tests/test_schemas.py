"""Tests for Pydantic schemas."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas import (
    AlertRuleCreate,
    AlertStatus,
    DashboardSummary,
    HealthResponse,
    TransactionDirection,
    TransactionRow,
)


class TestTransactionDirection:
    """Tests for TransactionDirection enum."""

    def test_inbound_value(self):
        """Test inbound direction value."""
        assert TransactionDirection.INBOUND.value == "inbound"

    def test_outbound_value(self):
        """Test outbound direction value."""
        assert TransactionDirection.OUTBOUND.value == "outbound"


class TestAlertStatus:
    """Tests for AlertStatus enum."""

    def test_open_value(self):
        """Test open status value."""
        assert AlertStatus.OPEN.value == "open"

    def test_acknowledged_value(self):
        """Test acknowledged status value."""
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"


class TestTransactionRow:
    """Tests for TransactionRow schema."""

    def test_valid_transaction(self):
        """Test creating valid transaction row."""
        tx = TransactionRow(
            hash="ABC123",
            timestamp=datetime.now(timezone.utc),
            amount_xrp=100.0,
            direction="inbound",
            counterparty="rSomeAddress",
            memo="Test memo",
        )
        assert tx.hash == "ABC123"
        assert tx.amount_xrp == 100.0

    def test_optional_fields(self):
        """Test transaction with optional fields."""
        tx = TransactionRow(
            hash="ABC123",
            timestamp=datetime.now(timezone.utc),
            amount_xrp=50.0,
            direction="outbound",
        )
        assert tx.counterparty is None
        assert tx.memo is None


class TestDashboardSummary:
    """Tests for DashboardSummary schema."""

    def test_default_values(self):
        """Test default summary values."""
        summary = DashboardSummary()
        assert summary.total_balance_xrp == 0.0
        assert summary.inflow_24h == 0.0
        assert summary.outflow_24h == 0.0
        assert summary.alert_count == 0

    def test_custom_values(self):
        """Test summary with custom values."""
        summary = DashboardSummary(
            total_balance_xrp=1000.0,
            inflow_24h=500.0,
            outflow_24h=200.0,
            alert_count=3,
        )
        assert summary.total_balance_xrp == 1000.0
        assert summary.inflow_24h == 500.0


class TestAlertRuleCreate:
    """Tests for AlertRuleCreate schema."""

    def test_valid_rule(self):
        """Test creating valid alert rule."""
        rule = AlertRuleCreate(
            name="Test Rule",
            min_amount_xrp=100.0,
            direction="inbound",
        )
        assert rule.name == "Test Rule"
        assert rule.min_amount_xrp == 100.0

    def test_direction_validation(self):
        """Test direction pattern validation."""
        # Valid directions
        rule1 = AlertRuleCreate(name="Test", direction="inbound")
        assert rule1.direction == "inbound"

        rule2 = AlertRuleCreate(name="Test", direction="outbound")
        assert rule2.direction == "outbound"

        # Invalid direction
        with pytest.raises(ValueError):
            AlertRuleCreate(name="Test", direction="invalid")

    def test_name_required(self):
        """Test name is required."""
        with pytest.raises(ValueError):
            AlertRuleCreate(name="")

    def test_min_amount_non_negative(self):
        """Test min_amount_xrp must be non-negative."""
        with pytest.raises(ValueError):
            AlertRuleCreate(name="Test", min_amount_xrp=-10.0)

    def test_optional_fields(self):
        """Test optional fields default to None."""
        rule = AlertRuleCreate(name="Test Rule")
        assert rule.min_amount_xrp is None
        assert rule.direction is None
        assert rule.counterparty is None
        assert rule.memo_keyword is None


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_health_response(self):
        """Test creating health response."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            database="healthy",
            timestamp=datetime.now(timezone.utc),
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
