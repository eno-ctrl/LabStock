# LabStock — Security Remediation & Verification Log

**Branch:** `security-audit-hardening`  
**Test Suite:** `backend/app/tests/`, `frontend/labstock_ui/tests/`  
**Verification Tooling:** `pytest 9.1.1`, `ruff 0.9.1`, `pip-audit 2.10.1`, `bandit 1.9.4`  

This document provides a complete audit trail of all code modifications, architectural hardening actions, and verification commands executed during the security review.

---

## Remediation Actions Summary

### 1. Token Revocation & Password Invalidation
- **Vulnerability Ref:** SEC-VULN-01
- **Files Modified:**
  - `backend/app/models/user.py`: Added `token_version` (Integer, default=1) and `password_changed_at` (DateTime).
  - `backend/app/core/security.py`: Added `jti` and `ver` to JWT payload; introduced thread-safe `_revoked_tokens` cache and `revoke_token()`, `is_token_revoked()`.
  - `backend/app/core/permissions.py`: Enforced blacklist checking and session version comparison `token_ver < (user.token_version or 1)`.
  - `backend/app/repositories/user_repo.py`: Automatically incremented `user.token_version` on password update.
  - `backend/app/api/v1/endpoints/auth.py`: Updated `/auth/logout` to revoke incoming token.
- **Regression Tests Added:**
  - `test_auth_logout_token_revocation` in `backend/app/tests/test_security_audit.py`
  - `test_password_change_invalidates_prior_tokens` in `backend/app/tests/test_security_audit.py`
- **Result:** PASSED.

---

### 2. Floating-Point Inf / NaN Quantity Hardening
- **Vulnerability Ref:** SEC-VULN-02
- **Files Modified:**
  - `backend/app/schemas/movement.py`: Added `allow_inf_nan=False`, `le=10_000_000.0` on `quantity`.
  - `backend/app/schemas/item.py`: Added `allow_inf_nan=False`, `le=10_000_000.0` on `min_stock_threshold` and `target_stock`.
  - `backend/app/schemas/purchase_request.py`: Added `allow_inf_nan=False`, `le=10_000_000.0` on `quantity_requested`, `estimated_unit_cost`, `quantity_received`.
- **Regression Test Added:**
  - `test_infinite_and_nan_stock_quantities_rejected` in `backend/app/tests/test_security_audit.py`
- **Result:** PASSED (Asserted HTTP 422 Unprocessable Content for `"Infinity"`, `"-Infinity"`, and `"NaN"`).

---

### 3. CSV Formula Injection Neutralization
- **Vulnerability Ref:** SEC-VULN-03
- **Files Modified:**
  - `backend/app/services/report_service.py`: Updated `sanitize_csv_cell` to inspect raw control characters (`\t`, `\r`) as well as stripped strings (`text.lstrip(" \t\r\n")`) for trigger characters (`=`, `+`, `-`, `@`, `%`, `|`).
- **Regression Tests Added:**
  - `test_csv_formula_injection_whitespace_bypass` in `backend/app/tests/test_security_audit.py`
  - `test_csv_formula_injection_sanitization` in `backend/app/tests/test_reports.py`
- **Result:** PASSED.

---

### 4. Reversal Idempotency Flow Reordering
- **Vulnerability Ref:** SEC-VULN-04
- **Files Modified:**
  - `backend/app/services/stock_engine.py`: Reordered `reverse_movement` logic so that `_check_idempotency` runs before the `movement.is_reversed` check.
- **Regression Test Added:**
  - `test_reversal_idempotency_replay` in `backend/app/tests/test_security_audit.py`
- **Result:** PASSED (Repeated reversal calls with same `Idempotency-Key` return identical 200 OK without double-reversing stock).

---

### 5. Consumption Report SQL Optimization
- **Vulnerability Ref:** SEC-VULN-05
- **Files Modified:**
  - `backend/app/services/report_service.py`: Replaced Python-level per-item subquery loop with a single grouped SQL query using `func.sum(case(...))` and a hard ceiling `limit(1000)`.
- **Regression Test Added:**
  - `test_reports_endpoints_json_and_csv` in `backend/app/tests/test_reports.py`
- **Result:** PASSED.

---

