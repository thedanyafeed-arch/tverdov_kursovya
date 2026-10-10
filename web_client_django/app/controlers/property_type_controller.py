from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PropertyTypeDTO:
    id: int
    name: str

    @staticmethod
    def from_api(payload: dict[str, Any]) -> "PropertyTypeDTO":
        return PropertyTypeDTO(id=int(payload["id"]), name=str(payload["name"]))

