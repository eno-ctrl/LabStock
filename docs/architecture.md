# LabStock System Architecture

## 1. Overview
**LabStock** is an enterprise-grade Laboratory Inventory and Spare Parts Management System engineered for engineering colleges, robotics research labs, workshop spaces, and institutional prototyping facilities. It provides full transactional integrity, immutable movement audit trails, role-based access controls, and automated procurement replenishment triggers.

```
+-------------------------------------------------------------+
|                      Client Layer                           |
|       Flet Desktop / Web Client (Clinical Precision UI)     |
|   - 12 Screen Modular Router (Dashboard, Inventory, etc.)   |
|   - Token-Aware HTTP Client (Bearer JWT, Auto Re-auth)     |
+-------------------------------------------------------------+
                               |
                               | REST JSON / SSE / CSV
                               v
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|   - Correlation ID & Redacted Security Logging Middleware   |
|   - RBAC Enforcement Dependencies (OAuth2 / Argon2id)       |
|   - Formula-Safe CSV Streaming & Analytics Engine           |
+-------------------------------------------------------------+
                               |
                               | Services & Transactions
                               v
+-------------------------------------------------------------+
|                 Stock Transaction Engine                    |
|   - Double-Entry Balance Mutator with Check Constraints    |
|   - Idempotency Hash Validator & Replay Protector          |
|   - Non-Negative Stock & Reversal Re-validation             |
+-------------------------------------------------------------+
                               |
                               | SQLAlchemy 2.0 ORM / Core
                               v
+-------------------------------------------------------------+
|                     Persistence Layer                       |
|   - SQLite (WAL Mode, foreign_keys=ON, busy_timeout=5000)   |
|   - Production-ready for PostgreSQL / Enterprise RDBMS      |
|   - Alembic Managed Schema Versioning                       |
+-------------------------------------------------------------+
```

## 2. Component Architecture

### 2.1 Backend Architecture
The backend is structured around clean domain-driven layering:
- **`backend/app/core/`**: Centralized configuration (`config.py`), Argon2id password hashing and JWT encoding (`security.py`), role-based authorization dependencies (`permissions.py`), RFC-compliant JSON logging with token redacting (`logging.py`), and domain-specific exception types (`exceptions.py`).
- **`backend/app/db/`**: Base Declarative Meta and SQLite WAL engine configuration (`base.py`, `session.py`).
- **`backend/app/models/`**: SQLAlchemy 2.x mapped classes (`User`, `Item`, `StockBalance`, `StockMovement`, `Supplier`, `PurchaseRequest`, `PurchaseRequestLine`, `AuditLog`).
- **`backend/app/repositories/`**: Decoupled database data access repositories implementing transactional persistence and query filtering.
- **`backend/app/services/`**: Business logic orchestration.
  - `StockTransactionEngine`: Atomic inventory operations (`RECEIPT`, `ISSUE`, `RETURN`, `DAMAGE`, `ADJUSTMENT`, `REVERSAL`), ensuring zero negative stock and idempotent replay safety.
  - `InventoryService`: SKU uniqueness, catalog metadata updates (strictly preventing balance tampering through item updates).
  - `ProcurementService`: Multi-state purchase request lifecycle (`draft` -> `submitted` -> `approved` -> `ordered` -> `partially_received` / `received`).
  - `ReportService`: Audit summaries and RFC 4180 CSV export with formula injection sanitization.
- **`backend/app/api/v1/`**: Typed REST API endpoints validating request contracts via Pydantic v2.

### 2.2 Frontend Architecture
The frontend is built using **Flet** following the **Clinical Precision** Design System tokens:
- **`frontend/labstock_ui/config.py`**: Design system tokens (Deep Navy `#15263B`, Slate Navy `#213B54`, Emerald Mint `#36B78A`, Deep Mint `#21805F`, Mint Tint `#EBFBF5`, Off-White Surface `#F5F7FA`, Border `#E2E8F0`).
- **`frontend/labstock_ui/state/`**: Reactive global singletons for `session` (active JWT, user profile, role checks) and `navigation` (route switching and parameters).
- **`frontend/labstock_ui/api/`**: Typed API clients (`auth_client`, `inventory_client`, `movement_client`, `supplier_client`, `procurement_client`, `report_client`, `dashboard_client`, `user_client`) with centralized HTTP error handling.
- **`frontend/labstock_ui/components/`**: Reusable clinical precision controls (`AppShell`, `Sidebar`, `Topbar`, `MetricCard`, `StatusBadge`, `SkuChip`, `EmptyState`, `LoadingState`, `ConfirmationDialog`).
- **`frontend/labstock_ui/pages/`**: 12 modular screen views covering all functional lab requirements.

## 3. Stock Transaction Engine Guarantees
1. **Atomic Mutation**: Every stock movement executes within a single database transaction. The physical ledger entry (`StockMovement`) and the balance snapshot (`StockBalance`) are updated simultaneously.
2. **Negative Stock Prevention**: Both software validation and database-level `CHECK (quantity_on_hand >= 0)` prevent stock from ever dropping below zero.
3. **Idempotency Protection**: When an `idempotency_key` is supplied, replayed requests return the original transaction result without re-executing stock deductions or ledger insertions.
4. **Reversal Ledger Auditability**: Reversals do not delete rows; instead, they generate a complementary compensating `REVERSAL` transaction referencing the original `reference_movement_id`.
5. **Periodic Reconciliation**: System diagnostics calculate `sum(signed_quantity)` across the entire historical ledger for an item and compare it with `StockBalance.quantity_on_hand` to detect any drift.
