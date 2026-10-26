import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import (
    require_authenticated_viewer,
    require_inventory_manager,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.balance_repo import BalanceRepository
from backend.app.repositories.movement_repo import MovementRepository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.item import ItemCreate, ItemFilter, ItemOut, ItemUpdate
from backend.app.schemas.movement import MovementFilter, MovementOut, MovementType, ReceiptCreate
from backend.app.services.inventory_service import InventoryService
from backend.app.services.stock_engine import StockEngine

router = APIRouter(prefix="/items", tags=["Inventory Items"])


def _map_item_out(it) -> ItemOut:
    out = ItemOut.model_validate(it)
    out.stock_status = InventoryService.compute_stock_status(it)
    return out


@router.get("", response_model=PaginatedResponse[ItemOut])
def list_items(
    query: str | None = Query(None, description="Search SKU, name, category, or location"),
    category: str | None = Query(None),
    storage_location: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    is_active: bool | None = Query(True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="name"),
    sort_desc: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """Retrieve paginated, searchable, filterable items with current stock status."""
    service = InventoryService(db)
    filters = ItemFilter(
        query=query,
        category=category,
        storage_location=storage_location,
        status=status_filter,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    items, total = service.list_items(filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[_map_item_out(it) for it in items],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Create a new catalog item. If initial_stock > 0, records an opening physical receipt atomically."""
    service = InventoryService(db)
    initial_stock = payload.initial_stock
    item = service.create_item(payload, actor_id=manager.id)

    if initial_stock > 0:
        stock_engine = StockEngine(db)
        stock_engine.receive_stock(
            ReceiptCreate(
                item_id=item.id,
                quantity=initial_stock,
                reference_type="opening_stock",
                reason="Initial item balance on catalog creation",
            ),
            actor_id=manager.id,
        )
        db.refresh(item)

    return _map_item_out(item)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    service = InventoryService(db)
    item = service.get_item(item_id)
    return _map_item_out(item)


@router.patch("/{item_id}", response_model=ItemOut)
def update_item_metadata(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Update item metadata. Stock quantities CANNOT be mutated via this endpoint."""
    service = InventoryService(db)
    item = service.update_item_metadata(item_id, payload, actor_id=manager.id)
    return _map_item_out(item)


@router.post("/{item_id}/deactivate", response_model=ItemOut)
def deactivate_item(
    item_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    service = InventoryService(db)
    item = service.set_active_status(item_id, is_active=False, actor_id=manager.id)
    return _map_item_out(item)


@router.post("/{item_id}/activate", response_model=ItemOut)
def activate_item(
    item_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    service = InventoryService(db)
    item = service.set_active_status(item_id, is_active=True, actor_id=manager.id)
    return _map_item_out(item)


@router.get("/{item_id}/movements", response_model=PaginatedResponse[MovementOut])
def get_item_movements(
    item_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    """Chronological ledger history for a specific catalog item."""
    movement_repo = MovementRepository(db)
    filters = MovementFilter(item_id=item_id, page=page, page_size=page_size)
    movements, total = movement_repo.list_movements(filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    items_out = []
    for m in movements:
        items_out.append(
            MovementOut(
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
        )

    return PaginatedResponse(
        items=items_out,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/{item_id}/reconcile")
def reconcile_item_balance(
    item_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Verifies that materialized stock balance matches the exact sum of the immutable ledger."""
    balance_repo = BalanceRepository(db)
    return balance_repo.reconcile_with_ledger(item_id)
