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

## Deployment

### Proxmox Server (Recommended)
Deploy to your Proxmox server with automated setup:
```bash
chmod +x deploy-proxmox.sh
sudo ./deploy-proxmox.sh
```

This will:
- Install Docker and dependencies
- Create systemd service with auto-start
- Set up persistent data storage
- Configure the application

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed Proxmox deployment guide, including LXC container setup, management commands, backup/restore procedures, and troubleshooting.

### Local Development
1. Copy `.env.example` to `.env` and fill in:
   - `XRPL_WS_URL` (e.g., `wss://s1.ripple.com/`)
   - Wallet addresses (comma-delimited)
   - Alert preferences (thresholds, email, webhook, API key, etc.)
2. Build + run container:
   ```bash
   docker compose up --build
   ```
3. MCP endpoint available at `http://localhost:8000`. Configure Claude Desktop to use that URL plus the API key.

## Management

Use the control script for easy management:
```bash
sudo ./xrp-tracker-ctl.sh status    # Check service status
sudo ./xrp-tracker-ctl.sh logs      # View logs
sudo ./xrp-tracker-ctl.sh restart   # Restart service
sudo ./xrp-tracker-ctl.sh backup    # Create backup
sudo ./xrp-tracker-ctl.sh help      # Show all commands
```

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
