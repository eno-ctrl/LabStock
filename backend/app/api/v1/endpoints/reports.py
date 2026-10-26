from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.app.core.permissions import require_authenticated_viewer
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/stock")
def get_current_stock_report(
    category: str | None = Query(None),
    location: str | None = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_current_stock_report(category=category, location=location)

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_current_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "current_stock", "total": len(data), "data": data}


@router.get("/low-stock")
def get_low_stock_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_low_stock_report()

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_low_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "low_stock", "total": len(data), "data": data}


@router.get("/out-of-stock")
def get_out_of_stock_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_out_of_stock_report()

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_out_of_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "out_of_stock", "total": len(data), "data": data}


@router.get("/movements")
def get_movements_report(
    item_id: int | None = Query(None),
    movement_type: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_movements_report(
        item_id=item_id,
        movement_type=movement_type,
        start_date=start_date,
        end_date=end_date,
    )

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_movements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "movements", "total": len(data), "data": data}


@router.get("/consumption")
def get_consumption_report(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_consumption_report(start_date=start_date, end_date=end_date)

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_consumption_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "consumption", "total": len(data), "data": data}


@router.get("/damaged-stock")
def get_damaged_stock_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = ReportService(db)
    data = service.get_damaged_stock_report()

    if format == "csv":
        csv_buffer = service.generate_csv_stream(data)
        filename = f"labstock_damaged_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return {"report": "damaged_stock", "total": len(data), "data": data}
