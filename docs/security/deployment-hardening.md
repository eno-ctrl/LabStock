# LabStock — Production Deployment & Infrastructure Hardening Guide

**Document Purpose:** Operational security baseline, host hardening, reverse-proxy setup, and database reliability controls for LabStock.  
**Audience:** System Administrators, DevOps Engineers, and Security Reviewers.  

---

## 1. Environment & Secret Management

### 1.1 Secret Key Generation
Never use default or predictable keys in production. Generate a cryptographically secure 256-bit secret key using Python's `secrets` module:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.2 Configuration Isolation
- Keep `.env` strictly local and out of version control (enforced in `.gitignore`).
- Ensure file system permissions restrict access exclusively to the application service user:
  ```bash
  chmod 600 .env
  chown labstock:labstock .env
  ```
- Production environment variable checklist:
  ```env
  ENVIRONMENT=production
  SECRET_KEY=<GENERATED_64_CHAR_KEY>
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  DATABASE_URL=postgresql://labstock_app:<STRONG_DB_PASS>@127.0.0.1:5432/labstock_prod
  BACKEND_CORS_ORIGINS=["https://labstock.institution.edu"]
  ```

---

## 2. Database Hardening

### 2.1 SQLite Operational Hardening (Development & Single-Node Labs)
When using SQLite in standalone or laboratory workbench environments:
1. **Enable Write-Ahead Logging (WAL):**
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA busy_timeout = 5000;
   PRAGMA foreign_keys = ON;
   ```
2. **File Permissions:**
   Restrict database file permissions to prevent read access by other local users:
   ```bash
   chmod 600 labstock.db
   chmod 600 labstock.db-wal
   chmod 600 labstock.db-shm
   ```
3. **Safe Online Backups:**
   Never copy an active SQLite database file directly with `cp`. Use the SQLite online backup API:
   ```bash
   sqlite3 labstock.db ".backup 'backups/labstock_$(date +%Y%m%d_%H%M%S).bak'"
   ```

### 2.2 PostgreSQL Operational Hardening (Multi-User Institutional Deployments)
For shared departmental installations:
1. **Dedicated Non-Superuser Role:**
   ```sql
   CREATE USER labstock_app WITH PASSWORD 'StrongRandomPassword!';
   GRANT CONNECT ON DATABASE labstock_prod TO labstock_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO labstock_app;
   ```
2. **Enforce SSL/TLS Connections:**
   In `DATABASE_URL`, append `?sslmode=verify-full&sslrootcert=/etc/ssl/certs/lab-ca.crt`.
3. **Row-Level Concurrency:**
   PostgreSQL uses MVCC. For stock ledger operations, `SELECT ... FOR UPDATE` or explicit transactions at `READ COMMITTED` / `REPEATABLE READ` are enforced.

---

## 3. Reverse Proxy & TLS Configuration

LabStock should never be exposed directly to an untrusted network on port 8000. Terminate TLS with a reverse proxy such as Nginx or Caddy.

### 3.1 Nginx Reference Hardening Config
```nginx
# Rate limiting zone: 10 requests per second per IP
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

server {
    listen 80;
    server_name labstock.institution.edu;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name labstock.institution.edu;

    ssl_certificate /etc/letsencrypt/live/labstock.institution.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/labstock.institution.edu/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Defense-in-depth security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;" always;

    # Client body limit
    client_max_body_size 5M;

    # Auth rate limit
    location /api/v1/auth/login {
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Flet Web / Static UI
    location / {
        proxy_pass http://127.0.0.1:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 4. Systemd Service Isolation

Run the backend under an unprivileged dedicated service account:

```ini
# /etc/systemd/system/labstock-backend.service
[Unit]
Description=LabStock FastAPI Backend Engine
After=network.target postgresql.service

[Service]
Type=simple
User=labstock
Group=labstock
WorkingDirectory=/opt/labstock
EnvironmentFile=/opt/labstock/.env
ExecStart=/opt/labstock/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4 --proxy-headers
Restart=always
RestartSec=5

# Sandboxing
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/labstock/backups /opt/labstock/logs
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

---

## 5. Backup & Recovery Protocol

1. **Daily Scheduled Backup Script (`/opt/labstock/scripts/backup.sh`):**
   ```bash
   #!/bin/bash
   set -euo pipefail
   BACKUP_DIR="/opt/labstock/backups"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="${BACKUP_DIR}/labstock_${TIMESTAMP}.bak"

   sqlite3 /opt/labstock/labstock.db ".backup '${BACKUP_FILE}'"
   sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
   find "${BACKUP_DIR}" -name "*.bak" -mtime +30 -delete
   ```
2. **Restoration Drill:**
   Verify backup integrity once per semester by restoring to an isolated database container and validating ledger balance checksums via:
   ```bash
   python scripts/reconcile_stock.py --db-path /tmp/restore_test.db
   ```
