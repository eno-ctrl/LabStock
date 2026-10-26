from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.permissions import require_authenticated_viewer
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/replenishment", tags=["Replenishment"])


@router.get("/low-stock", response_model=list[dict[str, Any]])
def get_low_stock_items(
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """List items currently below their configured minimum threshold."""
    service = ReportService(db)
    return service.get_low_stock_report()


@router.get("/out-of-stock", response_model=list[dict[str, Any]])
def get_out_of_stock_items(
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """List completely depleted catalog items."""
    service = ReportService(db)
    return service.get_out_of_stock_report()
