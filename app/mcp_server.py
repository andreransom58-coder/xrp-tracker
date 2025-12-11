from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import verify_api_key
from .db import init_db
from .schemas import AlertRuleCreate, DashboardResponse
from .services.alert_service import AlertService
from .services.dashboard_service import DashboardService
from .services.tx_service import TransactionService

app = FastAPI(title="XRP Monitor MCP API")

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

dashboard_service = DashboardService()
tx_service = TransactionService()
alert_service = AlertService()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    """Serve the professional UI dashboard"""
    return FileResponse(str(static_path / "index.html"))


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard(user=Depends(verify_api_key)):
    return dashboard_service.build()


@app.get("/transactions")
def list_transactions(limit: int = 50, direction: str | None = None, user=Depends(verify_api_key)):
    return {"items": tx_service.list(limit=limit, direction=direction)}


@app.get("/alerts")
def list_alerts(status: str | None = None, user=Depends(verify_api_key)):
    return {"items": alert_service.list(status=status)}


@app.post("/alerts")
def create_alert(rule: AlertRuleCreate, user=Depends(verify_api_key)):
    return alert_service.create(rule)


@app.post("/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, user=Depends(verify_api_key)):
    result = alert_service.acknowledge(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result
