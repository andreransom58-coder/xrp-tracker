from datetime import datetime, timedelta

from sqlalchemy import func, select, desc

from ..db import SessionLocal
from ..models import Transaction, AlertEvent
from ..schemas import DashboardResponse, DashboardSummary, TransactionRow


class DashboardService:
    def build(self) -> DashboardResponse:
        with SessionLocal() as session:
            balance = (
                session.query(
                    func.sum(
                        func.case(
                            (Transaction.direction == "inbound", Transaction.amount_xrp),
                            else_=-Transaction.amount_xrp,
                        )
                    )
                ).scalar()
                or 0.0
            )
            since = datetime.utcnow() - timedelta(hours=24)
            inflow = (
                session.query(func.sum(Transaction.amount_xrp))
                .filter(
                    Transaction.direction == "inbound", Transaction.timestamp >= since
                )
                .scalar()
                or 0.0
            )
            outflow = (
                session.query(func.sum(Transaction.amount_xrp))
                .filter(
                    Transaction.direction == "outbound",
                    Transaction.timestamp >= since,
                )
                .scalar()
                or 0.0
            )
            alerts = session.scalars(
                select(AlertEvent).where(AlertEvent.status == "open").order_by(
                    desc(AlertEvent.created_at)
                )
            ).all()
            txs = session.scalars(
                select(Transaction)
                .order_by(desc(Transaction.timestamp))
                .limit(25)
            ).all()
        summary = DashboardSummary(
            total_balance_xrp=balance, inflow_24h=inflow, outflow_24h=outflow, alert_count=len(alerts)
        )
        chart_points = [
            {
                "timestamp": tx.timestamp.isoformat(),
                "balance": tx.amount_xrp if tx.direction == "inbound" else -tx.amount_xrp,
            }
            for tx in reversed(txs)
        ]
        return DashboardResponse(
            summary=summary,
            transactions=[
                TransactionRow(
                    hash=tx.hash,
                    timestamp=tx.timestamp,
                    amount_xrp=tx.amount_xrp,
                    direction=tx.direction,
                    counterparty=tx.counterparty,
                    memo=tx.memo,
                )
                for tx in txs
            ],
            alerts=[{"id": alert.id, "message": alert.message, "created_at": alert.created_at.isoformat()} for alert in alerts],
            charts={"net_flow": chart_points},
        )
