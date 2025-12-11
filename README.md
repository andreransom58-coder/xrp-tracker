# XRP Monitoring MCP Service

Monitor personal XRP Ledger activity, enforce alerting rules, and surface a dashboard to Claude Desktop (via MCP) or any HTTP client.

## Features
- **Professional Web Dashboard** - Modern, responsive UI with real-time data visualization
- Live XRPL stream subscriber with automatic backfill
- Normalized transaction storage in SQLite (volume-friendly)
- Rule-based alert engine (amount thresholds, direction, memo keywords, counterparties)
- Alert delivery via desktop notifications, email (SMTP), or generic webhooks
- FastAPI MCP server exposing dashboard + control tools
- Docker + Compose deployment
- Dark/Light theme support
- Interactive charts and analytics

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
  static/
    index.html
    css/
      styles.css
    js/
      app.js
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
3. Access the application:
   - **Web Dashboard**: Open `http://localhost:8000` in your browser
   - **MCP Endpoint**: Available at `http://localhost:8000` for Claude Desktop integration

## Web Dashboard
The professional web interface provides:
- **Real-time Metrics**: Total balance, 24h inflow/outflow, and active alerts
- **Interactive Charts**: Visualize your XRP transaction flow over time
- **Transaction History**: View recent transactions with full details
- **Alert Management**: Create, view, and acknowledge alerts through the UI
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Theme Toggle**: Switch between light and dark modes

Simply navigate to `http://localhost:8000` after starting the service and enter your API key when prompted.

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
