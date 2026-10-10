from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings


def format_api_detail(detail: Any) -> str:
    """Короткое сообщение из ответа FastAPI (detail / validation errors)."""
    if detail is None:
        return "Ошибка запроса к API."
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        for item in detail:
            if not isinstance(item, dict):
                continue
            loc = item.get("loc") or ()
            msg = str(item.get("msg", ""))
            if any(part in loc for part in ("email", "username")) and msg:
                if "valid email" in msg.lower() or "@-sign" in msg.lower():
                    return "Некорректный email."
                return msg
            if "password" in loc and msg:
                if "at least" in msg.lower() or "string_too_short" in item.get("type", ""):
                    return "Пароль: минимум 6 символов."
                return msg
        first = detail[0] if detail else {}
        if isinstance(first, dict) and first.get("msg"):
            return str(first["msg"])
        return "Ошибка валидации данных."
    if isinstance(detail, dict):
        return str(detail.get("msg") or detail.get("detail") or detail)
    return str(detail)


class ApiClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    @property
    def user_message(self) -> str:
        text = str(self.args[0]) if self.args else ""
        if self.status_code == 401:
            if "Неверный" in text:
                return text
            return "Неверный email или пароль."
        if self.status_code == 400 and "email" in text.lower():
            return text
        if self.status_code == 422:
            return text or "Ошибка валидации."
        return text or "Ошибка API."


@dataclass
class ApiClient:
    """
    Тонкий HTTP-клиент для FastAPI.
    Важно: Django НЕ содержит бизнес-логики и НЕ хранит доменные данные.
    """

    token: str | None = None

    def _normalize_json(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {k: self._normalize_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize_json(v) for v in value]
        return value

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _url(self, path: str) -> str:
        return f"{settings.API_BASE_URL}{path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        if "json" in kwargs:
            kwargs["json"] = self._normalize_json(kwargs["json"])
        headers = kwargs.pop("headers", {})
        merged_headers = {**self._headers(), **headers}
        response = requests.request(
            method=method,
            url=self._url(path),
            headers=merged_headers,
            timeout=settings.API_TIMEOUT_SECONDS,
            **kwargs,
        )
        if response.status_code >= 400:
            detail: Any = response.text
            try:
                payload = response.json()
                detail = payload.get("detail", payload)
            except Exception:
                pass
            raise ApiClientError(format_api_detail(detail), response.status_code)
        if response.status_code == 204:
            return None
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.content

    # --- auth ---
    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request("POST", "/auth/login", data={"username": email, "password": password})

    def logout(self) -> dict[str, Any] | None:
        return self._request("POST", "/auth/logout")

    def register(self, email: str, password: str) -> dict[str, Any]:
        return self._request("POST", "/auth/register", json={"email": email, "password": password})

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    def list_users(self) -> list[dict[str, Any]]:
        return self._request("GET", "/auth/users")

    def update_me(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", "/auth/me", json=payload)

    def assign_user_role(self, user_id: int, role_name: str) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/auth/users/{user_id}/role",
            params={"role_name": role_name},
        )

    def delete_user_account(self, user_id: int) -> None:
        self._request("DELETE", f"/auth/users/{user_id}")

    # --- property-types (полный CRUD, менеджер/админ) ---
    def create_property_type(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/property-types", json={"name": name})

    def update_property_type(self, type_id: int, name: str) -> dict[str, Any]:
        return self._request("PUT", f"/property-types/{type_id}", json={"name": name})

    def delete_property_type(self, type_id: int) -> None:
        self._request("DELETE", f"/property-types/{type_id}")

    # --- catalog ---
    def list_property_types(self) -> list[dict[str, Any]]:
        return self._request("GET", "/property-types")

    def list_properties(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", "/properties", params=filters or {})

    def get_property(self, property_id: int) -> dict[str, Any]:
        return self._request("GET", f"/properties/{property_id}")

    # --- admin/manager CRUD ---
    def create_property(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/properties", json=payload)

    def update_property(self, property_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"/properties/{property_id}", json=payload)

    def update_property_status(self, property_id: int, status_value: str) -> dict[str, Any]:
        return self._request("PATCH", f"/properties/{property_id}/status", params={"new_status": status_value})

    def delete_property(self, property_id: int) -> None:
        self._request("DELETE", f"/properties/{property_id}")

    # --- media ---
    def list_all_documents(self) -> list[dict[str, Any]]:
        return self._request("GET", "/documents")

    def list_property_documents(self, property_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/documents/{property_id}")

    def list_property_photos(self, property_id: int) -> list[dict[str, Any]]:
        return self._request("GET", f"/photos/{property_id}")

    def list_all_photos(self) -> list[dict[str, Any]]:
        return self._request("GET", "/photos")

    def upload_photo(self, property_id: int, file_obj) -> dict[str, Any]:
        files = {
            "file": (
                file_obj.name,
                file_obj.read(),
                getattr(file_obj, "content_type", "application/octet-stream"),
            )
        }
        return self._request("POST", f"/photos/upload/{property_id}", files=files)

    def update_photo(self, photo_id: int, file_obj) -> dict[str, Any]:
        files = {
            "file": (
                file_obj.name,
                file_obj.read(),
                getattr(file_obj, "content_type", "application/octet-stream"),
            )
        }
        return self._request("PUT", f"/photos/{photo_id}", files=files)

    def delete_photo(self, photo_id: int) -> None:
        self._request("DELETE", f"/photos/{photo_id}")

    def upload_document(self, property_id: int, file_obj, doc_type: str) -> dict[str, Any]:
        files = {
            "file": (
                file_obj.name,
                file_obj.read(),
                getattr(file_obj, "content_type", "application/octet-stream"),
            )
        }
        return self._request(
            "POST",
            f"/documents/upload/{property_id}",
            params={"doc_type": doc_type},
            files=files,
        )

    def update_document(self, doc_id: int, file_obj, doc_type: str) -> dict[str, Any]:
        files = {
            "file": (
                file_obj.name,
                file_obj.read(),
                getattr(file_obj, "content_type", "application/octet-stream"),
            )
        }
        return self._request("PUT", f"/documents/{doc_id}", params={"doc_type": doc_type}, files=files)

    def delete_document(self, doc_id: int) -> None:
        self._request("DELETE", f"/documents/{doc_id}")

    def download_document(self, doc_id: int) -> bytes:
        return self._request("GET", f"/documents/download/{doc_id}")

    # --- contracts ---
    def list_contracts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/contracts")

    def list_all_contracts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/contracts/all")

    def generate_contract(self, property_id: int, manager_id: int | None = None) -> dict[str, Any]:
        params = {"manager_id": manager_id} if manager_id else {}
        return self._request("POST", f"/contracts/generate/{property_id}", params=params)

    def get_contract(self, contract_id: int) -> dict[str, Any]:
        return self._request("GET", f"/contracts/{contract_id}")

    def patch_contract(self, contract_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in payload.items() if v not in ("", None)}
        return self._request("PATCH", f"/contracts/{contract_id}", json=clean)

    def put_contract(self, contract_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", f"/contracts/{contract_id}", json=payload)

    def delete_contract(self, contract_id: int) -> None:
        self._request("DELETE", f"/contracts/{contract_id}")

    def download_contract(self, contract_id: int) -> bytes:
        return self._request("GET", f"/contracts/{contract_id}/download")
