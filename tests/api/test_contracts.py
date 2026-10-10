"""Тесты договоров."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlmodel import Session, select

from app.db.database import engine
from app.models.user import User
from app.schemas.contract_schema import ContractResponse
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, sample_property_payload, validate_model


@pytest.fixture
async def sale_property(
    async_client: AsyncClient,
    manager_token: str,
    property_type_id: int,
    api_v2_prefix: str,
):
    response = await async_client.post(
        f"{api_v2_prefix}/properties",
        json=sample_property_payload(property_type_id, status="в продаже"),
        headers=bearer_headers(manager_token),
    )
    assert_status(response, 201)
    prop_id = response.json()["id"]
    yield prop_id
    await async_client.delete(
        f"{api_v2_prefix}/properties/{prop_id}",
        headers=bearer_headers(manager_token),
    )


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestContractsAuth:
    async def test_list_requires_auth(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/contracts")
        assert_status(response, 401)

    async def test_all_requires_manager(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_prefix: str,
    ):
        response = await async_client.get(
            f"{api_prefix}/contracts/all",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)


@pytest.mark.v2
class TestContractsFlow:
    async def test_generate_and_crud(
        self,
        async_client: AsyncClient,
        user_token: str,
        manager_token: str,
        sale_property: int,
        api_v2_prefix: str,
    ):
        generate = await async_client.post(
            f"{api_v2_prefix}/contracts/generate/{sale_property}",
            headers=bearer_headers(user_token),
        )
        assert_status(generate, 201)
        contract = validate_model(ContractResponse, generate.json())
        contract_id = contract.id

        mine = await async_client.get(
            f"{api_v2_prefix}/contracts",
            headers=bearer_headers(user_token),
        )
        assert_status(mine, 200)
        assert any(c["id"] == contract_id for c in mine.json())

        all_contracts = await async_client.get(
            f"{api_v2_prefix}/contracts/all",
            headers=bearer_headers(manager_token),
        )
        assert_status(all_contracts, 200)

        get_one = await async_client.get(
            f"{api_v2_prefix}/contracts/{contract_id}",
            headers=bearer_headers(user_token),
        )
        assert_status(get_one, 200)

        download = await async_client.get(
            f"{api_v2_prefix}/contracts/{contract_id}/download",
            headers=bearer_headers(user_token),
        )
        assert_status(download, 200)

        patch = await async_client.patch(
            f"{api_v2_prefix}/contracts/{contract_id}",
            json={"status": "подписан"},
            headers=bearer_headers(manager_token),
        )
        assert_status(patch, 200)

        from tests.api.conftest import TEST_ADMIN_EMAIL, TEST_MANAGER_EMAIL

        with Session(engine) as session:
            admin_u = session.exec(select(User).where(User.email == TEST_ADMIN_EMAIL)).first()
            manager_u = session.exec(select(User).where(User.email == TEST_MANAGER_EMAIL)).first()
        assert admin_u and manager_u

        put = await async_client.put(
            f"{api_v2_prefix}/contracts/{contract_id}",
            json={
                "realEstateObjectId": sale_property,
                "userId": admin_u.id,
                "managerId": manager_u.id,
                "contractDate": "2026-05-16",
                "status": "подписан",
            },
            headers=bearer_headers(manager_token),
        )
        assert_status(put, 200)

        delete = await async_client.delete(
            f"{api_v2_prefix}/contracts/{contract_id}",
            headers=bearer_headers(manager_token),
        )
        assert_status(delete, 204)

    async def test_get_not_found(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.get(
            f"{api_v2_prefix}/contracts/999999",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 404)

    async def test_generate_property_not_found(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.post(
            f"{api_v2_prefix}/contracts/generate/999999",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 404)

    async def test_user_cannot_delete_contract(
        self,
        async_client: AsyncClient,
        user_token: str,
        manager_token: str,
        sale_property: int,
        api_v2_prefix: str,
    ):
        created = await async_client.post(
            f"{api_v2_prefix}/contracts/generate/{sale_property}",
            headers=bearer_headers(user_token),
        )
        assert_status(created, 201)
        contract_id = created.json()["id"]

        forbidden = await async_client.delete(
            f"{api_v2_prefix}/contracts/{contract_id}",
            headers=bearer_headers(user_token),
        )
        assert_status(forbidden, 403)

        await async_client.delete(
            f"{api_v2_prefix}/contracts/{contract_id}",
            headers=bearer_headers(manager_token),
        )

    async def test_contract_download_not_found(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.get(
            f"{api_v2_prefix}/contracts/999999/download",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 404)
