# LabStock — Comprehensive Security Findings & Vulnerability Register

**Assessment Reference:** OWASP ASVS v4.0.3, OWASP Top 10 (2021), OWASP API Security Top 10 (2023), NIST SSDF v1.1  
**Target:** LabStock Laboratory Inventory & Spare Parts Management System  
**Audit Scope:** FastAPI Backend, SQLAlchemy ORM, SQLite/PostgreSQL Engine, Pydantic Schemas, Flet UI Client  
**Status:** All Confirmed Critical, High, and Medium Vulnerabilities Remediated & Verified  

---

## Vulnerability Summary Matrix

| ID | Title | Severity | CVSS v3.1 | CWE | ASVS Reference | Status |
|---|---|---|---|---|---|---|
| **SEC-VULN-01** | Session Token Stateless Invalidation Gap | **High** | 7.5 | CWE-613 | V3.3.1, V3.5.3 | **FIXED** |
| **SEC-VULN-02** | Unbounded Floating-Point Stock Corruption via `inf`/`nan` | **High** | 7.2 | CWE-1284 | V5.1.1, V5.1.5 | **FIXED** |
| **SEC-VULN-03** | CSV Formula Injection (DDE) Whitespace Bypass | **Medium** | 6.8 | CWE-1236 | V5.2.8 | **FIXED** |
| **SEC-VULN-04** | Reversal Idempotency Replay Ordering Conflict | **Medium** | 5.3 | CWE-675 | V13.1.1 | **FIXED** |
| **SEC-VULN-05** | N+1 Subquery Denial of Service in Consumption Reports | **Medium** | 5.3 | CWE-400 | V13.2.1 | **FIXED** |
| **SEC-VULN-06** | Missing HTTP Defense-in-Depth Security Headers | **Medium** | 5.0 | CWE-693 | V14.4.1, V14.4.2 | **FIXED** |
| **SEC-VULN-07** | Incomplete IP-Wide Login Throttling & Limiter Memory Leak | **Medium** | 4.8 | CWE-307 | V2.2.1 | **FIXED** |
| **SEC-VULN-08** | Segregation of Duties Bypass in Purchase Request Approval | **Medium** | 4.3 | CWE-284 | V4.1.3 | **FIXED** |
| **SEC-VULN-09** | Unbounded Text Fields Memory Exhaustion | **Low** | 3.7 | CWE-400 | V5.1.1 | **FIXED** |
| **SEC-VULN-10** | Exposure of Interactive OpenAPI/Docs in Production | **Low** | 3.1 | CWE-200 | V14.2.1 | **FIXED** |

---

## Detailed Vulnerability Reports

### SEC-VULN-01: Session Token Stateless Invalidation Gap
- **Severity:** High (CVSS: 7.5 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`)
- **CWE:** CWE-613 (Insufficient Session Expiration)
- **Affected Components:** `backend/app/core/security.py`, `backend/app/core/permissions.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/user.py`
- **Description:**  
  Previously, JWT access tokens were validated statelessly with no backend revocation store or version checking. When a user logged out (`/api/v1/auth/logout`) or an administrator changed a compromised user's password, existing tokens remained valid and usable until the 60-minute expiration period elapsed.
- **Impact:** An attacker who obtained a valid access token retained full API access even after the victim explicitly logged out or reset their password.
- **Root Cause:** Absence of token blacklist registry and missing user session version tracking in database schema.
- **Remediation:**  
  1. Added `jti` (JWT ID) and `ver` (session version) claims to all issued tokens.
  2. Created an in-memory TTL-tracked `_revoked_tokens` store with `revoke_token()` and automatic stale entry eviction.
  3. Added `token_version` column to the `User` model, incremented upon password changes.
  4. Updated `get_current_user` to reject revoked tokens and tokens with `ver < user.token_version`.
  5. Updated `/auth/logout` to explicitly revoke the active `jti` and token string.
- **Verification:** Verified by `test_auth_logout_token_revocation` and `test_password_change_invalidates_prior_tokens`.

---

### SEC-VULN-02: Unbounded Floating-Point Stock Corruption via `Infinity` and `NaN`
- **Severity:** High (CVSS: 7.2 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:H`)
- **CWE:** CWE-1284 (Improper Validation of Specified Quantity in Input)
- **Affected Components:** `backend/app/schemas/movement.py`, `backend/app/schemas/item.py`, `backend/app/schemas/purchase_request.py`
- **Description:**  
  Pydantic v2 `float = Field(..., gt=0.0)` accepts Python `float('inf')` and string inputs like `"Infinity"`, `"+Infinity"`, and `"NaN"`. Submitting an issue or receipt with `"quantity": "Infinity"` caused the database stock balance to become `inf`, corrupting ledger math, breaking balance queries, and causing unhandled exceptions in reporting.
