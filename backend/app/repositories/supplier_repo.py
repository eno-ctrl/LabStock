from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.supplier import Supplier
from backend.app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_name(self, name: str) -> Supplier | None:
        return (
            self.db.query(Supplier)
            .filter(func.lower(Supplier.name) == name.lower().strip())
            .first()
        )

    def list_suppliers(
        self,
        query: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Supplier], int]:
        q = self.db.query(Supplier)
        if query:
            pattern = f"%{query.strip()}%"
            q = q.filter(
                (Supplier.name.ilike(pattern))
                | (Supplier.contact_person.ilike(pattern))
                | (Supplier.email.ilike(pattern))
            )
        if is_active is not None:
            q = q.filter(Supplier.is_active == is_active)

        total = q.count()
        items = q.order_by(Supplier.name.asc()).offset(skip).limit(limit).all()
        return items, total

    def create(self, supplier_in: SupplierCreate) -> Supplier:
        db_supplier = Supplier(
            name=supplier_in.name.strip(),
            contact_person=supplier_in.contact_person.strip()
            if supplier_in.contact_person
            else None,
            email=supplier_in.email.strip() if supplier_in.email else None,
            phone=supplier_in.phone.strip() if supplier_in.phone else None,
            address=supplier_in.address.strip() if supplier_in.address else None,
            notes=supplier_in.notes.strip() if supplier_in.notes else None,
            is_active=supplier_in.is_active,
        )
        self.db.add(db_supplier)
        self.db.commit()
        self.db.refresh(db_supplier)
        return db_supplier

    def update(self, supplier: Supplier, supplier_in: SupplierUpdate) -> Supplier:
        if supplier_in.name is not None:
            supplier.name = supplier_in.name.strip()
        if supplier_in.contact_person is not None:
            supplier.contact_person = (
                supplier_in.contact_person.strip() if supplier_in.contact_person else None
            )
        if supplier_in.email is not None:
            supplier.email = supplier_in.email.strip() if supplier_in.email else None
        if supplier_in.phone is not None:
            supplier.phone = supplier_in.phone.strip() if supplier_in.phone else None
        if supplier_in.address is not None:
            supplier.address = supplier_in.address.strip() if supplier_in.address else None
        if supplier_in.notes is not None:
            supplier.notes = supplier_in.notes.strip() if supplier_in.notes else None
        if supplier_in.is_active is not None:
            supplier.is_active = supplier_in.is_active

        self.db.commit()
        self.db.refresh(supplier)
        return supplier
