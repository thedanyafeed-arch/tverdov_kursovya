from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PropertyDTO:
    """
    DTO для данных объекта недвижимости, пришедших из FastAPI.
    Используется на уровне UI-клиента (Django) только для удобства шаблонов.
    """

    id: int
    address: str | None
    status: str | None
    price: Any
    discount_price: Any
    property_type_id: int | None

    @staticmethod
    def from_api(payload: dict[str, Any]) -> "PropertyDTO":
        return PropertyDTO(
            id=int(payload.get("id")),
            address=payload.get("address"),
            status=payload.get("status"),
            price=payload.get("price"),
            discount_price=payload.get("discountPrice"),
            property_type_id=payload.get("propertyTypeId"),
        )

