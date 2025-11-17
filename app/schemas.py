from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionRow(BaseModel):
    hash: str
    timestamp: datetime
    amount_xrp: float
    direction: str
    counterparty: Optional[str]
    memo: Optional[str]


class DashboardSummary(BaseModel):
    total_balance_xrp: float = Field(default=0.0)
    inflow_24h: float = Field(default=0.0)
    outflow_24h: float = Field(default=0.0)
    alert_count: int = Field(default=0)


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    transactions: List[TransactionRow]
    alerts: List[dict]
    charts: dict


class AlertRuleCreate(BaseModel):
    name: str
    min_amount_xrp: Optional[float] = None
    direction: Optional[str] = Field(default=None, pattern="^(inbound|outbound)$")
    counterparty: Optional[str] = None
    memo_keyword: Optional[str] = None


class AlertAction(BaseModel):
    alert_id: int
    status: str
