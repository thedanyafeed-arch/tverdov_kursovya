from sqlmodel import Field, Relationship
from typing import Optional, List
from decimal import Decimal
from .base import CamelModel
from .property_type import PropertyType

class RealEstateObject(CamelModel, table=True):
    id: int = Field(default=None, primary_key=True)
    property_type_id: int = Field(foreign_key="propertytype.id")
    total_area: float
    finishing: str
    wall_material: str
    floor: int
    floors_total: int
    price: Decimal
    discount_price: Decimal | None = None
    status: str  # 'в продаже', 'продан', 'забронирован'
    address: str
    description: str | None = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    property_type: PropertyType = Relationship()
    photos: List["Photo"] = Relationship(back_populates="real_estate_object")
    documents: List["Document"] = Relationship(back_populates="real_estate_object")
    contracts: List["Contract"] = Relationship(back_populates="real_estate_object")