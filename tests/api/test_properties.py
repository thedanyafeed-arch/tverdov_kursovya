"""Тесты объектов недвижимости."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.real_estate_object import RealEstateObject
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, sample_property_payload, validate_model


@pytest.fixture
async def created_property(
    async_client: AsyncClient,
    manager_token: str,
    property_type_id: int,
    api_v2_prefix: str,
):
    response = await async_client.post(
        f"{api_v2_prefix}/properties",
        json=sample_property_payload(property_type_id),
        headers=bearer_headers(manager_token),
    )
    assert_status(response, 201)
    prop = validate_model(RealEstateObject, response.json())
    yield prop
    await async_client.delete(
        f"{api_v2_prefix}/properties/{prop.id}",
        headers=bearer_headers(manager_token),
    )


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestProperties:
    async def test_list_public(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/properties")
        assert_status(response, 200)
        body = response.json()
        assert "items" in body
        assert "total" in body

    async def test_list_filters_min_price(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/properties", params={"min_price": 0})
        assert_status(response, 200)

    async def test_create_requires_manager(
        self,
        async_client: AsyncClient,
        user_token: str,
        property_type_id: int,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/properties",
            json=sample_property_payload(property_type_id),
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)

    async def test_create_invalid_body(
        self,
        async_client: AsyncClient,
        manager_token: str,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/properties",
            json={"propertyTypeId": "not-int"},
            headers=bearer_headers(manager_token),
        )
        assert_status(response, 422)

    async def test_get_by_id_not_found(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/properties/999999")
        assert_status(response, 404)


@pytest.mark.v2
class TestPropertiesV2Filters:
    async def test_list_filters_invalid_status(self, async_client: AsyncClient, api_v2_prefix: str):
        response = await async_client.get(
            f"{api_v2_prefix}/properties",
            params={"status_filter": "недопустимый"},
        )
        assert_status(response, 422)

    async def test_list_filters_invalid_price_range(
        self,
        async_client: AsyncClient,
        api_v2_prefix: str,
    ):
        response = await async_client.get(
            f"{api_v2_prefix}/properties",
            params={"min_price": 100, "max_price": 50},
        )
        assert_status(response, 422)


@pytest.mark.v2
class TestPropertiesFlow:
    async def test_crud_and_reserve(
        self,
        async_client: AsyncClient,
        manager_token: str,
        user_token: str,
        property_type_id: int,
        api_v2_prefix: str,
        created_property: RealEstateObject,
    ):
        prop_id = created_property.id

        get_resp = await async_client.get(f"{api_v2_prefix}/properties/{prop_id}")
        assert_status(get_resp, 200)
        validate_model(RealEstateObject, get_resp.json())

        status_resp = await async_client.patch(
            f"{api_v2_prefix}/properties/{prop_id}/status",
            params={"new_status": "забронирован"},
            headers=bearer_headers(manager_token),
        )
        assert_status(status_resp, 200)

        reserve_conflict = await async_client.post(
            f"{api_v2_prefix}/properties/{prop_id}/reserve",
            headers=bearer_headers(user_token),
        )
        assert_status(reserve_conflict, 409)

        replace_payload = sample_property_payload(
            property_type_id,
            address="Екатеринбург, обновлённый адрес",
            totalArea=60.0,
        )
        put_resp = await async_client.put(
            f"{api_v2_prefix}/properties/{prop_id}",
            json=replace_payload,
            headers=bearer_headers(manager_token),
        )
        assert_status(put_resp, 200)

    async def test_reserve_available_property(
        self,
        async_client: AsyncClient,
        manager_token: str,
        user_token: str,
        property_type_id: int,
        api_v2_prefix: str,
    ):
        create = await async_client.post(
            f"{api_v2_prefix}/properties",
            json=sample_property_payload(property_type_id, status="в продаже"),
            headers=bearer_headers(manager_token),
        )
        assert_status(create, 201)
        prop_id = create.json()["id"]

        reserve = await async_client.post(
            f"{api_v2_prefix}/properties/{prop_id}/reserve",
            headers=bearer_headers(user_token),
        )
        assert_status(reserve, 200)
        body = validate_model(RealEstateObject, reserve.json())
        assert body.status == "забронирован"

        await async_client.delete(
            f"{api_v2_prefix}/properties/{prop_id}",
            headers=bearer_headers(manager_token),
        )

    async def test_reserve_sold_conflict(
        self,
        async_client: AsyncClient,
        manager_token: str,
        user_token: str,
        property_type_id: int,
        api_v2_prefix: str,
    ):
        create = await async_client.post(
            f"{api_v2_prefix}/properties",
            json=sample_property_payload(property_type_id, status="продан"),
            headers=bearer_headers(manager_token),
        )
        assert_status(create, 201)
        prop_id = create.json()["id"]

        reserve = await async_client.post(
            f"{api_v2_prefix}/properties/{prop_id}/reserve",
            headers=bearer_headers(user_token),
        )
        assert_status(reserve, 409)

        await async_client.delete(
            f"{api_v2_prefix}/properties/{prop_id}",
            headers=bearer_headers(manager_token),
        )
