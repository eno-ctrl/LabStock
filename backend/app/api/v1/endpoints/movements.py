import math

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import (
    require_admin,
    require_authenticated_viewer,
    require_inventory_manager,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.movement_repo import MovementRepository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.movement import (
    AdjustmentCreate,
    DamageCreate,
    IssueCreate,
    MovementFilter,
    MovementOut,
    MovementType,
    ReceiptCreate,
    ReturnCreate,
    ReversalCreate,
)
from backend.app.services.stock_engine import StockEngine

router = APIRouter(prefix="/movements", tags=["Stock Movements"])


def _to_movement_out(m) -> MovementOut:
    return MovementOut(
        id=m.id,
        item_id=m.item_id,
        item_sku=m.item.sku if m.item else "",
        item_name=m.item.name if m.item else "",
        movement_type=MovementType(m.movement_type),
        quantity=m.quantity,
        signed_quantity=m.signed_quantity,
        balance_after=m.balance_after,
        reference_type=m.reference_type,
        reference_id=m.reference_id,
        reason=m.reason,
        recipient_project=m.recipient_project,
        actor_id=m.actor_id,
        actor_name=m.actor.full_name if m.actor else None,
        timestamp=m.timestamp,
        idempotency_key=m.idempotency_key,
        reversal_of_movement_id=m.reversal_of_movement_id,
    )


@router.get("", response_model=PaginatedResponse[MovementOut])
def list_movements(
    item_id: int | None = Query(None),
    movement_type: MovementType | None = Query(None),
    query: str | None = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """List immutable stock movements ledger with search and filters."""
    movement_repo = MovementRepository(db)
    filters = MovementFilter(
        item_id=item_id,
        movement_type=movement_type,
        query=query,
        page=page,
        page_size=page_size,
    )
    movements, total = movement_repo.list_movements(filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[_to_movement_out(m) for m in movements],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("/receipts", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def receive_stock(
    payload: ReceiptCreate,
    request: Request,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Receive stock into inventory atomically."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.receive_stock(
        payload=payload,
        actor_id=manager.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)


@router.post("/issues", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def issue_stock(
    payload: IssueCreate,
    request: Request,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Issue stock to a person, student, course, or project with available balance check."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.issue_stock(
        payload=payload,
        actor_id=manager.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)


@router.post("/returns", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def return_stock(
    payload: ReturnCreate,
    request: Request,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Return working components back into usable inventory balance."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.return_stock(
        payload=payload,
        actor_id=manager.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)


@router.post("/damages", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_damage(
    payload: DamageCreate,
    request: Request,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Write off damaged, broken, or expired items with mandatory justification."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.record_damage(
        payload=payload,
        actor_id=manager.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)


@router.post("/adjustments", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def adjust_stock(
    payload: AdjustmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Authorized inventory adjustment/reconciliation with mandatory reason."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.adjust_stock(
        payload=payload,
        actor_id=manager.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)


@router.post(
    "/{movement_id}/reverse", response_model=MovementOut, status_code=status.HTTP_201_CREATED
)
def reverse_movement(
    movement_id: int,
    payload: ReversalCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Administrator-only: reverse an eligible historical movement atomically."""
    correlation_id = getattr(request.state, "correlation_id", None)
    stock_engine = StockEngine(db)
    movement = stock_engine.reverse_movement(
        movement_id=movement_id,
        payload=payload,
        actor_id=admin.id,
        request_id=correlation_id,
    )
    return _to_movement_out(movement)
