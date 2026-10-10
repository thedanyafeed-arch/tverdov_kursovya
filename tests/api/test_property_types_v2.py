"""Дополнительные v2-тесты типов недвижимости."""

from httpx import AsyncClient

from tests.api.helpers import assert_status, bearer_headers


class TestPropertyTypesV2:
    async def test_update_not_found(
        self,
        async_client: AsyncClient,
        manager_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.put(
            f"{api_v2_prefix}/property-types/999999",
            json={"name": "ghost"},
            headers=bearer_headers(manager_token),
        )
        assert_status(response, 404)
