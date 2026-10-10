"""Тесты типов недвижимости."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.property_type import PropertyType
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, validate_model


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestPropertyTypes:
    async def test_list_public(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/property-types")
        assert_status(response, 200)
        items = response.json()
        assert isinstance(items, list)
        if items:
            validate_model(PropertyType, items[0])

    async def test_create_requires_manager(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/property-types",
            json={"name": "тест-тип"},
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)

    async def test_create_update_delete_flow(
        self,
        async_client: AsyncClient,
        manager_token: str,
        api_prefix: str,
    ):
        name = f"pytest-type-{uuid.uuid4().hex[:8]}"
        create = await async_client.post(
            f"{api_prefix}/property-types",
            json={"name": name},
            headers=bearer_headers(manager_token),
        )
        assert_status(create, 201)
        created = validate_model(PropertyType, create.json())
        type_id = created.id

        duplicate = await async_client.post(
            f"{api_prefix}/property-types",
            json={"name": name},
            headers=bearer_headers(manager_token),
        )
        if api_prefix == API_V2_PREFIX:
            assert_status(duplicate, 409)
        else:
            assert_status(duplicate, 201)

        update = await async_client.put(
            f"{api_prefix}/property-types/{type_id}",
            json={"name": f"{name}-updated"},
            headers=bearer_headers(manager_token),
        )
        assert_status(update, 200)
        updated = validate_model(PropertyType, update.json())
        assert updated.name == f"{name}-updated"

        delete = await async_client.delete(
            f"{api_prefix}/property-types/{type_id}",
            headers=bearer_headers(manager_token),
        )
        if api_prefix == API_V2_PREFIX:
            assert_status(delete, 204)
        else:
            assert delete.status_code in (200, 204)

