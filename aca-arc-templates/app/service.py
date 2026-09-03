from app.models import InventoryItem, InventorySummary, StockStatus
from app.repository import InMemoryInventoryRepository, InventoryRecord


class InventoryService:
    def __init__(self, repository: InMemoryInventoryRepository):
        self._repository = repository

    @staticmethod
    def _to_item(record: InventoryRecord) -> InventoryItem:
        if record.quantity == 0:
            status = StockStatus.OUT_OF_STOCK
        elif record.quantity <= record.reorder_level:
            status = StockStatus.LOW_STOCK
        else:
            status = StockStatus.IN_STOCK
        return InventoryItem(
            sku=record.sku,
            name=record.name,
            category=record.category,
            unit_price_cents=record.unit_price_cents,
            quantity=record.quantity,
            reorder_level=record.reorder_level,
            status=status,
        )

    def list_items(self) -> list[InventoryItem]:
        return [self._to_item(record) for record in self._repository.list()]

    def get_item(self, sku: str) -> InventoryItem:
        return self._to_item(self._repository.get(sku))

    def adjust_stock(self, sku: str, quantity_delta: int) -> InventoryItem:
        return self._to_item(self._repository.adjust(sku, quantity_delta))

    def summary(self) -> InventorySummary:
        items = self.list_items()
        return InventorySummary(
            distinct_items=len(items),
            total_units=sum(item.quantity for item in items),
            low_stock_items=sum(
                item.status == StockStatus.LOW_STOCK for item in items
            ),
            out_of_stock_items=sum(
                item.status == StockStatus.OUT_OF_STOCK for item in items
            ),
            inventory_value_cents=sum(
                item.quantity * item.unit_price_cents for item in items
            ),
        )
