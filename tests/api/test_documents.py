"""Тесты документов объектов."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.schemas.document_schema import DocumentResponse
from tests.api.conftest import API_V1_PREFIX, API_V2_PREFIX
from tests.api.helpers import assert_status, bearer_headers, sample_property_payload, validate_model

FAKE_PDF = ("doc.pdf", b"%PDF-1.4 pytest fake", "application/pdf")


@pytest.fixture
async def property_with_document(
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
        f"{api_v2_prefix}/documents/upload/{prop_id}",
        params={"doc_type": "схема"},
        files={"file": FAKE_PDF},
        headers=bearer_headers(manager_token),
    )
    assert_status(upload, 201)
    doc = validate_model(DocumentResponse, upload.json())

    yield {"property_id": prop_id, "doc_id": doc.id}

    await async_client.delete(
        f"{api_v2_prefix}/documents/{doc.id}",
        headers=bearer_headers(manager_token),
    )
    await async_client.delete(
        f"{api_v2_prefix}/properties/{prop_id}",
        headers=bearer_headers(manager_token),
    )


@pytest.mark.parametrize("api_prefix", [API_V1_PREFIX, API_V2_PREFIX], ids=["v1", "v2"])
class TestDocuments:
    async def test_list_by_property_public(
        self,
        async_client: AsyncClient,
        property_with_document: dict,
        api_prefix: str,
    ):
        prop_id = property_with_document["property_id"]
        response = await async_client.get(f"{api_prefix}/documents/{prop_id}")
        assert_status(response, 200)
        items = response.json()
        assert isinstance(items, list)
        if items:
            validate_model(DocumentResponse, items[0])

    async def test_list_all_requires_manager(
        self,
        async_client: AsyncClient,
        user_token: str,
        api_prefix: str,
    ):
        response = await async_client.get(
            f"{api_prefix}/documents",
            headers=bearer_headers(user_token),
        )
        assert_status(response, 403)


@pytest.mark.v2
class TestDocumentsFlow:
    async def test_upload_download_update_delete(
        self,
        async_client: AsyncClient,
        manager_token: str,
        property_with_document: dict,
        api_v2_prefix: str,
    ):
        doc_id = property_with_document["doc_id"]

        all_docs = await async_client.get(
            f"{api_v2_prefix}/documents",
            headers=bearer_headers(manager_token),
        )
        assert_status(all_docs, 200)

        download = await async_client.get(f"{api_v2_prefix}/documents/download/{doc_id}")
        assert_status(download, 200)
        assert download.content

        update = await async_client.put(
            f"{api_v2_prefix}/documents/{doc_id}",
            params={"doc_type": "план"},
            files={"file": ("doc2.pdf", b"%PDF-1.4 updated", "application/pdf")},
            headers=bearer_headers(manager_token),
        )
        assert_status(update, 200)
        validate_model(DocumentResponse, update.json())

    async def test_upload_without_file(
        self,
        async_client: AsyncClient,
        manager_token: str,
        property_type_id: int,
        api_v2_prefix: str,
    ):
        create = await async_client.post(
            f"{api_v2_prefix}/properties",
            json=sample_property_payload(property_type_id),
            headers=bearer_headers(manager_token),
        )
        assert_status(create, 201)
        prop_id = create.json()["id"]

        upload = await async_client.post(
            f"{api_v2_prefix}/documents/upload/{prop_id}",
            params={"doc_type": "схема"},
            headers=bearer_headers(manager_token),
        )
        assert_status(upload, 422)

        await async_client.delete(
            f"{api_v2_prefix}/properties/{prop_id}",
            headers=bearer_headers(manager_token),
        )

    async def test_download_not_found(
        self,
        async_client: AsyncClient,
        api_v2_prefix: str,
    ):
        response = await async_client.get(f"{api_v2_prefix}/documents/download/999999")
        assert_status(response, 404)
