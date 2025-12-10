"""Transaction service for querying transaction history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import desc, func, select

from ..db import SessionLocal
from ..models import Transaction

logger = structlog.get_logger(__name__)


class TransactionService:
    """Service for transaction queries and aggregations."""

    def list(
        self,
        limit: int = 50,
        direction: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List transactions with optional filtering.

        Args:
            limit: Maximum number of transactions to return
            direction: Filter by direction ('inbound' or 'outbound')

        Returns:
            List of transaction dictionaries
        """
        logger.debug("tx_service.list", limit=limit, direction=direction)

        with SessionLocal() as session:
            stmt = (
                select(Transaction)
                .order_by(desc(Transaction.timestamp))
                .limit(limit)
            )
            if direction:
                stmt = stmt.where(Transaction.direction == direction)

            rows = session.scalars(stmt).all()

            return [
                {
                    "hash": tx.hash,
                    "timestamp": tx.timestamp.isoformat(),
                    "amount_xrp": tx.amount_xrp,
                    "direction": tx.direction,
                    "counterparty": self._get_counterparty(tx),
                    "memo": tx.memo,
                }
                for tx in rows
            ]

    def inflow_outflow_24h(self) -> tuple[float, float]:
        """
        Calculate 24-hour inflow and outflow totals.

        Returns:
            Tuple of (inflow, outflow) amounts in XRP
        """
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        with SessionLocal() as session:
            inflow_stmt = select(func.sum(Transaction.amount_xrp)).where(
                Transaction.direction == "inbound",
                Transaction.timestamp >= since,
            )
            inbound: float = session.execute(inflow_stmt).scalar() or 0.0

            outflow_stmt = select(func.sum(Transaction.amount_xrp)).where(
                Transaction.direction == "outbound",
                Transaction.timestamp >= since,
            )
            outbound: float = session.execute(outflow_stmt).scalar() or 0.0

        logger.debug(
            "tx_service.flow_24h",
            inbound=inbound,
            outbound=outbound,
        )

        return inbound, outbound

    def get_by_hash(self, tx_hash: str) -> Transaction | None:
        """
        Get a transaction by its hash.

        Args:
            tx_hash: Transaction hash to look up

        Returns:
            Transaction object or None if not found
        """
        with SessionLocal() as session:
            return session.get(Transaction, tx_hash)

    def _get_counterparty(self, tx: Transaction) -> str | None:
        """Get counterparty address based on transaction direction."""
        if tx.direction == "outbound":
            return tx.destination
        return tx.account
