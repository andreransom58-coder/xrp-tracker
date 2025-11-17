# XRP Monitoring MCP Service

Monitor personal XRP Ledger activity, enforce alerting rules, and surface a dashboard to Claude Desktop (via MCP) or any HTTP client.

## Features
- Live XRPL stream subscriber with automatic backfill
- Normalized transaction storage in SQLite (volume-friendly)
- Rule-based alert engine (amount thresholds, direction, memo keywords, counterparties)
- Alert delivery via desktop notifications, email (SMTP), or generic webhooks
- FastAPI MCP server exposing dashboard + control tools
- Docker + Compose deployment

## Project Layout
```
app/
  alerts.py
  auth.py
  collector.py
  config.py
  db.py
  models.py
  mcp_server.py
  schemas.py
  xrpl_client.py
  services/
    alert_service.py
    dashboard_service.py
    tx_service.py
start.sh
Dockerfile
docker-compose.yml
.env.example
requirements.txt
```

## Getting Started
1. Copy `.env.example` to `.env` and fill in:
   - `XRPL_WS_URL` (e.g., `wss://s1.ripple.com/`)
   - Wallet addresses (comma-delimited)
   - Alert preferences (thresholds, email, webhook, API key, etc.)
2. Build + run container:
   ```bash
   docker compose up --build
   ```
3. MCP endpoint available at `http://localhost:8000`. Configure Claude Desktop to use that URL plus the API key.

## MCP Tools
- `GET /dashboard` – summary metrics + recent transactions and alert digest
- `GET /transactions` – queryable ledger history
- `GET /alerts` – active alerts
- `POST /alerts` – create rule
- `POST /alerts/{id}/ack` – acknowledge alert
- `POST /alerts/test` – send test alert

## Development
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.collector &
uvicorn app.mcp_server:app --reload
```

## Testing
```bash
pytest
```
(*placeholder tests in `tests/` — expand as you add business logic*)
