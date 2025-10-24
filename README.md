# Arbitrage

A small FastAPI-based arbitrage monitoring service that polls multiple exchange APIs, stores results in PostgreSQL, exposes Prometheus metrics, and can notify via Telegram.

This repository contains everything needed to run the full stack (backend, Postgres, Prometheus, Grafana) via Docker Compose or to run the backend locally for development.

## Key features

-   FastAPI backend exposing a small API and a Prometheus `/metrics` endpoint.
-   Background market polling loop that checks exchange prices and notifies via Telegram when configured.
-   Uses PostgreSQL to persist results.
-   Prometheus + Grafana included (via Docker Compose) with sample dashboards in `grafana/`.

## Quick facts

-   Backend: FastAPI (entrypoint `app.main:app`)
-   Metrics endpoint: `GET /metrics` (Prometheus format)
-   Default polling interval: 20 seconds (controlled with `POLL_INTERVAL_SECONDS` env var)

## Prerequisites

-   Docker & Docker Compose (recommended for running full stack)
-   Or Python 3.10+ and a PostgreSQL instance for local development

## Environment variables

The service reads configuration from environment variables. Most important:

-   `WALLEX_API_KEY` - API key for the Wallex exchange (if used)
-   `TELEGRAM_TOKEN` - Telegram bot token used by the notifier
-   `DATABASE_URL` - SQLAlchemy database URL (Docker Compose sets this for you)
-   `POLL_INTERVAL_SECONDS` - optional, seconds between market polls (default: 20)

When using the provided `docker-compose.yml`, `DATABASE_URL` is set for the `backend` service automatically.

## Run the full stack (recommended)

From the repository root, start the services with Docker Compose. In PowerShell:

```powershell
# Start services in the foreground (Ctrl+C to stop)
docker-compose up --build

# Or start in detached mode
docker-compose up --build -d
```

Services and useful ports (default):

-   Backend: http://localhost:8000
    -   Root: `/` (simple health / welcome)
    -   Metrics: `/metrics` (Prometheus)
-   Prometheus UI: http://localhost:9090
-   Grafana UI: http://localhost:3000 (default admin/admin)
-   Postgres: 5432 (container exposes for convenience)
-   Postgres exporter: 9187

Grafana provisioning and dashboards live under `grafana/`.

## Run backend locally (without Docker)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Provide required environment variables (PowerShell example):

```powershell
$env:TELEGRAM_TOKEN = "<your-telegram-token>"
$env:WALLEX_API_KEY = "<your-wallex-key>"
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/arbitrage"
```

4. Run the app with Uvicorn (module: `app.main:app`):

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Note: If you run the backend locally you still need a PostgreSQL server reachable at `DATABASE_URL`. Using Docker Compose (above) is the easiest way to get all dependencies running.

## Observability (Prometheus & Grafana)

-   The backend exposes metrics at `/metrics` using `prometheus_client`.
-   `prometheus.yml` config is included and Docker Compose mounts it into the Prometheus container.
-   Grafana provisioning files and dashboards are included under `grafana/` (dashboards and datasource YAMLs).

## Project structure

```
./
├─ app/                      # backend application package
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app, startup/shutdown, polling loop, /metrics
│  ├─ database.py             # DB initialization and helpers
│  ├─ exchanges.py            # exchange adapters & market checking logic
│  ├─ notifier.py             # Telegram notifier implementation
│  ├─ metrics.py              # metrics helpers
│  └─ ...
├─ grafana/                  # Grafana dashboards and provisioning
├─ prometheus.yml            # Prometheus scrape configuration
├─ docker-compose.yml        # Full stack orchestration (backend, db, prometheus, grafana)
├─ Dockerfile                # Builds the backend container
└─ requirements.txt          # Python dependencies
```

## Configuration & extension points

-   Polling interval: change `POLL_INTERVAL_SECONDS` environment variable.
-   Add more exchange adapters in `app/exchanges.py` or similar modules.
-   Notification channels: `app/notifier.py` implements a Telegram notifier; you can extend it.

## Notes & development tips

-   The background polling task only attempts to notify when there are registered Telegram chat IDs. The `TelegramNotifier` class handles connecting and running the bot.
-   The `/metrics` endpoint is provided for Prometheus scraping.
-   The repository intentionally does not include secrets; set tokens and keys via environment variables or a secure secrets manager.

## Troubleshooting

-   If Prometheus/Grafana fail to start, check container logs with `docker-compose logs prometheus` or `docker-compose logs grafana`.
-   If the backend can't connect to Postgres, verify `DATABASE_URL` and that the `db` service is healthy.

## License

No license is specified. Add a LICENSE file if you intend to make the project open source.

---

If you want, I can also:

-   Add a small `README` section explaining how to configure a Telegram bot and obtain `TELEGRAM_TOKEN`.
-   Provide a PowerShell script to quickly spin up the stack and set environment variables.

(Per your request, no code files were changed.)