- **Impact:** Irreversible corruption of database stock balances and loss of inventory audit integrity.
- **Root Cause:** Default Pydantic float parsing allows IEEE 754 non-finite numbers unless explicitly prohibited.
- **Remediation:**  
  Configured `allow_inf_nan=False` and enforced upper bound `le=10_000_000.0` across all quantity, threshold, and target stock fields in Pydantic schemas.
- **Verification:** Verified by `test_infinite_and_nan_stock_quantities_rejected` (asserts HTTP 422 for `"Infinity"`, `"-Infinity"`, and `"NaN"`).

---

### SEC-VULN-03: CSV Formula Injection (DDE) Whitespace Bypass
- **Severity:** Medium (CVSS: 6.8 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:U/C:H/I:L/A:N`)
- **CWE:** CWE-1236 (Improper Neutralization of Formula Elements in a CSV File)
- **Affected Components:** `backend/app/services/report_service.py`
- **Description:**  
  The CSV export sanitizer inspected only `text[0]`. An inventory manager or user could create an item with leading whitespace before a DDE payload (e.g., `   =cmd|'/C calc'!A0` or `\t=1+1`). Microsoft Excel and LibreOffice Calc strip leading whitespace when parsing CSV cells, allowing the formula to execute.
- **Impact:** Arbitrary code execution or data exfiltration on client workstations when lab administrators open exported inventory CSV files.
- **Root Cause:** Incomplete prefix inspection in `sanitize_csv_cell`.
- **Remediation:**  
  Updated `sanitize_csv_cell` to evaluate both raw control characters (`\t`, `\r`) and stripped strings (`text.lstrip(" \t\r\n")`) against trigger characters (`=`, `+`, `-`, `@`, `%`, `|`). If detected, the cell is safely escaped with a single quote prefix (`'`).
- **Verification:** Verified by `test_csv_formula_injection_sanitization` and `test_csv_formula_injection_whitespace_bypass`.

---

### SEC-VULN-04: Reversal Idempotency Replay Ordering Conflict
- **Severity:** Medium (CVSS: 5.3 — `CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:N/I:L/A:L`)
- **CWE:** CWE-675 (Multiple Operations on Resource in Single-Operation Context)
- **Affected Components:** `backend/app/services/stock_engine.py`
- **Description:**  
  In `StockEngine.reverse_movement`, the check for whether a movement had already been reversed was evaluated before checking the idempotency key store. If an administrator replayed an identical reversal request with the same `Idempotency-Key` (e.g. after a network drop), the server returned HTTP 409 `MOVEMENT_ALREADY_REVERSED` instead of the original cached success response.
- **Impact:** Spurious errors on network retries, causing administrative confusion and potential reconciliation discrepancies.
- **Root Cause:** Incorrect control flow sequence in reversal transaction handler.
- **Remediation:**  
  Moved `_check_idempotency` evaluation to the entry of `reverse_movement`, prior to checking `movement.is_reversed`.
- **Verification:** Verified by `test_reversal_idempotency_replay`.

---

### SEC-VULN-05: N+1 Subquery Denial of Service in Consumption Reports
- **Severity:** Medium (CVSS: 5.3 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:L`)
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **Affected Components:** `backend/app/services/report_service.py`
- **Description:**  
  `ReportService.get_consumption_report` queried all active items and iterated over them in Python, executing two individual aggregate subqueries (`func.sum` for issues and returns) per item. In a laboratory with 5,000 components, this resulted in 10,001 database queries per report generation request.
- **Impact:** High database CPU utilization, connection pool starvation, and API timeout.
- **Root Cause:** Lack of SQL grouping and bulk aggregation in report service.
- **Remediation:**  
  Refactored consumption report calculation into a single SQL query using `GROUP BY StockMovement.item_id`, SQLAlchemy `case` expressions for conditional summation, and an explicit result limit of 1,000 records.
- **Verification:** Verified by `test_reports_endpoints_json_and_csv`.

---

### SEC-VULN-06: Missing HTTP Defense-in-Depth Security Headers
- **Severity:** Medium (CVSS: 5.0 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N`)
- **CWE:** CWE-693 (Protection Mechanism Failure)
- **Affected Components:** `backend/app/main.py`
- **Description:**  
  FastAPI HTTP responses lacked critical security headers required for browser and hybrid web client protection.
- **Impact:** Susceptibility to MIME-type confusion attacks, clickjacking if embedded in iframes, and referrer data leakage across origins.
- **Remediation:**  
  Implemented global middleware in `main.py` setting:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- **Verification:** Verified by `test_security_headers_present`.

---

### SEC-VULN-07: Incomplete IP-Wide Login Throttling & Limiter Memory Leak
- **Severity:** Medium (CVSS: 4.8 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`)
- **CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)
- **Affected Components:** `backend/app/core/security.py`, `backend/app/api/v1/endpoints/auth.py`
- **Description:**  
  Rate limiting was applied solely per `(IP + username)`. An attacker executing a distributed username spray from a single IP could test passwords against thousands of accounts without triggering rate limits. Additionally, timestamp lists in the in-memory limiter were never pruned, creating unbounded memory growth.
- **Impact:** Credential stuffing attacks against laboratory staff accounts and potential server memory exhaustion.
- **Remediation:**  
  1. Added secondary IP-wide rate limit (`ip_login:{client_ip}`) capping total authentication attempts per IP.
  2. Implemented lazy cleanup in `check_rate_limit` removing expired timestamps.
- **Verification:** Verified by `test_auth.py` and `test_security_audit.py`.

---

### SEC-VULN-08: Segregation of Duties Bypass in Purchase Request Approval
- **Severity:** Medium (CVSS: 4.3 — `CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:N/I:L/A:N`)
- **CWE:** CWE-284 (Improper Access Control / Segregation of Duties)
- **Affected Components:** `backend/app/services/procurement_service.py`
- **Description:**  
  An administrator who submitted a purchase request for inventory parts could subsequently approve their own request without secondary oversight.
- **Impact:** Violation of dual-control accounting and laboratory governance; risk of fraudulent or unauthorized procurement.
- **Remediation:**  
  Enforced a validation check in `ProcurementService.approve_request`:
  `if pr.requester_id == approver_id: raise BadRequestException("Self-approval forbidden...")`.
- **Verification:** Verified by `test_purchase_request_self_approval_prevented`.

---

### SEC-VULN-09: Unbounded Text Fields Memory Exhaustion
- **Severity:** Low (CVSS: 3.7 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:L`)
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **Affected Components:** `backend/app/schemas/item.py`, `backend/app/schemas/movement.py`, `backend/app/schemas/purchase_request.py`
- **Description:**  
  Pydantic schemas permitted arbitrarily large strings in `description`, `notes`, and `reason` fields.
- **Impact:** Database bloat, client UI rendering stutter, and JSON parser memory spike.
- **Remediation:**  
  Added strict length boundaries (`max_length=5000` for item descriptions, `max_length=1000` to `2000` for movement notes and purchase requests).
- **Verification:** Verified by schema unit tests.

---

### SEC-VULN-10: Exposure of Interactive OpenAPI/Docs in Production
- **Severity:** Low (CVSS: 3.1 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`)
- **CWE:** CWE-200 (Exposure of Sensitive Information)
- **Affected Components:** `backend/app/main.py`
- **Description:**  
  The interactive API explorer endpoints (`/docs`, `/redoc`, `/openapi.json`) were exposed unconditionally.
- **Impact:** Reconnaissance information disclosure for potential attackers regarding internal schema and route structure.
- **Remediation:**  
  Configured FastAPI initialization to conditionally disable `docs_url`, `redoc_url`, and `openapi_url` when `settings.ENVIRONMENT.lower() == "production"`.
- **Verification:** Verified by configuration inspection and unit test.
