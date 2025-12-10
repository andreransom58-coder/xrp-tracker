"""Alert service for managing alert rules and events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select

from ..db import SessionLocal
from ..models import AlertEvent, AlertRule
from ..schemas import AlertRuleCreate

logger = structlog.get_logger(__name__)


class AlertService:
    """Service for alert rule and event management."""

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        """
        List alert events with optional status filtering.

        Args:
            status: Filter by status ('open' or 'acknowledged')

        Returns:
            List of alert event dictionaries
        """
        logger.debug("alert_service.list", status=status)

        with SessionLocal() as session:
            stmt = select(AlertEvent).order_by(AlertEvent.created_at.desc())
            if status:
                stmt = stmt.where(AlertEvent.status == status)

            alerts = session.scalars(stmt).all()

            return [
                {
                    "id": alert.id,
                    "message": alert.message,
                    "status": alert.status,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in alerts
            ]

    def create(self, rule: AlertRuleCreate) -> dict[str, Any]:
        """
        Create a new alert rule.

        Args:
            rule: Alert rule creation parameters

        Returns:
            Dictionary with created rule ID and name
        """
        with SessionLocal() as session:
            model = AlertRule(**rule.model_dump())
            session.add(model)
            session.commit()
            session.refresh(model)

            logger.info(
                "alert_service.rule_created",
                rule_id=model.id,
                name=model.name,
            )

            return {"id": model.id, "name": model.name}

    def acknowledge(self, alert_id: int) -> dict[str, Any] | None:
        """
        Acknowledge an alert event.

        Args:
            alert_id: ID of the alert to acknowledge

        Returns:
            Dictionary with alert ID and status, or None if not found
        """
        with SessionLocal() as session:
            alert = session.get(AlertEvent, alert_id)
            if not alert:
                logger.warning("alert_service.acknowledge_not_found", alert_id=alert_id)
                return None

            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.now(timezone.utc)
            session.commit()

            logger.info("alert_service.acknowledged", alert_id=alert_id)

            return {"id": alert_id, "status": alert.status}

    def get_active_rules(self) -> list[AlertRule]:
        """
        Get all active alert rules.

        Returns:
            List of active AlertRule objects
        """
        with SessionLocal() as session:
            stmt = select(AlertRule).where(AlertRule.active.is_(True))
            return list(session.scalars(stmt).all())
