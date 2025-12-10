"""Alert engine for evaluating transactions and dispatching notifications."""

from __future__ import annotations

import smtplib
import socket
from email.message import EmailMessage
from typing import TYPE_CHECKING, Any

import requests
import structlog
from plyer import notification
from sqlalchemy import select

from .config import get_settings
from .db import SessionLocal
from .models import AlertEvent, AlertRule

if TYPE_CHECKING:
    from .config import Settings

logger = structlog.get_logger(__name__)


class AlertEngine:
    """
    Engine for evaluating transactions against alert rules and dispatching notifications.

    Supports multiple notification channels:
    - Webhooks (POST to configured URL)
    - Email (SMTP)
    - Desktop notifications (via plyer)
    """

    def __init__(self) -> None:
        """Initialize the alert engine with application settings."""
        self.settings: Settings = get_settings()

    async def evaluate(self, tx_data: dict[str, Any]) -> None:
        """
        Evaluate a transaction against all active alert rules.

        Args:
            tx_data: Normalized transaction data dictionary containing:
                - hash: Transaction hash
                - amount_xrp: Transaction amount in XRP
                - direction: 'inbound' or 'outbound'
                - counterparty: Other party's address
                - memo: Transaction memo (if present)
        """
        with SessionLocal() as session:
            rules = session.scalars(
                select(AlertRule).where(AlertRule.active.is_(True))
            ).all()

        triggered: list[AlertRule] = []
        for rule in rules:
            if self._matches_rule(rule, tx_data):
                triggered.append(rule)

        # Skip if no rules triggered and amount below threshold
        if not triggered and tx_data["amount_xrp"] < self.settings.alert_min_xrp:
            return

        message = (
            f"XRP Tx {tx_data['direction']} {tx_data['amount_xrp']:.2f} XRP "
            f"with {tx_data.get('counterparty', 'unknown')}"
        )
        await self.dispatch_alert(
            message=message,
            tx_hash=tx_data["hash"],
            rule_ids=[rule.id for rule in triggered],
        )

    def _matches_rule(self, rule: AlertRule, tx_data: dict[str, Any]) -> bool:
        """Check if a transaction matches an alert rule."""
        if rule.min_amount_xrp and tx_data["amount_xrp"] < rule.min_amount_xrp:
            return False
        if rule.direction and tx_data["direction"] != rule.direction:
            return False
        if rule.counterparty and tx_data.get("counterparty") != rule.counterparty:
            return False
        if rule.memo_keyword:
            memo = tx_data.get("memo")
            if not memo or rule.memo_keyword.lower() not in memo.lower():
                return False
        return True

    async def dispatch_alert(
        self, message: str, tx_hash: str, rule_ids: list[int]
    ) -> None:
        """
        Create alert event and dispatch to all configured channels.

        Args:
            message: Alert message text
            tx_hash: Associated transaction hash
            rule_ids: List of triggered rule IDs
        """
        # Persist alert event
        with SessionLocal() as session:
            alert = AlertEvent(
                rule_id=rule_ids[0] if rule_ids else None,
                transaction_hash=tx_hash,
                message=message,
            )
            session.add(alert)
            session.commit()
            alert_id = alert.id

        logger.info(
            "alert.triggered",
            alert_id=alert_id,
            message=message,
            tx_hash=tx_hash,
            rule_count=len(rule_ids),
        )

        # Dispatch to all configured channels
        if self.settings.webhook_url:
            self._send_webhook(alert_id, message, tx_hash)

        if self.settings.smtp_host and self.settings.smtp_to:
            self._send_email(alert_id, message)

        if self.settings.enable_desktop_notifications:
            self._notify_desktop(message)

    def _send_webhook(self, alert_id: int, message: str, tx_hash: str) -> None:
        """Send alert to configured webhook URL."""
        payload = {"id": alert_id, "message": message, "tx_hash": tx_hash}
        try:
            response = requests.post(
                self.settings.webhook_url,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.debug("alert.webhook_sent", alert_id=alert_id, status=response.status_code)
        except requests.exceptions.Timeout:
            logger.warning("alert.webhook_timeout", alert_id=alert_id)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("alert.webhook_connection_error", alert_id=alert_id, error=str(exc))
        except requests.exceptions.HTTPError as exc:
            logger.warning(
                "alert.webhook_http_error",
                alert_id=alert_id,
                status=exc.response.status_code if exc.response else None,
            )
        except requests.RequestException as exc:
            logger.warning("alert.webhook_failed", alert_id=alert_id, error=str(exc))

    def _send_email(self, alert_id: int, message: str) -> None:
        """Send alert via SMTP email."""
        msg = EmailMessage()
        msg["Subject"] = f"XRP Alert #{alert_id}"
        msg["From"] = self.settings.smtp_from
        msg["To"] = self.settings.smtp_to
        msg.set_content(message)

        try:
            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port, timeout=10
            ) as smtp:
                smtp.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(msg)
            logger.debug("alert.email_sent", alert_id=alert_id, to=self.settings.smtp_to)
        except smtplib.SMTPAuthenticationError:
            logger.warning("alert.email_auth_failed", alert_id=alert_id)
        except smtplib.SMTPRecipientsRefused:
            logger.warning("alert.email_recipient_refused", alert_id=alert_id)
        except smtplib.SMTPException as exc:
            logger.warning("alert.email_smtp_error", alert_id=alert_id, error=str(exc))
        except socket.timeout:
            logger.warning("alert.email_timeout", alert_id=alert_id)
        except OSError as exc:
            logger.warning("alert.email_connection_error", alert_id=alert_id, error=str(exc))

    def _notify_desktop(self, message: str) -> None:
        """Send desktop notification."""
        try:
            notification.notify(
                title="XRP Alert",
                message=message,
                app_name="XRP Tracker",
                timeout=5,
            )
            logger.debug("alert.desktop_sent")
        except NotImplementedError:
            logger.warning("alert.desktop_not_supported")
        except RuntimeError as exc:
            logger.warning("alert.desktop_failed", error=str(exc))
