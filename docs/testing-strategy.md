# LabStock Testing Strategy & Quality Assurance

## 1. Overview
The testing architecture guarantees high confidence in stock ledger accuracy, transactional isolation, role enforcement, and user interface responsiveness.

Tests are organized into two primary suites executed by `pytest`:
1. **Backend Integration & Unit Tests** (`backend/app/tests/`)
2. **Frontend UI State & Component Tests** (`frontend/labstock_ui/tests/`)

## 2. Test Suites

### 2.1 Backend Tests (`backend/app/tests/`)
- `test_auth.py`:
  - Validates Argon2id password hashing and verification.
  - Tests successful login, invalid credentials, token verification, and deactivated user lockout.
- `test_inventory.py`:
  - Item creation with initial atomic stock receipt.
  - Duplicate SKU rejection (409 conflict).
  - Verifies that catalog metadata updates (name, category, location) never tamper with quantity on hand.
  - Soft deactivation and catalog filtering.
- `test_stock_engine.py`:
  - Atomic stock receipts, issues, and adjustments.
  - Insufficient stock prevention (refusal to allow negative quantity on hand).
  - Idempotency key replay and conflict detection.
  - Movement reversal mechanics and full ledger-to-balance reconciliation checks.
- `test_permissions.py`:
  - Strict RBAC matrix verification: Viewer cannot mutate items or users.
  - Manager cannot manage users or reverse movements.
  - Administrator lockout protection (last active administrator cannot be deactivated).
- `test_procurement.py`:
  - Full purchase request lifecycle: `draft` -> `submitted` -> `approved` -> `ordered` -> `received`.
  - Auto-generation of physical stock receipts upon purchase request receiving.
- `test_reports.py`:
  - CSV formula injection sanitization.
  - Verification of report summary and streaming CSV endpoints.

### 2.2 Frontend Tests (`frontend/labstock_ui/tests/`)
- `test_ui_flows.py`:
  - Global `SessionState` transitions, JWT persistence, and role-derived permission helpers (`is_admin`, `is_manager`).
  - `NavigationState` routing, listener notification, and parameter forwarding.
  - `StatusBadge` and `SkuChip` styling and Clinical Precision token conformance.
  - `MetricCard` rendering and radius configuration.
  - `EmptyState` and `LoadingState` UI instantiation.

## 3. Running the Test Suite
All tests use a dedicated temporary SQLite test database (`test_labstock.db`) which is isolated and purged after each test run:
```bash
# Run complete test suite with verbose output
.venv\Scripts\pytest -v

# Run with test coverage report
.venv\Scripts\pytest --cov=backend/app --cov=frontend/labstock_ui
```

## 4. Linting & Code Hygiene
Linting and formatting are enforced via `ruff`:
```bash
# Check code style and common bugs
.venv\Scripts\ruff check .

# Format code
.venv\Scripts\ruff format .
```
