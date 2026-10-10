"""Тесты эндпоинтов аутентификации (v1 и v2)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.schemas.user_schema import ProfileUpdateResponse, UserPublic, UserRegisterResponse
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, login_and_get_token, validate_model


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestAuthPublic:
    async def test_login_success(
        self,
        async_client: AsyncClient,
        test_users,
        api_prefix: str,
    ):
        user = test_users["user"]
        response = await async_client.post(
            f"{api_prefix}/auth/login",
            data={"username": user["email"], "password": user["password"]},
        )
        assert_status(response, 200)
        body = response.json()
        assert body.get("token_type") == "bearer"
        assert isinstance(body.get("access_token"), str) and body["access_token"]

    async def test_login_empty_password(
        self,
        async_client: AsyncClient,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/auth/login",
            data={"username": test_users["user"]["email"], "password": ""},
        )
        assert_status(response, 401, 422)

    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/auth/login",
            data={"username": test_users["user"]["email"], "password": "WrongPass1!"},
        )
        assert_status(response, 401)

    async def test_register_success(
        self,
        async_client: AsyncClient,
        unique_email: str,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/auth/register",
            json={"email": unique_email, "password": "Password123"},
        )
        expected_status = 201 if api_prefix == API_V2_PREFIX else 200
        assert_status(response, expected_status)
        body = response.json()
        data = validate_model(UserRegisterResponse, body)
        assert data.user_id > 0
        assert "зарегистрирован" in data.message.lower()

    async def test_register_duplicate_email(
        self,
        async_client: AsyncClient,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.post(
            f"{api_prefix}/auth/register",
            json={"email": test_users["user"]["email"], "password": "Password123"},
        )
        assert_status(response, 400)

    @pytest.mark.parametrize(
        "payload,expected",
        [
            ({"email": "bad", "password": "123"}, 422),
            ({"email": "valid@example.com"}, 422),
            ({"password": "short"}, 422),
        ],
    )
    async def test_register_invalid_body(
        self,
        async_client: AsyncClient,
        payload: dict,
        expected: int,
        api_prefix: str,
    ):
        response = await async_client.post(f"{api_prefix}/auth/register", json=payload)
        assert_status(response, expected)

    async def test_logout(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.post(f"{api_prefix}/auth/logout")
        assert_status(response, 200)
        assert "message" in response.json()


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestAuthProtected:
    async def test_me_requires_auth(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/auth/me")
        assert_status(response, 401)

    async def test_me_success(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.get(
            f"{api_prefix}/auth/me",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 200)
        body = response.json()
        if api_prefix == API_V2_PREFIX:
            me = validate_model(UserPublic, body)
            assert me.email == test_users["user"]["email"]
            assert me.is_active is True
        else:
            assert body.get("email") == test_users["user"]["email"]
            assert body.get("isActive", body.get("is_active")) is True

    async def test_update_profile(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.patch(
            f"{api_prefix}/auth/me",
            json={"email": test_users["user"]["email"]},
            headers=bearer_headers(user_token),
        )
        assert_status(response, 200)
        if api_prefix == API_V2_PREFIX:
            data = validate_model(ProfileUpdateResponse, response.json())
            assert data.email == test_users["user"]["email"]
        else:
            assert "message" in response.json()

    async def test_update_profile_forbidden_extra_field(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_prefix: str,
    ):
        response = await async_client.patch(
            f"{api_prefix}/auth/me",
            json={"email": "other@example.com", "unknown": True},
            headers=bearer_headers(user_token),
        )
        assert_status(response, 422)

    async def test_assign_role_admin_only(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_users,
        api_prefix: str,
    ):
        response = await async_client.patch(
            f"{api_prefix}/auth/users/{test_users['user']['id']}/role",
            params={"role_name": "manager"},
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)

    async def test_assign_role_success(
        self,
        async_client: AsyncClient,
        admin_token: str,
        unique_email: str,
        api_prefix: str,
    ):
        reg = await async_client.post(
            f"{api_prefix}/auth/register",
            json={"email": unique_email, "password": "Password123"},
        )
        assert_status(reg, 201 if api_prefix == API_V2_PREFIX else 200)
        user_id = reg.json()["user_id"]

        response = await async_client.patch(
            f"{api_prefix}/auth/users/{user_id}/role",
            params={"role_name": "manager"},
            headers=bearer_headers(admin_token),
        )
        assert_status(response, 200)

        delete_resp = await async_client.delete(
            f"{api_prefix}/auth/users/{user_id}",
            headers=bearer_headers(admin_token),
        )
        if api_prefix == API_V2_PREFIX:
            assert_status(delete_resp, 204)
        else:
            assert delete_resp.status_code in (200, 204)

    async def test_delete_user_not_found(
        self,
        async_client: AsyncClient,
        admin_token: str,
        api_prefix: str,
    ):
        response = await async_client.delete(
            f"{api_prefix}/auth/users/999999",
            headers=bearer_headers(admin_token),
        )
        assert_status(response, 404)


@pytest.mark.v2
class TestAuthV2Only:
    async def test_list_users_manager(
        self,
        async_client: AsyncClient,
        manager_token: str,
    ):
        response = await async_client.get(
            f"{API_V2_PREFIX}/auth/users",
            headers=bearer_headers(manager_token),
        )
        assert_status(response, 200)
        assert isinstance(response.json(), list)

    async def test_list_users_forbidden_for_user(
        self,
        async_client: AsyncClient,
        user_token: str,
    ):
        response = await async_client.get(
            f"{API_V2_PREFIX}/auth/users",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)

    async def test_assign_role_invalid_pattern(
        self,
        async_client: AsyncClient,
        admin_token: str,
        test_users,
    ):
        response = await async_client.patch(
            f"{API_V2_PREFIX}/auth/users/{test_users['user']['id']}/role",
            params={"role_name": "invalid"},
            headers=bearer_headers(admin_token),
        )
        assert_status(response, 422)
