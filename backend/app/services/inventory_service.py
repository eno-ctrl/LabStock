from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.models.item import Item
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.item_repo import ItemRepository
from backend.app.schemas.item import ItemCreate, ItemFilter, ItemUpdate


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.item_repo = ItemRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_item(self, item_id: int) -> Item:
        item = self.item_repo.get_by_id(item_id)
        if not item:
            raise NotFoundException("Item", item_id)
        return item

    def get_item_by_sku(self, sku: str) -> Item:
        item = self.item_repo.get_by_sku(sku)
        if not item:
            raise NotFoundException("Item", sku)
        return item

    def list_items(self, filters: ItemFilter) -> tuple[list[Item], int]:
        return self.item_repo.list_items(filters)

    def create_item(self, item_in: ItemCreate, actor_id: int | None = None) -> Item:
        item = self.item_repo.create(item_in)
        self.audit_repo.log_event(
            action="CREATE_ITEM",
            entity_type="item",
            entity_id=str(item.id),
            actor_id=actor_id,
            details={"sku": item.sku, "name": item.name, "category": item.category},
        )
        self.db.commit()
        return item

    def update_item_metadata(
        self, item_id: int, item_in: ItemUpdate, actor_id: int | None = None
    ) -> Item:
        item = self.get_item(item_id)
        updated = self.item_repo.update_metadata(item, item_in)
        self.audit_repo.log_event(
            action="UPDATE_ITEM_METADATA",
            entity_type="item",
            entity_id=str(item.id),
            actor_id=actor_id,
            details=item_in.model_dump(exclude_unset=True),
        )
        self.db.commit()
        return updated

    def set_active_status(self, item_id: int, is_active: bool, actor_id: int | None = None) -> Item:
        item = self.get_item(item_id)
        item.is_active = is_active
        self.db.commit()
        self.audit_repo.log_event(
            action="ACTIVATE_ITEM" if is_active else "DEACTIVATE_ITEM",
            entity_type="item",
            entity_id=str(item.id),
            actor_id=actor_id,
            details={"sku": item.sku, "is_active": is_active},
        )
        self.db.commit()
        return item

    @staticmethod
    def compute_stock_status(item: Item) -> str:
        qoh = item.balance.quantity_on_hand if item.balance else 0.0
        min_thresh = item.min_stock_threshold or 0.0
        if qoh <= 0:
            return "OUT_OF_STOCK"
        elif qoh <= min_thresh:
            return "LOW_STOCK"
        return "IN_STOCK"
