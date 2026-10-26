from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StockBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    quantity_on_hand: float
    reserved_quantity: float
    available_to_issue: float
    updated_at: datetime
