# LabStock Deployment & Operations Guide

## 1. System Requirements
- **Python**: 3.12+ (tested on Python 3.12.10)
- **Memory**: Minimum 512 MB RAM (1 GB recommended)
- **Disk**: 100 MB for application + storage for database & backups
- **OS**: Windows 10/11, macOS, or Linux (Ubuntu 22.04 LTS / Debian 12 recommended for server)

## 2. Local Environment Setup

### 2.1 Virtual Environment & Installation
```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

### 2.2 Environment Configuration
Copy the provided `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Default parameters in `.env`:
- `SECRET_KEY`: Set to a strong random 256-bit hexadecimal string in production.
- `DATABASE_URL`: `sqlite:///./labstock.db` (or `postgresql://user:pass@localhost:5432/labstock`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default 480 (8 hours).

### 2.3 Database Migration & Seeding
```bash
# Run database migrations
alembic upgrade head

# Bootstrap root administrator
python scripts/bootstrap_admin.py --email admin@labstock.edu --name "Chief Lab Administrator" --password "AdminPass123!"

# (Optional) Seed realistic engineering lab demo dataset
python scripts/seed_demo_data.py
```

## 3. Running the Services

### 3.1 Running the Backend API
Start the FastAPI server on port 8000:
```bash
.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation is accessible at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

### 3.2 Running the Frontend Client
Launch the Flet UI client in a separate terminal:
```bash
.venv\Scripts\python -m frontend.labstock_ui.main
```
The Flet application connects to `http://127.0.0.1:8000/api/v1` by default.

## 4. Production Deployment

### 4.1 Production Backend (Systemd & Gunicorn/Uvicorn)
For server deployments on Linux:
```ini
[Unit]
Description=LabStock Backend FastAPI Service
After=network.target

[Service]
User=labstock
WorkingDirectory=/opt/labstock
ExecStart=/opt/labstock/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4.2 Web UI Delivery (Flet Web Mode)
Flet can also be exposed over web browser ports:
```bash
.venv\Scripts\flet run frontend/labstock_ui/main.py --web --port 8080
```
Then reverse-proxy through Nginx with HTTPS enabled.

### 4.3 Database Backup & WAL Maintenance
For SQLite deployments:
- SQLite WAL mode writes transactions to `labstock.db-wal`. Never delete this file while the application is running.
- Use SQLite's online backup API or `sqlite3 labstock.db ".backup backup.db"` for hot backups.
