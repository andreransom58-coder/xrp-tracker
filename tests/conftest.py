"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment variables before importing app modules
os.environ["XRPL_WS_URL"] = "wss://test.example.com/"
os.environ["XRPL_RPC_URL"] = "https://test.example.com/"
os.environ["XRPL_ACCOUNT_ADDRESSES"] = "rTestAddress1,rTestAddress2"
os.environ["API_KEY"] = "test-api-key-12345"
os.environ["DB_PATH"] = ":memory:"

from app.db import SessionLocal
from app.models import AlertEvent, AlertRule, Base, Transaction


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(test_engine, monkeypatch) -> Generator[TestClient, None, None]:
    """Create a test client with mocked database."""
    from app.mcp_server import app

    # Create fresh tables for each test
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_session():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    # Monkeypatch SessionLocal
    monkeypatch.setattr("app.db.SessionLocal", TestSession)
    monkeypatch.setattr("app.services.dashboard_service.SessionLocal", TestSession)
    monkeypatch.setattr("app.services.alert_service.SessionLocal", TestSession)
    monkeypatch.setattr("app.services.tx_service.SessionLocal", TestSession)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return authentication headers for API requests."""
    return {"X-API-Key": "test-api-key-12345"}


@pytest.fixture
def sample_transaction() -> dict[str, Any]:
    """Return sample transaction data."""
    return {
        "hash": "ABC123DEF456",
        "ledger_index": 12345,
        "account": "rSenderAddress",
        "destination": "rReceiverAddress",
        "amount_xrp": 100.50,
        "direction": "inbound",
        "memo": "Test transaction",
        "timestamp": datetime.now(timezone.utc),
        "raw": {"test": "data"},
    }


@pytest.fixture
def sample_alert_rule() -> dict[str, Any]:
    """Return sample alert rule data."""
    return {
        "name": "Test Alert Rule",
        "min_amount_xrp": 50.0,
        "direction": "inbound",
        "counterparty": None,
        "memo_keyword": None,
    }


@pytest.fixture
def populated_db(test_engine, sample_transaction) -> Generator[None, None, None]:
    """Populate the test database with sample data."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    session = TestSession()

    try:
        # Add sample transactions
        for i in range(5):
            tx = Transaction(
                hash=f"TX{i:03d}",
                ledger_index=1000 + i,
                account="rAccount1",
                destination="rAccount2",
                amount_xrp=10.0 * (i + 1),
                direction="inbound" if i % 2 == 0 else "outbound",
                timestamp=datetime.now(timezone.utc),
            )
            session.add(tx)

        # Add sample alert rule
        rule = AlertRule(
            name="Test Rule",
            min_amount_xrp=20.0,
            direction="inbound",
            active=True,
        )
        session.add(rule)

        # Add sample alert event
        alert = AlertEvent(
            rule_id=1,
            transaction_hash="TX001",
            message="Test alert message",
            status="open",
        )
        session.add(alert)

        session.commit()
        yield
    finally:
        session.close()
