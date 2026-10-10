"""Вспомогательные функции для API-тестов."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient, Response
from pydantic import BaseModel, ValidationError

from app.schemas.contract_schema import ContractResponse
from app.schemas.document_schema import DocumentResponse
from app.schemas.photo_schema import PhotoResponse
from app.models.property_type import PropertyType
from app.schemas.user_schema import UserPublic, UserRegisterResponse
from app.models.real_estate_object import RealEstateObject


async def login_and_get_token(
    client: AsyncClient,
    prefix: str,
    email: str,
    password: str,
) -> str:
    response = await client.post(
        f"{prefix}/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    token = payload.get("access_token")
    assert token, "access_token отсутствует в ответе login"
    return token


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_status(response: Response, *expected: int) -> None:
    assert response.status_code in expected, (
        f"Ожидался один из {expected}, получен {response.status_code}: {response.text[:500]}"
    )


def validate_model(model: type[BaseModel], data: Any) -> BaseModel:
    return model.model_validate(data)


def validate_or_none(model: type[BaseModel], data: Any) -> BaseModel | None:
    try:
        return model.model_validate(data)
    except ValidationError:
        return None


def sample_property_payload(property_type_id: int, **overrides: Any) -> dict[str, Any]:
    payload = {
        "propertyTypeId": property_type_id,
        "totalArea": 55.5,
        "finishing": "чистовая",
        "wallMaterial": "кирпич",
        "floor": 2,
        "floorsTotal": 10,
        "price": "4200000.00",
        "discountPrice": "4000000.00",
        "status": "в продаже",
        "address": "Екатеринбург, тестовая улица, 1",
        "description": "Объект для автотестов",
    }
    payload.update(overrides)
    return payload


# Re-export schema models used in assertions
__all__ = [
    "login_and_get_token",
    "bearer_headers",
    "assert_status",
    "validate_model",
    "sample_property_payload",
    "ContractResponse",
    "DocumentResponse",
    "PhotoResponse",
    "PropertyType",
    "UserPublic",
    "UserRegisterResponse",
    "RealEstateObject",
]
