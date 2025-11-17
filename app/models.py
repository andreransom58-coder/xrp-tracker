from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CursorState(Base):
    __tablename__ = "cursor_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_ledger_index = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    hash = Column(String(128), primary_key=True)
    ledger_index = Column(Integer, nullable=False)
    account = Column(String(64), index=True, nullable=False)
    destination = Column(String(64), index=True, nullable=True)
    amount_xrp = Column(Float, nullable=False)
    direction = Column(String(8), nullable=False)
    memo = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    raw = Column(JSON, nullable=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    min_amount_xrp = Column(Float, nullable=True)
    direction = Column(String(8), nullable=True)  # inbound/outbound
    counterparty = Column(String(64), nullable=True)
    memo_keyword = Column(String(128), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=True)
    transaction_hash = Column(String(128), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(32), default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
