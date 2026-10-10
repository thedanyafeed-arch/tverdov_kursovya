"""Дополнительные негативные тесты auth (v2)."""

import pytest
from httpx import AsyncClient

from tests.api.conftest import API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers


@pytest.mark.v2
class TestAuthExtraV2:
    async def test_register_invalid_email_format(self, async_client: AsyncClient):
        response = await async_client.post(
            f"{API_V2_PREFIX}/auth/register",
            json={"email": "not-email", "password": "Password123"},
        )
        assert_status(response, 422)

    async def test_logout_without_token(self, async_client: AsyncClient):
        response = await async_client.post(f"{API_V2_PREFIX}/auth/logout")
        assert_status(response, 200)

    async def test_register_short_password(self, async_client: AsyncClient, unique_email: str):
        response = await async_client.post(
            f"{API_V2_PREFIX}/auth/register",
            json={"email": unique_email, "password": "123"},
        )
        assert_status(response, 422)

    async def test_update_profile_rejects_unknown_field(
        self,
        async_client: AsyncClient,
        user_token: str,
    ):
        response = await async_client.patch(
            f"{API_V2_PREFIX}/auth/me",
            json={"unknownField": True},
            headers=bearer_headers(user_token),
        )
        assert_status(response, 422)
