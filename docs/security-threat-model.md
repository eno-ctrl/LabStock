# LabStock Security & Threat Model

## 1. Threat Modeling Overview (STRIDE)
LabStock is architected following defense-in-depth principles to protect university and research lab assets against unauthorized tampering, theft, inventory misreporting, and software vulnerabilities.

| Threat Category | Potential Attack Vector | LabStock Mitigation Control |
|---|---|---|
| **Spoofing** | Attacker impersonates faculty or lab manager | Strict Argon2id password hashing with time-memory cost parameters; signed JWT tokens with short expiry; user account active status checks on every request. |
| **Tampering** | Direct manual mutation of stock balance without audit trail | `StockBalance` can only be modified via the internal `StockTransactionEngine`; item metadata update endpoints are strictly barred from updating stock quantities; database check constraints enforce non-negative stock. |
| **Repudiation** | Operator denies issuing high-value hardware | Immutable `stock_movements` table logs operator ID, timestamp, transaction type, reference document, and resulting balance after mutation; comprehensive `audit_logs` record all administrative actions. |
| **Information Disclosure** | Leakage of sensitive tokens or internal exceptions in logs | Structured logging middleware strips Authorization headers, passwords, and sensitive keys; centralized exception handlers convert raw tracebacks to safe, sanitized JSON error responses. |
| **Denial of Service** | Rapid repeated requests exhausting server resources | Sliding-window IP/user rate limiter on authentication endpoints; SQLite configured in Write-Ahead-Logging (WAL) mode with busy timeouts to avoid lock contention. |
| **Elevation of Privilege** | Student viewer attempts to create users or issue stock | Server-side RBAC enforcement via FastAPI dependency injection (`require_manager_or_admin`, `require_admin`); frontend UI controls dynamically disabled based on current role. |

## 2. Specific Security Controls

### 2.1 Password Hashing (Argon2id)
Passwords are never stored in plaintext or with legacy hashing algorithms (such as MD5 or single-iteration SHA). We employ `argon2-cffi` configured with:
- `time_cost = 2`
- `memory_cost = 65536` (64 MB)
- `parallelism = 8`
- `hash_len = 32`

### 2.2 CSV Formula Injection Prevention (Spreadsheet Attack)
When exporting inventory data or movement history to CSV, cell contents beginning with dangerous formula characters (`=`, `+`, `-`, `@`, `\t`, `\r`) can execute malicious commands in spreadsheet applications (e.g. Microsoft Excel or LibreOffice Calc). LabStock sanitizes all exported string cells:
```python
def sanitize_csv_cell(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value
```

### 2.3 Idempotency & Replay Attack Defense
Network jitter in workshops can cause automated tools or barcode scanners to send multiple identical requests. The `POST /api/v1/movements` endpoint accepts an `idempotency_key`:
1. If the key was already processed successfully with the exact same payload, the original transaction is returned without modifying stock.
2. If the key was used previously with different parameters, an `IDEMPOTENCY_CONFLICT` (409) is raised.

### 2.4 Administrative Safety Guardrails
The system strictly prevents the deactivation of the last remaining active Administrator account. If an admin attempts to deactivate their own account or another admin when only one active administrator remains, the operation is blocked with a 409 status code.
