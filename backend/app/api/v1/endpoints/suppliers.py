import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.core.permissions import (
    require_authenticated_viewer,
    require_inventory_manager,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.supplier_repo import SupplierRepository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierOut])
def list_suppliers(
    query: str | None = Query(None, description="Search supplier name, contact, or email"),
    is_active: bool | None = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    supplier_repo = SupplierRepository(db)
    skip = (page - 1) * page_size
    suppliers, total = supplier_repo.list_suppliers(
        query=query, is_active=is_active, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[SupplierOut.model_validate(s) for s in suppliers],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    supplier_repo = SupplierRepository(db)
    supplier = supplier_repo.create(payload)

    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="CREATE_SUPPLIER",
        entity_type="supplier",
        entity_id=str(supplier.id),
        actor_id=manager.id,
        details={"name": supplier.name},
    )
    db.commit()
    return SupplierOut.model_validate(supplier)


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated_viewer),
):
    supplier_repo = SupplierRepository(db)
    supplier = supplier_repo.get_by_id(supplier_id)
    if not supplier:
        raise NotFoundException("Supplier", supplier_id)
    return SupplierOut.model_validate(supplier)


@router.patch("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_inventory_manager),
):
    supplier_repo = SupplierRepository(db)
    supplier = supplier_repo.get_by_id(supplier_id)
    if not supplier:
        raise NotFoundException("Supplier", supplier_id)

    updated = supplier_repo.update(supplier, payload)
    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="UPDATE_SUPPLIER",
        entity_type="supplier",
        entity_id=str(updated.id),
        actor_id=manager.id,
        details={"name": updated.name, "is_active": updated.is_active},
    )
    db.commit()
    return SupplierOut.model_validate(updated)
