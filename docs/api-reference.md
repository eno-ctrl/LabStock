# LabStock REST API Reference (v1)

## Base URL
`/api/v1`

All responses follow standard HTTP status codes. Errors return a standardized JSON error envelope:
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Cannot issue 50.00 units of Raspberry Pi 4 Model B (SKU: SBC-RPI4-4GB). Available to issue: 12.00.",
    "status_code": 409
  }
}
```

---

## 1. Authentication (`/auth`)

### `POST /auth/login`
Authenticates a user via form-urlencoded credentials.
- **Request Body**: `username` (email), `password`
- **Response**: `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

### `GET /auth/me`
Retrieves profile and permissions of currently authenticated user.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: User object with id, email, full_name, role, is_active.

### `POST /auth/logout`
Terminates current session on the client and records audit sign-off.

---

## 2. Items & Catalog (`/items`)

### `GET /items`
Lists catalog items with optional filtering and pagination.
- **Query Parameters**:
  - `query` (str): Search term matching name, SKU, or description.
  - `category` (str): Filter by category.
  - `storage_location` (str): Filter by storage bin.
  - `status` (str): Filter by stock status (`IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`).
  - `active_only` (bool, default `true`): Exclude archived items.
  - `skip` (int), `limit` (int): Pagination controls.

### `POST /items`
Registers a new catalog item. (Requires `inventory_manager` or `administrator`).
- Initial stock can be received atomically during item registration.

### `GET /items/{item_id}`
Returns item specifications, linked vendor, and real-time stock balance.

### `PUT /items/{item_id}`
Updates catalog specifications (SKU, name, category, storage location, min threshold).
*Note*: This endpoint strictly prohibits altering quantity on hand.

### `DELETE /items/{item_id}`
Soft-deactivates an item from active catalog views.

---

## 3. Stock Movements (`/movements`)

### `GET /movements`
Queries chronological ledger entries with item, type, and date range filters.

### `POST /movements`
Executes an atomic stock movement. (Requires `inventory_manager` or `administrator`).
- **Body**:
  - `item_id`: int
  - `movement_type`: `RECEIPT` | `ISSUE` | `RETURN` | `DAMAGE` | `ADJUSTMENT`
  - `quantity`: float (> 0)
  - `reference_type`: optional string
  - `reference_id`: optional string
  - `notes`: optional string
  - `idempotency_key`: optional UUID/string
- **Behavior**: Atomically updates `stock_balances` and writes immutable `stock_movements` record.

### `POST /movements/{movement_id}/reverse`
Reverses a past movement by writing an equal and opposite `REVERSAL` transaction. (Requires `administrator`).

---

## 4. Replenishment & Procurement (`/replenishment`, `/purchase-requests`)

### `GET /replenishment`
Lists items below minimum safety stock, deficit quantities, and suggested order amounts.

### `GET /purchase-requests`
Lists purchase requests with status filtering.

### `POST /purchase-requests`
Creates a purchase request with item lines and vendor reference.

### `POST /purchase-requests/{id}/status`
Transitions PR status (`submit`, `approve`, `order`, `cancel`).

### `POST /purchase-requests/{id}/receive`
Records physical delivery of ordered goods, auto-generating atomic `RECEIPT` movements.

---

## 5. Dashboard & Analytics (`/dashboard`, `/reports`)

### `GET /dashboard/summary`
Calculates high-level metrics: total active SKUs, total valuation, low stock count, out of stock count.

### `GET /dashboard/recent-activity`
Returns the 10 most recent stock movements.

### `GET /reports/summary`
Computes inventory valuation by category and turnover metrics.

### `GET /reports/export/inventory-csv`
Streams RFC 4180 CSV export of catalog with formula injection protection (`=`, `+`, `-`, `@` escaped).

### `GET /reports/export/movements-csv`
Streams RFC 4180 CSV export of ledger transactions.

---

## 6. User Management (`/users`)
*Requires `administrator` role.*
- `GET /users`: List institutional accounts.
- `POST /users`: Create account with role.
- `PUT /users/{id}`: Update user metadata or role.
- `PUT /users/{id}/deactivate`: Soft-deactivate user account (safeguards last active administrator).
