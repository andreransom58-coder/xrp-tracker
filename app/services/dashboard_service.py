"""Dashboard service for aggregating metrics and transaction data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import case, desc, func, select

from ..db import SessionLocal
from ..models import AlertEvent, Transaction
from ..schemas import DashboardResponse, DashboardSummary, TransactionRow

logger = structlog.get_logger(__name__)


class DashboardService:
    """Service for building dashboard metrics and aggregated data."""

    def build(self) -> DashboardResponse:
        """
        Build complete dashboard response with metrics and recent data.

        Returns:
            DashboardResponse containing:
                - Summary metrics (balance, 24h flow, alert count)
                - Recent transactions (last 25)
                - Open alerts
                - Chart data for visualization
        """
        logger.debug("dashboard.build_start")

        with SessionLocal() as session:
            # Calculate net balance using modern select() style
            balance_stmt = select(
                func.sum(
                    case(
                        (Transaction.direction == "inbound", Transaction.amount_xrp),
                        else_=-Transaction.amount_xrp,
                    )
                )
            )
            balance: float = session.execute(balance_stmt).scalar() or 0.0

            # Calculate 24h inflow/outflow
            since = datetime.now(timezone.utc) - timedelta(hours=24)

            inflow_stmt = select(func.sum(Transaction.amount_xrp)).where(
                Transaction.direction == "inbound",
                Transaction.timestamp >= since,
            )
            inflow: float = session.execute(inflow_stmt).scalar() or 0.0

            outflow_stmt = select(func.sum(Transaction.amount_xrp)).where(
                Transaction.direction == "outbound",
                Transaction.timestamp >= since,
            )
            outflow: float = session.execute(outflow_stmt).scalar() or 0.0

            # Get open alerts
            alerts_stmt = (
                select(AlertEvent)
                .where(AlertEvent.status == "open")
                .order_by(desc(AlertEvent.created_at))
            )
            alerts = session.scalars(alerts_stmt).all()

            # Get recent transactions
            txs_stmt = (
                select(Transaction)
                .order_by(desc(Transaction.timestamp))
                .limit(25)
            )
            txs = session.scalars(txs_stmt).all()

        # Build summary
        summary = DashboardSummary(
            total_balance_xrp=balance,
            inflow_24h=inflow,
            outflow_24h=outflow,
            alert_count=len(alerts),
        )

        # Build chart data points
        chart_points: list[dict[str, Any]] = [
            {
                "timestamp": tx.timestamp.isoformat(),
                "balance": tx.amount_xrp if tx.direction == "inbound" else -tx.amount_xrp,
            }
            for tx in reversed(txs)
        ]

        # Build transaction rows
        transaction_rows = [
            TransactionRow(
                hash=tx.hash,
                timestamp=tx.timestamp,
                amount_xrp=tx.amount_xrp,
                direction=tx.direction,
                counterparty=self._get_counterparty(tx),
                memo=tx.memo,
            )
            for tx in txs
        ]

        # Build alert items
        alert_items = [
            {
                "id": alert.id,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ]

        logger.debug(
            "dashboard.build_complete",
            tx_count=len(txs),
            alert_count=len(alerts),
        )

        return DashboardResponse(
            summary=summary,
            transactions=transaction_rows,
            alerts=alert_items,
            charts={"net_flow": chart_points},
        )

    def _get_counterparty(self, tx: Transaction) -> str | None:
        """Get counterparty address based on transaction direction."""
        if tx.direction == "outbound":
            return tx.destination
        return tx.account
