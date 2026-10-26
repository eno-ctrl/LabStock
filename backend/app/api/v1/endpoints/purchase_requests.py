import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import (
    require_admin,
    require_authenticated_viewer,
    require_inventory_manager,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestFilter,
    PurchaseRequestLineOut,
    PurchaseRequestOut,
    PurchaseRequestStatus,
    ReceivePurchaseRequestPayload,
)
from backend.app.services.procurement_service import ProcurementService

router = APIRouter(prefix="/purchase-requests", tags=["Purchase Requests"])


def _to_pr_out(pr) -> PurchaseRequestOut:
    lines_out = [
        PurchaseRequestLineOut(
            id=line.id,
            request_id=line.request_id,
            item_id=line.item_id,
            item_sku=line.item.sku if line.item else "",
            item_name=line.item.name if line.item else "",
            requested_quantity=line.requested_quantity,
            ordered_quantity=line.ordered_quantity,
            received_quantity=line.received_quantity,
            unit_cost=line.unit_cost,
            notes=line.notes,
        )
        for line in pr.lines
    ]
    return PurchaseRequestOut(
        id=pr.id,
        request_number=pr.request_number,
        status=PurchaseRequestStatus(pr.status),
        supplier_id=pr.supplier_id,
        supplier=pr.supplier,
        requester_id=pr.requester_id,
        requester=pr.requester,
        approver_id=pr.approver_id,
        approver=pr.approver,
        notes=pr.notes,
        lines=lines_out,
        created_at=pr.created_at,
        updated_at=pr.updated_at,
    )


@router.get("", response_model=PaginatedResponse[PurchaseRequestOut])
def list_purchase_requests(
    status_filter: PurchaseRequestStatus | None = Query(None, alias="status"),
    supplier_id: int | None = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    procurement_service = ProcurementService(db)
    filters = PurchaseRequestFilter(
        status=status_filter,
        supplier_id=supplier_id,
        page=page,
        page_size=page_size,
    )
    requests, total = procurement_service.list_requests(filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[_to_pr_out(pr) for pr in requests],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("", response_model=PurchaseRequestOut, status_code=status.HTTP_201_CREATED)
def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    procurement_service = ProcurementService(db)
    pr = procurement_service.create_request(requester_id=manager.id, pr_in=payload)
    return _to_pr_out(pr)


@router.get("/{request_id}", response_model=PurchaseRequestOut)
def get_purchase_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    procurement_service = ProcurementService(db)
    pr = procurement_service.get_request(request_id)
    return _to_pr_out(pr)


@router.post("/{request_id}/submit", response_model=PurchaseRequestOut)
def submit_purchase_request(
    request_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    procurement_service = ProcurementService(db)
    pr = procurement_service.submit_request(request_id, actor_id=manager.id)
    return _to_pr_out(pr)


@router.post("/{request_id}/approve", response_model=PurchaseRequestOut)
def approve_purchase_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Administrator-only: approves a submitted purchase request."""
    procurement_service = ProcurementService(db)
    pr = procurement_service.approve_request(request_id, approver_id=admin.id)
    return _to_pr_out(pr)


@router.post("/{request_id}/order", response_model=PurchaseRequestOut)
def mark_purchase_request_ordered(
    request_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    procurement_service = ProcurementService(db)
    pr = procurement_service.order_request(request_id, actor_id=manager.id)
    return _to_pr_out(pr)


@router.post("/{request_id}/receive", response_model=PurchaseRequestOut)
def receive_stock_for_purchase_request(
    request_id: int,
    payload: ReceivePurchaseRequestPayload,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    """Atomically receives physical stock for ordered lines, updates balance, and ledger."""
    procurement_service = ProcurementService(db)
    pr = procurement_service.receive_stock_for_request(
        request_id=request_id, payload=payload, actor_id=manager.id
    )
    return _to_pr_out(pr)


@router.post("/{request_id}/cancel", response_model=PurchaseRequestOut)
def cancel_purchase_request(
    request_id: int,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    procurement_service = ProcurementService(db)
    pr = procurement_service.cancel_request(request_id, actor_id=manager.id, reason=reason)
    return _to_pr_out(pr)
