# LabStock Security Assessment Plan

## 1. Scope & Rules of Engagement
- **Target In-Scope**:
  - Source code repository: `backend/app/`, `frontend/labstock_ui/`, `scripts/`, `docs/`.
  - Local development runtime and dedicated SQLite test database (`test_isolated.db`).
  - Python 3.12 virtual environment (`.venv`).
- **Explicit Exclusions**:
  - Production institutional databases or real student records.
  - Third-party external APIs, cloud services, and production networks.
  - Unbounded Denial-of-Service or destructive payloads against shared systems.

## 2. Test Environment & Safety Controls
- **Test Database Isolation**:
  - All tests execute against an isolated SQLite test database with `assert "test" in TEST_DATABASE_URL or ":memory:" in TEST_DATABASE_URL`.
  - Real operational database (`labstock.db`) is never written to during automated security testing.
- **Data Protection**:
  - All credentials used in tests are synthetic demo accounts (`admin@labstock.edu`, `manager@labstock.edu`, `viewer@labstock.edu`).
  - No live secrets or customer PII exist in the workspace.

## 3. Tooling & Verification Matrix
| Tool / Framework | Version | Purpose |
|---|---|---|
| **pytest** | 9.1.1 | Automated security regression test execution |
| **HTTPX / FastAPI TestClient** | 0.28.1 | Direct HTTP API adversarial testing across roles |
| **pip-audit** | 2.10.1 | Known CVE scanning of direct & transitive dependencies |
| **bandit** | 1.9.4 | Static application security testing (SAST) for Python |
| **ruff** | 0.8.2 | Code hygiene, dead code, and format validation |

## 4. Phase-by-Phase Verification Scope
1. **Phase 1: Attack-Surface Discovery**: Route mapping, input schemas, and permission requirements.
2. **Phase 2: Authentication & Session**: Argon2id verification, brute-force rate limits, token invalidation on logout and password reset.
3. **Phase 3: Authorization & Roles**: Complete endpoint matrix (Anonymous, Viewer, Manager, Admin, Deactivated).
4. **Phase 4: API Security**: Pagination limits, input types, HTTP security headers, CORS origin controls.
5. **Phase 5: Inventory Integrity**: Concurrency, non-negative balances, idempotency replays, movement reversals, PR receiving limits.
6. **Phase 6: Injection & Validation**: SQL injection resistance, CSV formula injection sanitization, Unicode handling.
7. **Phase 7: Supply Chain & Dependencies**: pip-audit and bandit verification.
8. **Phase 8: Configuration & Hardening**: Production vs development configs, environment variables, documentation protection.
9. **Phase 9: Audit Logs**: Event attribution, credential redaction, immutable log integrity.
10. **Phase 10: Client-Side Security**: Flet state handling, credential storage, error reporting.
11. **Phase 11: Abuse Resilience**: Overflow/Infinity numbers, boundary values, N+1 query performance.
12. **Phase 12: Automated Regression Suite**: Execution of `test_security_audit.py` with 100% pass criteria.
13. **Phase 13: Remediation & Retesting**: Verification that all confirmed Critical and High issues are fixed and retested.
