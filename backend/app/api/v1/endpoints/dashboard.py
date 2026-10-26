from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.permissions import require_authenticated_viewer
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.dashboard import DashboardRecentActivity, DashboardSummary
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """Retrieve real backend-derived inventory metrics, active item counts, and attention items."""
    service = DashboardService(db)
    return service.get_summary()


@router.get("/recent-activity", response_model=DashboardRecentActivity)
def get_dashboard_recent_activity(
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """Retrieve recent stock transactions ledger entries."""
    service = DashboardService(db)
    movements = service.get_recent_movements(limit=15)
    return DashboardRecentActivity(recent_movements=movements)
