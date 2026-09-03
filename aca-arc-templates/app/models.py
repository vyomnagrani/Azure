from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class InventoryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    category: str
    unit_price_cents: int = Field(ge=0)
    quantity: int = Field(ge=0)
    reorder_level: int = Field(ge=0)
    status: StockStatus


class StockAdjustment(BaseModel):
    quantity_delta: int = Field(ge=-1000, le=1000)

    @field_validator("quantity_delta")
    @classmethod
    def adjustment_must_not_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_delta must not be zero")
        return value


class InventorySummary(BaseModel):
    distinct_items: int = Field(ge=0)
    total_units: int = Field(ge=0)
    low_stock_items: int = Field(ge=0)
    out_of_stock_items: int = Field(ge=0)
    inventory_value_cents: int = Field(ge=0)


class HealthStatus(BaseModel):
    status: str

