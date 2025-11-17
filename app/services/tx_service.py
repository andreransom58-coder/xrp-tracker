from datetime import datetime, timedelta

from sqlalchemy import select, desc, func

from ..db import SessionLocal
from ..models import Transaction


class TransactionService:
    def list(self, limit: int = 50, direction: str | None = None):
        with SessionLocal() as session:
            stmt = select(Transaction).order_by(desc(Transaction.timestamp)).limit(limit)
            if direction:
                stmt = stmt.where(Transaction.direction == direction)
            rows = session.scalars(stmt).all()
            return [
                {
                    "hash": tx.hash,
                    "timestamp": tx.timestamp.isoformat(),
                    "amount_xrp": tx.amount_xrp,
                    "direction": tx.direction,
                    "counterparty": tx.counterparty,
                    "memo": tx.memo,
                }
                for tx in rows
            ]

    def inflow_outflow_24h(self):
        since = datetime.utcnow() - timedelta(hours=24)
        with SessionLocal() as session:
            inbound = (
                session.query(func.sum(Transaction.amount_xrp))
                .filter(Transaction.direction == "inbound", Transaction.timestamp >= since)
                .scalar()
                or 0.0
            )
            outbound = (
                session.query(func.sum(Transaction.amount_xrp))
                .filter(
                    Transaction.direction == "outbound",
                    Transaction.timestamp >= since,
                )
                .scalar()
                or 0.0
            )
        return inbound, outbound
