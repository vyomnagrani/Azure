from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from app.models import (
    HealthStatus,
    InventoryItem,
    InventorySummary,
    StockAdjustment,
)
from app.repository import (
    InMemoryInventoryRepository,
    InsufficientStockError,
    ItemNotFoundError,
)
from app.service import InventoryService

STATIC_DIR = Path(__file__).parent / "static"


def create_app(
    repository: InMemoryInventoryRepository | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Contoso Edge Store Inventory",
        version="0.1.0",
        description="Educational in-memory inventory API.",
    )
    service = InventoryService(repository or InMemoryInventoryRepository())

    def get_service() -> InventoryService:
        return service

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health/live", response_model=HealthStatus)
    def live() -> HealthStatus:
        return HealthStatus(status="ok")

    @app.get("/health/ready", response_model=HealthStatus)
    def ready() -> HealthStatus:
        return HealthStatus(status="ready")

    @app.get("/api/inventory", response_model=list[InventoryItem])
    def list_inventory(
        inventory: InventoryService = Depends(get_service),
    ) -> list[InventoryItem]:
        return inventory.list_items()

    @app.get("/api/inventory/summary", response_model=InventorySummary)
    def inventory_summary(
        inventory: InventoryService = Depends(get_service),
    ) -> InventorySummary:
        return inventory.summary()

    @app.get("/api/inventory/{sku}", response_model=InventoryItem)
    def get_inventory_item(
        sku: str,
        inventory: InventoryService = Depends(get_service),
    ) -> InventoryItem:
        try:
            return inventory.get_item(sku)
        except ItemNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Inventory item not found") from exc

    @app.post("/api/inventory/{sku}/adjust", response_model=InventoryItem)
    def adjust_inventory(
        sku: str,
        adjustment: StockAdjustment,
        inventory: InventoryService = Depends(get_service),
    ) -> InventoryItem:
        try:
            return inventory.adjust_stock(sku, adjustment.quantity_delta)
        except ItemNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Inventory item not found") from exc
        except InsufficientStockError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    return app


app = create_app()
