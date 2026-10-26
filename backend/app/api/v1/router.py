from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    dashboard,
    items,
    movements,
    purchase_requests,
    replenishment,
    reports,
    suppliers,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(items.router)
api_router.include_router(movements.router)
api_router.include_router(suppliers.router)
api_router.include_router(purchase_requests.router)
api_router.include_router(replenishment.router)
api_router.include_router(reports.router)
api_router.include_router(users.router)
