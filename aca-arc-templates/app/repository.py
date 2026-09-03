from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True, slots=True)
class InventoryRecord:
    sku: str
    name: str
    category: str
    unit_price_cents: int
    quantity: int
    reorder_level: int


SEED_INVENTORY = (
    InventoryRecord("EDGE-CAM-01", "Aisle Camera", "Sensors", 12900, 12, 5),
    InventoryRecord("EDGE-TAG-04", "Shelf Tag Pack", "Displays", 4900, 4, 6),
    InventoryRecord("EDGE-GW-02", "Store Gateway", "Compute", 34900, 2, 1),
    InventoryRecord("EDGE-SCAN-03", "Handheld Scanner", "Devices", 18900, 0, 3),
)


class ItemNotFoundError(LookupError):
    pass


class InsufficientStockError(ValueError):
    pass


class InMemoryInventoryRepository:
    """Educational process-local storage; all data resets when the app restarts."""

    def __init__(self, records: tuple[InventoryRecord, ...] = SEED_INVENTORY):
        self._lock = RLock()
        self._records = {record.sku: record for record in records}

    def list(self) -> list[InventoryRecord]:
        with self._lock:
            return sorted(self._records.values(), key=lambda record: record.sku)

    def get(self, sku: str) -> InventoryRecord:
        with self._lock:
            try:
                return self._records[sku]
            except KeyError as exc:
                raise ItemNotFoundError(sku) from exc

    def adjust(self, sku: str, quantity_delta: int) -> InventoryRecord:
        with self._lock:
            current = self.get(sku)
            quantity = current.quantity + quantity_delta
            if quantity < 0:
                raise InsufficientStockError(
                    f"Adjustment would reduce {sku} below zero"
                )
            updated = InventoryRecord(
                sku=current.sku,
                name=current.name,
                category=current.category,
                unit_price_cents=current.unit_price_cents,
                quantity=quantity,
                reorder_level=current.reorder_level,
            )
            self._records[sku] = updated
            return updated

