from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Dict, Any

import requests
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from plyer import notification
from sqlalchemy import select

from .config import get_settings
from .db import SessionLocal
from .models import AlertEvent, AlertRule

logger = structlog.get_logger(__name__)


class AlertEngine:
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def evaluate(self, tx_data: Dict[str, Any]):
        with SessionLocal() as session:
            rules = session.scalars(
                select(AlertRule).where(AlertRule.active.is_(True))
            ).all()
        triggered = []
        for rule in rules:
            if rule.min_amount_xrp and tx_data["amount_xrp"] < rule.min_amount_xrp:
                continue
            if rule.direction and tx_data["direction"] != rule.direction:
                continue
            if rule.counterparty and tx_data.get("counterparty") != rule.counterparty:
                continue
            if rule.memo_keyword and (
                not tx_data.get("memo")
                or rule.memo_keyword.lower() not in tx_data["memo"].lower()
            ):
                continue
            triggered.append(rule)
        if not triggered and tx_data["amount_xrp"] < self.settings.alert_min_xrp:
            return
        message = (
            f"XRP Tx {tx_data['direction']} {tx_data['amount_xrp']:.2f} XRP "
            f"with {tx_data.get('counterparty')}"
        )
        await self.dispatch_alert(
            message=message,
            tx_hash=tx_data["hash"],
            rule_ids=[rule.id for rule in triggered],
        )

    async def dispatch_alert(self, message: str, tx_hash: str, rule_ids: list[int]):
        with SessionLocal() as session:
            alert = AlertEvent(
                rule_id=rule_ids[0] if rule_ids else None,
                transaction_hash=tx_hash,
                message=message,
            )
            session.add(alert)
            session.commit()
            alert_id = alert.id
        logger.info("alert.triggered", message=message, tx_hash=tx_hash)
        if self.settings.webhook_url:
            self._send_webhook(alert_id, message, tx_hash)
        if self.settings.smtp_host and self.settings.smtp_to:
            self._send_email(alert_id, message)
        if self.settings.enable_desktop_notifications:
            self._notify_desktop(message)

    def _send_webhook(self, alert_id: int, message: str, tx_hash: str):
        payload = {"id": alert_id, "message": message, "tx_hash": tx_hash}
        try:
            requests.post(self.settings.webhook_url, json=payload, timeout=5)
        except requests.RequestException as exc:
            logger.warning("alert.webhook_failed", error=str(exc))

    def _send_email(self, alert_id: int, message: str):
        msg = EmailMessage()
        msg["Subject"] = f"XRP Alert #{alert_id}"
        msg["From"] = self.settings.smtp_from
        msg["To"] = self.settings.smtp_to
        msg.set_content(message)
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
                smtp.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(msg)
        except Exception as exc:
            logger.warning("alert.email_failed", error=str(exc))

    def _notify_desktop(self, message: str):
        try:
            notification.notify(
                title="XRP Alert",
                message=message,
                app_name="XRP Monitor",
                timeout=5,
            )
        except Exception as exc:
            logger.warning("alert.desktop_failed", error=str(exc))
