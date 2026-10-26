# LabStock Permissions & Authorization Matrix

| HTTP Method | Route Endpoint | Required Role | Anonymous | Viewer | Inventory Manager | Administrator | Deactivated User |
|---|---|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | None (Public) | 200 / 401 | 200 / 401 | 200 / 401 | 200 / 401 | 401 Unauthorized |
| `GET` | `/api/v1/auth/me` | Authenticated | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/auth/logout` | Authenticated | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/items` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/items` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `GET` | `/api/v1/items/{id}` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `PATCH` | `/api/v1/items/{id}` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/items/{id}/deactivate` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/items/{id}/activate` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/items/{id}/movements` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/items/{id}/reconcile` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/movements` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/movements/receipts` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/movements/issues` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/movements/returns` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/movements/damages` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/movements/adjustments` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/movements/{id}/reverse` | Administrator | 401 Unauthorized | 403 Forbidden | 403 Forbidden | 201 Created | 401 Unauthorized |
| `GET` | `/api/v1/replenishment` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/purchase-requests` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests/{id}/submit` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests/{id}/approve` | Administrator | 401 Unauthorized | 403 Forbidden | 403 Forbidden | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests/{id}/order` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests/{id}/receive` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/purchase-requests/{id}/cancel` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/suppliers` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/suppliers` | Manager+ | 401 Unauthorized | 403 Forbidden | 201 Created | 201 Created | 401 Unauthorized |
| `PATCH` | `/api/v1/suppliers/{id}` | Manager+ | 401 Unauthorized | 403 Forbidden | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/dashboard/summary` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/dashboard/recent-activity` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/reports/*` | Viewer+ | 401 Unauthorized | 200 OK | 200 OK | 200 OK | 401 Unauthorized |
| `GET` | `/api/v1/users` | Administrator | 401 Unauthorized | 403 Forbidden | 403 Forbidden | 200 OK | 401 Unauthorized |
| `POST` | `/api/v1/users` | Administrator | 401 Unauthorized | 403 Forbidden | 403 Forbidden | 201 Created | 401 Unauthorized |
| `PATCH` | `/api/v1/users/{id}` | Administrator | 401 Unauthorized | 403 Forbidden | 403 Forbidden | 200 OK | 401 Unauthorized |
| `GET` | `/health` | None (Public) | 200 OK | 200 OK | 200 OK | 200 OK | 200 OK |