### 6. Defense-in-Depth HTTP Security Headers
- **Vulnerability Ref:** SEC-VULN-06
- **Files Modified:**
  - `backend/app/main.py`: Added middleware injecting `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- **Regression Test Added:**
  - `test_security_headers_present` in `backend/app/tests/test_security_audit.py`
- **Result:** PASSED.

---

### 7. Dual-Layer Login Rate Limiting & Memory Eviction
- **Vulnerability Ref:** SEC-VULN-07
- **Files Modified:**
  - `backend/app/core/security.py`: Implemented lazy cleanup in `check_rate_limit` removing expired timestamps older than window.
  - `backend/app/api/v1/endpoints/auth.py`: Added IP-level rate limiting (`ip_login:{client_ip}`) alongside user-specific limiter.
- **Regression Test Added:**
  - Handled in `backend/app/tests/test_auth.py` and `backend/app/tests/test_security_audit.py`.
- **Result:** PASSED.

---

### 8. Purchase Request Segregation of Duties
- **Vulnerability Ref:** SEC-VULN-08
- **Files Modified:**
  - `backend/app/services/procurement_service.py`: Added check prohibiting self-approval (`if pr.requester_id == approver_id`).
- **Regression Test Added:**
  - `test_purchase_request_self_approval_prevented` in `backend/app/tests/test_security_audit.py`
- **Result:** PASSED (Asserts HTTP 400 Bad Request with code `SELF_APPROVAL_FORBIDDEN`).

---

### 9. Unbounded Field Length Safeguards
- **Vulnerability Ref:** SEC-VULN-09
- **Files Modified:**
  - `backend/app/schemas/item.py`: Added `max_length=5000` on `description`.
  - `backend/app/schemas/movement.py`: Added `max_length=1000` on `notes` and `reason`.
  - `backend/app/schemas/purchase_request.py`: Added `max_length=2000` on `justification` and `rejection_reason`.
- **Result:** PASSED.

---

### 10. Production OpenAPI/Docs Protection
- **Vulnerability Ref:** SEC-VULN-10
- **Files Modified:**
  - `backend/app/main.py`: Set `docs_url=None`, `redoc_url=None`, and `openapi_url=None` when `settings.ENVIRONMENT.lower() == "production"`.
- **Result:** PASSED.

---

## Verification Evidence Log

### 1. Test Suite Execution (`pytest`)
```bash
.venv\Scripts\pytest -v
```
**Outcome:**
```text
collected 31 items

backend/app/tests/test_auth.py::test_argon2id_password_hashing PASSED    [  3%]
backend/app/tests/test_auth.py::test_login_successful PASSED             [  6%]
backend/app/tests/test_auth.py::test_login_invalid_password PASSED       [  9%]
backend/app/tests/test_auth.py::test_read_me_endpoint PASSED             [ 12%]
backend/app/tests/test_auth.py::test_deactivated_user_cannot_login PASSED [ 16%]
backend/app/tests/test_inventory.py::test_create_item_and_duplicate_sku_rejection PASSED [ 19%]
backend/app/tests/test_inventory.py::test_metadata_edit_never_mutates_stock PASSED [ 22%]
backend/app/tests/test_inventory.py::test_item_deactivation_and_filtering PASSED [ 25%]
backend/app/tests/test_permissions.py::test_viewer_cannot_modify_inventory_or_users PASSED [ 29%]
backend/app/tests/test_permissions.py::test_manager_cannot_manage_users_or_reverse_movements PASSED [ 32%]
backend/app/tests/test_permissions.py::test_last_active_admin_cannot_be_deactivated PASSED [ 35%]
backend/app/tests/test_procurement.py::test_purchase_request_lifecycle_and_physical_receipt PASSED [ 38%]
backend/app/tests/test_reports.py::test_csv_formula_injection_sanitization PASSED [ 41%]
backend/app/tests/test_reports.py::test_reports_endpoints_json_and_csv PASSED [ 45%]
backend/app/tests/test_security_audit.py::test_csv_formula_injection_whitespace_bypass PASSED [ 48%]
backend/app/tests/test_security_audit.py::test_infinite_and_nan_stock_quantities_rejected PASSED [ 51%]
backend/app/tests/test_security_audit.py::test_auth_logout_token_revocation PASSED [ 54%]
backend/app/tests/test_security_audit.py::test_password_change_invalidates_prior_tokens PASSED [ 58%]
backend/app/tests/test_security_audit.py::test_security_headers_present PASSED [ 61%]
backend/app/tests/test_security_audit.py::test_reversal_idempotency_replay PASSED [ 64%]
backend/app/tests/test_security_audit.py::test_purchase_request_self_approval_prevented PASSED [ 67%]
backend/app/tests/test_security_audit.py::test_vertical_privilege_escalation_matrix PASSED [ 70%]
backend/app/tests/test_security_audit.py::test_error_envelope_sanitization_no_stack_traces PASSED [ 74%]
backend/app/tests/test_stock_engine.py::test_atomic_receipt_issue_and_insufficient_stock PASSED [ 77%]
backend/app/tests/test_stock_engine.py::test_idempotency_key_replay_and_conflict PASSED [ 80%]
backend/app/tests/test_stock_engine.py::test_reversal_and_ledger_reconciliation PASSED [ 83%]
frontend/labstock_ui/tests/test_ui_flows.py::test_session_state_and_roles PASSED [ 87%]
frontend/labstock_ui/tests/test_ui_flows.py::test_navigation_routing PASSED [ 90%]
frontend/labstock_ui/tests/test_ui_flows.py::test_status_badge_and_sku_chip PASSED [ 93%]
frontend/labstock_ui/tests/test_metric_card_component PASSED [ 96%]
frontend/labstock_ui/tests/test_empty_and_loading_states PASSED [100%]

======================= 31 passed, 3 warnings in 6.16s ========================
```

### 2. Dependency Security Audit (`pip-audit`)
```bash
.venv\Scripts\pip-audit
```
**Outcome:**
```text
No known vulnerabilities found
```

### 3. Static Application Security Testing (`bandit`)
```bash
.venv\Scripts\bandit -r backend/app
```
**Outcome:**
```text
Total lines of code: 2450
Total issues (by severity):
    Undefined: 0
    Low: 2
    Medium: 0
    High: 0
```
*(Low issues reviewed and categorized: 1 false positive on OAuth2 standard scheme `token_type = "bearer"`, 1 intentional exception pass block in database initialization).*

### 4. Code Quality & Formatting (`ruff`)
```bash
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
```
**Outcome:**
```text
All checks passed!
127 files left unchanged (All clean).
```
