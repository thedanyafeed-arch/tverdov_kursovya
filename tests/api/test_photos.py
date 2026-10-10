"""Тесты фотографий объектов."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.schemas.photo_schema import PhotoResponse
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, sample_property_payload, validate_model

FAKE_JPEG = ("photo.jpg", b"\xff\xd8\xff fake jpeg content", "image/jpeg")


@pytest.fixture
async def property_with_photo(
    async_client: AsyncClient,
    manager_token: str,
    property_type_id: int,
    api_v2_prefix: str,
):
    prop_resp = await async_client.post(
        f"{api_v2_prefix}/properties",
        json=sample_property_payload(property_type_id),
        headers=bearer_headers(manager_token),
    )
    assert_status(prop_resp, 201)
    prop_id = prop_resp.json()["id"]

    upload = await async_client.post(
        f"{api_v2_prefix}/photos/upload/{prop_id}",
        files={"file": FAKE_JPEG},
        headers=bearer_headers(manager_token),
    )
    assert_status(upload, 201)
    photo = validate_model(PhotoResponse, upload.json())

    yield {"property_id": prop_id, "photo_id": photo.id}

    await async_client.delete(
        f"{api_v2_prefix}/photos/{photo.id}",
        headers=bearer_headers(manager_token),
    )
    await async_client.delete(
        f"{api_v2_prefix}/properties/{prop_id}",
        headers=bearer_headers(manager_token),
    )


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestPhotos:
    async def test_list_all_public(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/photos")
        assert_status(response, 200)
        assert isinstance(response.json(), list)

    async def test_list_by_property_empty(self, async_client: AsyncClient, api_prefix: str):
        response = await async_client.get(f"{api_prefix}/photos/999999")
        assert_status(response, 200)
        assert response.json() == []

    async def test_upload_requires_manager(
        self,
        async_client: AsyncClient,
        user_token: str,
        property_type_id: int,
        manager_token: str,
        api_prefix: str,
    ):
        create = await async_client.post(
            f"{api_prefix}/properties",
            json=sample_property_payload(property_type_id),
            headers=bearer_headers(manager_token),
        )
        assert_status(create, 201)
        prop_id = create.json()["id"]

        upload = await async_client.post(
            f"{api_prefix}/photos/upload/{prop_id}",
            files={"file": FAKE_JPEG},
            headers=bearer_headers(user_token),
        )
        assert_status(upload, 403)

        await async_client.delete(
            f"{api_prefix}/properties/{prop_id}",
            headers=bearer_headers(manager_token),
        )


@pytest.mark.v2
class TestPhotosFlow:
    async def test_upload_list_update_delete(
        self,
        async_client: AsyncClient,
        manager_token: str,
        property_with_photo: dict,
        api_v2_prefix: str,
    ):
        prop_id = property_with_photo["property_id"]
        photo_id = property_with_photo["photo_id"]

        by_prop = await async_client.get(f"{api_v2_prefix}/photos/{prop_id}")
        assert_status(by_prop, 200)
        assert len(by_prop.json()) >= 1

        update = await async_client.put(
            f"{api_v2_prefix}/photos/{photo_id}",
            files={"file": ("photo2.jpg", b"updated-image", "image/jpeg")},
            headers=bearer_headers(manager_token),
        )
        assert_status(update, 200)
        validate_model(PhotoResponse, update.json())

    async def test_delete_not_found(
        self,
        async_client: AsyncClient,
        manager_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.delete(
            f"{api_v2_prefix}/photos/999999",
            headers=bearer_headers(manager_token),
        )
        assert_status(response, 404)

    async def test_upload_property_not_found(
        self,
        async_client: AsyncClient,
        manager_token: str,
        api_v2_prefix: str,
    ):
        response = await async_client.post(
            f"{api_v2_prefix}/photos/upload/999999",
            files={"file": FAKE_JPEG},
            headers=bearer_headers(manager_token),
        )
        assert_status(response, 404)
