from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Literal
from app.models.base import CamelModel

# Допустимые статусы объектов недвижимости
ALLOWED_STATUSES = ("в продаже", "продан", "забронирован")

class RealEstateObjectCreate(CamelModel):
    property_type_id: int
    total_area: float = Field(gt=0)
    finishing: str
    wall_material: str
    floor: int = Field(ge=1)
    floors_total: int = Field(ge=1)
    price: Decimal = Field(decimal_places=2, gt=0)
    discount_price: Decimal | None = Field(decimal_places=2, ge=0, default=None)
    status: Literal[*ALLOWED_STATUSES] = "в продаже"
    address: str
    description: str | None = None

class RealEstateObjectUpdate(CamelModel):
    property_type_id: int | None = None
    total_area: float | None = Field(default=None, gt=0)
    finishing: str | None = None
    wall_material: str | None = None
    floor: int | None = Field(default=None, ge=1)
    floors_total: int | None = Field(default=None, ge=1)
    price: Decimal | None = Field(default=None, decimal_places=2, gt=0)
    discount_price: Decimal | None = Field(decimal_places=2, ge=0, default=None)
    status: Literal[*ALLOWED_STATUSES] | None = None
    address: str | None = None
    description: str | None = None

    model_config = {"extra": "forbid"}  # запрещает лишние поля


class RealEstateObjectReplace(CamelModel):
    property_type_id: int
    total_area: float = Field(gt=0)
    finishing: str
    wall_material: str
    floor: int = Field(ge=1)
    floors_total: int = Field(ge=1)
    price: Decimal = Field(decimal_places=2, gt=0)
    discount_price: Decimal | None = Field(decimal_places=2, ge=0, default=None)
    status: Literal[*ALLOWED_STATUSES]
    address: str
    description: str | None = None

    model_config = {"extra": "forbid"}