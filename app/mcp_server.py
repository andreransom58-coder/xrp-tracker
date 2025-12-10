"""FastAPI MCP server for XRP monitoring dashboard and alerts."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import __version__
from .auth import verify_api_key
from .db import SessionLocal, init_db
from .schemas import (
    AlertListResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    DashboardResponse,
    ErrorResponse,
    HealthResponse,
    TransactionListResponse,
)
from .services.alert_service import AlertService
from .services.dashboard_service import DashboardService
from .services.tx_service import TransactionService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    logger.info("app.startup", version=__version__)
    init_db()
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title="XRP Tracker MCP API",
    description="Monitor XRP Ledger activity with real-time alerts and dashboard",
    version=__version__,
    lifespan=lifespan,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
dashboard_service = DashboardService()
tx_service = TransactionService()
alert_service = AlertService()


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint",
)
async def health_check() -> HealthResponse:
    """
    Check the health status of the service.

    Returns service status, version, and database connectivity.
    This endpoint does not require authentication.
    """
    db_status = "healthy"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=__version__,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )


@app.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["Dashboard"],
    summary="Get dashboard metrics and data",
)
def dashboard(user: Any = Depends(verify_api_key)) -> DashboardResponse:
    """
    Retrieve dashboard summary with metrics, recent transactions, and alerts.

    Returns:
        - Summary metrics (balance, 24h inflow/outflow, alert count)
        - Recent transactions (last 25)
        - Open alerts
        - Chart data for visualization
    """
    return dashboard_service.build()


@app.get(
    "/transactions",
    response_model=TransactionListResponse,
    tags=["Transactions"],
    summary="List transactions",
)
def list_transactions(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum transactions to return"),
    direction: str | None = Query(
        default=None,
        pattern="^(inbound|outbound)$",
        description="Filter by direction",
    ),
    user: Any = Depends(verify_api_key),
) -> TransactionListResponse:
    """
    Query transaction history with optional filtering.

    Returns a paginated list of transactions ordered by timestamp (newest first).
    """
    return TransactionListResponse(items=tx_service.list(limit=limit, direction=direction))


@app.get(
    "/alerts",
    response_model=AlertListResponse,
    tags=["Alerts"],
    summary="List alert events",
)
def list_alerts(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(open|acknowledged)$",
        description="Filter by alert status",
    ),
    user: Any = Depends(verify_api_key),
) -> AlertListResponse:
    """
    Query alert events with optional status filtering.

    Returns alerts ordered by creation time (newest first).
    """
    return AlertListResponse(items=alert_service.list(status=status_filter))


@app.post(
    "/alerts",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Alerts"],
    summary="Create alert rule",
)
def create_alert(
    rule: AlertRuleCreate,
    user: Any = Depends(verify_api_key),
) -> AlertRuleResponse:
    """
    Create a new alert rule for transaction monitoring.

    Alert rules can filter on:
    - Minimum XRP amount
    - Transaction direction (inbound/outbound)
    - Specific counterparty address
    - Memo keywords
    """
    result = alert_service.create(rule)
    logger.info("alert_rule.created", rule_id=result["id"], name=result["name"])
    return AlertRuleResponse(**result)


@app.post(
    "/alerts/{alert_id}/ack",
    response_model=dict[str, Any],
    tags=["Alerts"],
    summary="Acknowledge alert",
)
def ack_alert(
    alert_id: int,
    user: Any = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Acknowledge an open alert event.

    Marks the alert as acknowledged and records the acknowledgment timestamp.
    """
    result = alert_service.acknowledge(alert_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found",
        )
    logger.info("alert.acknowledged", alert_id=alert_id)
    return result
