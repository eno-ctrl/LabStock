from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import DuplicateSKUException
from backend.app.models.balance import StockBalance
from backend.app.models.item import Item
from backend.app.schemas.item import ItemCreate, ItemFilter, ItemUpdate


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: int) -> Item | None:
        return (
            self.db.query(Item)
            .options(joinedload(Item.balance), joinedload(Item.supplier))
            .filter(Item.id == item_id)
            .first()
        )

    def get_by_sku(self, sku: str) -> Item | None:
        return (
            self.db.query(Item)
            .options(joinedload(Item.balance), joinedload(Item.supplier))
            .filter(func.upper(Item.sku) == sku.strip().upper())
            .first()
        )

    def list_items(self, filters: ItemFilter) -> tuple[list[Item], int]:
        q = self.db.query(Item).outerjoin(StockBalance, Item.id == StockBalance.item_id)

        # Active status filter
        if filters.is_active is not None:
            q = q.filter(Item.is_active == filters.is_active)

        # Text query filter
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            q = q.filter(
                (Item.sku.ilike(pattern))
                | (Item.name.ilike(pattern))
                | (Item.category.ilike(pattern))
                | (Item.storage_location.ilike(pattern))
                | (Item.manufacturer_model.ilike(pattern))
            )

        # Category filter
        if filters.category and filters.category != "All":
            q = q.filter(Item.category == filters.category)

        # Storage location filter
        if filters.storage_location:
            q = q.filter(Item.storage_location.ilike(f"%{filters.storage_location}%"))

        # Stock status filter
        if filters.status and filters.status.lower() != "all":
            status_val = filters.status.lower()
            if status_val == "out_of_stock":
                q = q.filter(
                    (StockBalance.quantity_on_hand.is_(None)) | (StockBalance.quantity_on_hand <= 0)
                )
            elif status_val == "low_stock":
                q = q.filter(
                    StockBalance.quantity_on_hand > 0,
                    StockBalance.quantity_on_hand <= Item.min_stock_threshold,
                )
            elif status_val == "in_stock":
                q = q.filter(StockBalance.quantity_on_hand > Item.min_stock_threshold)

        total = q.count()

        # Sorting
        sort_col = Item.name
        if filters.sort_by == "sku":
            sort_col = Item.sku
        elif filters.sort_by == "category":
            sort_col = Item.category
        elif filters.sort_by == "storage_location":
            sort_col = Item.storage_location
        elif filters.sort_by == "created_at":
            sort_col = Item.created_at
        elif filters.sort_by == "quantity_on_hand":
            sort_col = StockBalance.quantity_on_hand

        q = q.order_by(desc(sort_col)) if filters.sort_desc else q.order_by(sort_col.asc())

        skip = (filters.page - 1) * filters.page_size
        items = (
            q.options(joinedload(Item.balance), joinedload(Item.supplier))
            .offset(skip)
            .limit(filters.page_size)
            .all()
        )
        return items, total

    def create(self, item_in: ItemCreate) -> Item:
        sku = item_in.sku.strip().upper()
        if self.get_by_sku(sku):
            raise DuplicateSKUException(sku)

        item = Item(
            sku=sku,
            name=item_in.name.strip(),
            description=item_in.description.strip() if item_in.description else None,
            category=item_in.category.strip(),
            unit=item_in.unit.strip(),
            storage_location=item_in.storage_location.strip(),
            min_stock_threshold=item_in.min_stock_threshold,
            target_stock=item_in.target_stock,
            preferred_supplier_id=item_in.preferred_supplier_id,
            manufacturer_model=item_in.manufacturer_model.strip()
            if item_in.manufacturer_model
            else None,
            is_active=item_in.is_active,
        )
        self.db.add(item)
        self.db.flush()  # assign item.id

        # Initialize corresponding StockBalance record atomically
        balance = StockBalance(
            item_id=item.id,
            quantity_on_hand=0.0,
            reserved_quantity=0.0,
            available_to_issue=0.0,
            version=1,
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_metadata(self, item: Item, item_in: ItemUpdate) -> Item:
        """Update item metadata. Strictly NEVER mutates stock balance quantities."""
        if item_in.name is not None:
            item.name = item_in.name.strip()
        if item_in.description is not None:
            item.description = item_in.description.strip() if item_in.description else None
        if item_in.category is not None:
            item.category = item_in.category.strip()
        if item_in.unit is not None:
            item.unit = item_in.unit.strip()
        if item_in.storage_location is not None:
            item.storage_location = item_in.storage_location.strip()
        if item_in.min_stock_threshold is not None:
            item.min_stock_threshold = item_in.min_stock_threshold
        if item_in.target_stock is not None:
            item.target_stock = item_in.target_stock
        if item_in.preferred_supplier_id is not None:
            item.preferred_supplier_id = item_in.preferred_supplier_id
        if item_in.manufacturer_model is not None:
            item.manufacturer_model = (
                item_in.manufacturer_model.strip() if item_in.manufacturer_model else None
            )
        if item_in.is_active is not None:
            item.is_active = item_in.is_active

        self.db.commit()
        self.db.refresh(item)
        return item
