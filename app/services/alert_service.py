from datetime import datetime

from sqlalchemy import select

from ..db import SessionLocal
from ..models import AlertEvent, AlertRule
from ..schemas import AlertRuleCreate


class AlertService:
    def list(self, status: str | None = None):
        with SessionLocal() as session:
            stmt = select(AlertEvent).order_by(AlertEvent.created_at.desc())
            if status:
                stmt = stmt.where(AlertEvent.status == status)
            return [
                {
                    "id": alert.id,
                    "message": alert.message,
                    "status": alert.status,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in session.scalars(stmt).all()
            ]

    def create(self, rule: AlertRuleCreate):
        with SessionLocal() as session:
            model = AlertRule(**rule.model_dump())
            session.add(model)
            session.commit()
            session.refresh(model)
            return {"id": model.id, "name": model.name}

    def acknowledge(self, alert_id: int):
        with SessionLocal() as session:
            alert = session.get(AlertEvent, alert_id)
            if not alert:
                return None
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow()
            session.commit()
            return {"id": alert_id, "status": alert.status}
