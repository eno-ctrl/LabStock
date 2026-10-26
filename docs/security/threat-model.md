# LabStock Security Threat Model (STRIDE & ASVS)

## 1. System Overview & Scope
- **Application**: LabStock Laboratory Inventory & Spare Parts Management System.
- **Environment**: University engineering labs, robotics clubs, prototyping workshops.
- **Stack**:
  - Frontend: Python Flet (Desktop/Web UI client)
  - Backend: Python FastAPI 0.115+ (REST API v1)
  - Database: SQLite (WAL mode, foreign keys ON) for local / PostgreSQL for shared
  - Authentication: Argon2id password hashing, Bearer JWT (HS256)
  - Validation: Pydantic v2
  - ORM: SQLAlchemy 2.x, migrations via Alembic

---

## 2. Threat Actors
| Actor ID | Profile | Capability / Motivation | Risk Level |
|---|---|---|---|
| **ACT-01** | Unauthenticated Network Attacker | Probes public API endpoints, attempts brute-force, injection, or DoS. | Medium |
| **ACT-02** | Compromised / Stolen Token Bearer | Uses expired, revoked, or leaked JWT from shared lab terminal or network sniffing. | High |
| **ACT-03** | Malicious / Curious Student (Viewer) | Attempts vertical privilege escalation to issue hardware or modify user accounts. | Medium |
| **ACT-04** | Careless / Rogue Inventory Manager | Over-issues parts, attempts self-approval of purchase requests, or manipulates quantities. | High |
| **ACT-05** | Malicious Administrator | Attempts to delete audit logs or deactivate all other administrators. | High |
| **ACT-06** | Accidental Operator / Workshop User | Double-clicks submit, scans barcodes twice, or enters invalid quantities. | Medium |

---

## 3. Trust Boundaries
```
+-------------------------------------------------------------+
| TB-1: Client Device / User Workstation (Flet Desktop / Web)  |
| - Local memory, user input fields, OS clipboard             |
+-------------------------------------------------------------+
                               |
                        [Network Boundary: HTTPS / TLS 1.3]
                               |
+-------------------------------------------------------------+
| TB-2: API Gateway & Application Server (FastAPI)            |
| - Authentication middleware, rate limiters, security headers |
| - Authorization dependencies, Pydantic schema validation    |
| - Redacted JSON logging                                     |
+-------------------------------------------------------------+
                               |
                       [Internal Service Boundary]
                               |
+-------------------------------------------------------------+
| TB-3: Business Services & Transaction Engine                |
| - Double-entry ledger, non-negative stock enforcement       |
| - Idempotency deduplication, audit logging                  |
+-------------------------------------------------------------+
                               |
                       [Data Persistence Boundary]
                               |
+-------------------------------------------------------------+
| TB-4: Relational Database (SQLite WAL / PostgreSQL)         |
| - Check constraints, foreign keys, row versioning           |
+-------------------------------------------------------------+
```

---

## 4. STRIDE Threat Analysis Matrix

| Threat Category | Target Asset | Threat Scenario | Preconditions | Existing Control | Residual Risk / Gap |
|---|---|---|---|---|---|
| **Spoofing** | User Identity, JWT Token | Attacker replays token after user logged out on shared terminal. | Stolen token or shared machine. | Short-lived token (8h). | **HIGH**: Tokens not blacklisted on logout; password change doesn't revoke existing tokens. |
| **Spoofing** | Credentials | Password spraying / credential stuffing. | Public login endpoint. | Argon2id, IP+user rate limiting. | **MEDIUM**: Rate limiting per (IP+username); pure IP spraying not throttled. |
| **Tampering** | Stock Balance | Attacker updates stock directly via item metadata edit. | Authenticated manager. | `update_item_metadata` rejects balance fields. | **LOW**: Direct balance edit blocked; stock only changes via `StockEngine`. |
| **Tampering** | Stock Balance | Submitting `quantity: "Infinity"` or `NaN` in movement payload. | Authenticated manager. | `Field(..., gt=0.0)` in Pydantic. | **HIGH**: `float` without `allow_inf_nan=False` or `le` accepts `inf`. |
| **Tampering** | Purchase Request | Requester approves their own purchase request. | Manager / Admin user. | Role requires Admin. | **MEDIUM**: No check ensuring `requester_id != approver_id`. |
| **Repudiation** | Stock Movements | Operator denies issuing high-value hardware. | Authenticated user. | Immutable `stock_movements` table with actor_id, timestamp. | **LOW**: Audit trail is immutable and linked to movements. |
| **Information Disclosure** | Credentials & Tokens | Leaking passwords or tokens in application logs. | Server error or debug log. | Structured logging redaction filter. | **LOW**: Passwords and Authorization headers redacted. |
| **Information Disclosure** | API Schema | Exposing `/docs` and `/redoc` in production. | Production deployment. | FastAPI docs enabled by default. | **MEDIUM**: Docs should be disabled in production environment. |
| **Denial of Service** | Report Engine | Massive consumption report triggers thousands of SQL queries (N+1). | Viewer access. | None on consumption endpoint. | **MEDIUM**: N+1 queries on `get_consumption_report` can exhaust DB pool. |
| **Elevation of Privilege** | Administrative Ops | Viewer invokes Manager/Admin endpoints. | Authenticated Viewer. | FastAPI `require_roles` dependencies. | **LOW**: Enforced server-side on every route. |
| **Elevation of Privilege** | Admin Lockout | Admin deactivates last active admin. | Authenticated Admin. | `count_active_admins() <= 1` guard. | **LOW**: Guarded in `UserRepository.update`. |
