"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionDirection(str, Enum):
    """Direction of a transaction relative to monitored wallets."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class AlertStatus(str, Enum):
    """Status of an alert event."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"


class TransactionRow(BaseModel):
    """Schema for transaction data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    hash: str = Field(..., description="Unique transaction hash")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    amount_xrp: float = Field(..., ge=0, description="Amount in XRP")
    direction: str = Field(..., description="Transaction direction (inbound/outbound)")
    counterparty: str | None = Field(None, description="Other party's address")
    memo: str | None = Field(None, description="Transaction memo if present")


class DashboardSummary(BaseModel):
    """Summary metrics for the dashboard."""

    total_balance_xrp: float = Field(default=0.0, description="Net balance from tracked transactions")
    inflow_24h: float = Field(default=0.0, ge=0, description="Total inbound XRP in last 24 hours")
    outflow_24h: float = Field(default=0.0, ge=0, description="Total outbound XRP in last 24 hours")
    alert_count: int = Field(default=0, ge=0, description="Number of open alerts")


class AlertEventResponse(BaseModel):
    """Schema for alert event in API responses."""

    id: int = Field(..., description="Alert event ID")
    message: str = Field(..., description="Alert message")
    created_at: str = Field(..., description="ISO timestamp when alert was created")


class ChartData(BaseModel):
    """Schema for chart data points."""

    net_flow: list[dict[str, Any]] = Field(
        default_factory=list, description="Net flow chart data points"
    )


class DashboardResponse(BaseModel):
    """Complete dashboard response with all metrics and data."""

    summary: DashboardSummary = Field(..., description="Summary metrics")
    transactions: list[TransactionRow] = Field(..., description="Recent transactions")
    alerts: list[dict[str, Any]] = Field(..., description="Open alerts")
    charts: ChartData | dict[str, Any] = Field(..., description="Chart data")


class AlertRuleCreate(BaseModel):
    """Schema for creating a new alert rule."""

    name: str = Field(..., min_length=1, max_length=128, description="Alert rule name")
    min_amount_xrp: float | None = Field(
        default=None, ge=0, description="Minimum XRP amount to trigger alert"
    )
    direction: str | None = Field(
        default=None,
        pattern="^(inbound|outbound)$",
        description="Transaction direction filter",
    )
    counterparty: str | None = Field(
        default=None, max_length=64, description="Specific counterparty address filter"
    )
    memo_keyword: str | None = Field(
        default=None, max_length=128, description="Keyword to match in transaction memo"
    )

    @field_validator("min_amount_xrp", mode="after")
    @classmethod
    def validate_amount(cls, v: float | None) -> float | None:
        """Ensure amount is not negative."""
        if v is not None and v < 0:
            raise ValueError("min_amount_xrp cannot be negative")
        return v


class AlertRuleResponse(BaseModel):
    """Schema for alert rule response."""

    id: int = Field(..., description="Alert rule ID")
    name: str = Field(..., description="Alert rule name")


class AlertAction(BaseModel):
    """Schema for alert action response."""

    alert_id: int = Field(..., description="Alert event ID")
    status: str = Field(..., description="Current alert status")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Health check timestamp")


class TransactionListResponse(BaseModel):
    """Response schema for transaction list endpoint."""

    items: list[dict[str, Any]] = Field(..., description="List of transactions")


class AlertListResponse(BaseModel):
    """Response schema for alert list endpoint."""

    items: list[dict[str, Any]] = Field(..., description="List of alerts")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Error message")
