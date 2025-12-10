# XRP Tracker

[![CI](https://github.com/yourusername/xrp-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/xrp-tracker/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Real-time XRP Ledger monitoring service with configurable alerts and a comprehensive dashboard. Built as an MCP (Model Context Protocol) server for seamless integration with Claude Desktop and other AI assistants.

## Features

- **Live XRPL Stream** - Real-time transaction monitoring via WebSocket subscription
- **Automatic Backfill** - Historical transaction retrieval for new wallets
- **Configurable Alerts** - Rule-based alerting with flexible filters:
  - Amount thresholds
  - Transaction direction (inbound/outbound)
  - Counterparty addresses
  - Memo keyword matching
- **Multi-Channel Notifications**
  - Webhook integrations
  - Email alerts (SMTP)
  - Desktop notifications
- **RESTful API** - FastAPI-powered MCP server with OpenAPI documentation
- **Persistent Storage** - SQLite database with Docker volume support
- **Production Ready** - Docker containerization with health checks

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   XRPL Network  │────▶│  Collector Svc   │────▶│    SQLite DB    │
│   (WebSocket)   │     │  (Transaction    │     │  (Transactions  │
└─────────────────┘     │   Stream)        │     │   & Alerts)     │
                        └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                                 ▼                        │
                        ┌──────────────────┐              │
                        │   Alert Engine   │              │
                        │  (Rule Matching  │              │
                        │   & Dispatch)    │              │
                        └────────┬─────────┘              │
                                 │                        │
           ┌─────────────────────┼────────────────────────┘
           │                     │
           ▼                     ▼
┌─────────────────┐     ┌──────────────────┐
│  Notifications  │     │   FastAPI MCP    │
│  (Webhook/Email │     │     Server       │◀──── Claude Desktop
│   /Desktop)     │     │   (REST API)     │      or HTTP Client
└─────────────────┘     └──────────────────┘
```

## Quick Start

### Using Docker (Recommended)

1. **Clone and configure:**
   ```bash
   git clone https://github.com/yourusername/xrp-tracker.git
   cd xrp-tracker
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```env
   XRPL_WS_URL=wss://s1.ripple.com/
   XRPL_ACCOUNT_ADDRESSES=rYourWalletAddress1,rYourWalletAddress2
   API_KEY=your-secure-api-key
   ```

3. **Start the service:**
   ```bash
   docker compose up --build -d
   ```

4. **Verify it's running:**
   ```bash
   curl http://localhost:8000/health
   ```

### Local Development

1. **Set up Python environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run services:**
   ```bash
   # Terminal 1: Start collector
   python -m app.collector

   # Terminal 2: Start API server
   uvicorn app.mcp_server:app --reload
   ```

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (no auth required) |
| `GET` | `/dashboard` | Dashboard metrics and recent data |
| `GET` | `/transactions` | Query transaction history |
| `GET` | `/alerts` | List alert events |
| `POST` | `/alerts` | Create alert rule |
| `POST` | `/alerts/{id}/ack` | Acknowledge alert |

### Authentication

All endpoints (except `/health`) require an API key header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/dashboard
```

### Example: Create Alert Rule

```bash
curl -X POST http://localhost:8000/alerts \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Large Inbound Alert",
    "min_amount_xrp": 1000,
    "direction": "inbound"
  }'
```

### OpenAPI Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `XRPL_WS_URL` | XRPL WebSocket URL | `wss://s1.ripple.com/` |
| `XRPL_RPC_URL` | XRPL JSON-RPC URL | `https://s2.ripple.com:51234/` |
| `XRPL_ACCOUNT_ADDRESSES` | Comma-separated wallet addresses | (required) |
| `API_KEY` | API authentication key | `change-me` |
| `DB_PATH` | SQLite database path | `data/xrp_monitor.db` |
| `ALERT_MIN_XRP` | Default alert threshold | `50.0` |
| `WEBHOOK_URL` | Alert webhook endpoint | (optional) |
| `SMTP_HOST` | SMTP server hostname | (optional) |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP authentication username | (optional) |
| `SMTP_PASSWORD` | SMTP authentication password | (optional) |
| `SMTP_FROM` | Email sender address | (optional) |
| `SMTP_TO` | Email recipient address | (optional) |
| `ENABLE_DESKTOP_NOTIFICATIONS` | Enable desktop alerts | `false` |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type check
mypy app

# Security scan
bandit -r app
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Project Structure

```
xrp-tracker/
├── app/
│   ├── __init__.py           # Package metadata
│   ├── alerts.py             # Alert engine & dispatch
│   ├── auth.py               # API authentication
│   ├── collector.py          # XRPL stream collector
│   ├── config.py             # Settings management
│   ├── db.py                 # Database setup
│   ├── mcp_server.py         # FastAPI application
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   ├── xrpl_client.py        # XRPL WebSocket client
│   └── services/
│       ├── alert_service.py      # Alert CRUD operations
│       ├── dashboard_service.py  # Dashboard aggregation
│       └── tx_service.py         # Transaction queries
├── tests/
│   ├── conftest.py           # Test fixtures
│   ├── test_alerts.py        # Alert engine tests
│   ├── test_api.py           # API endpoint tests
│   ├── test_config.py        # Configuration tests
│   └── test_schemas.py       # Schema validation tests
├── .github/workflows/
│   └── ci.yml                # CI pipeline
├── docker-compose.yml        # Container orchestration
├── Dockerfile                # Container build
├── pyproject.toml            # Project configuration
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── README.md
```

## Claude Desktop Integration

To use with Claude Desktop, add to your MCP configuration:

```json
{
  "mcpServers": {
    "xrp-tracker": {
      "url": "http://localhost:8000",
      "headers": {
        "X-API-Key": "your-api-key"
      }
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [XRPL.org](https://xrpl.org/) - XRP Ledger documentation
- [xrpl-py](https://github.com/XRPLF/xrpl-py) - Python XRPL library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
