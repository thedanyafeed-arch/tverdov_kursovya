from __future__ import annotations

import base64
import json
from typing import Any

from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect

from .services.api_client import ApiClient


def api_client(request: HttpRequest) -> ApiClient:
    return ApiClient(token=request.session.get("access_token"))


def extract_role_from_token(token: str | None) -> str | None:
    if not token or token.count(".") < 2:
        return None
    try:
        payload_part = token.split(".")[1]
        payload_part += "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part.encode("utf-8")).decode("utf-8"))
        return payload.get("role")
    except Exception:
        return None


def require_api_auth(request: HttpRequest):
    if not request.session.get("access_token"):
        messages.warning(request, "Сначала авторизуйтесь.")
        return redirect("login")
    return None


def role_name(request: HttpRequest) -> str | None:
    return request.session.get("role_name")


def is_manager_or_admin(request: HttpRequest) -> bool:
    return role_name(request) in {"manager", "admin"}


def require_manager(request: HttpRequest):
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect
    if not is_manager_or_admin(request):
        messages.error(request, "Недостаточно прав: нужны права manager/admin.")
        return redirect("catalog")
    return None


def require_admin(request: HttpRequest):
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect
    if request.session.get("role_name") != "admin":
        messages.error(request, "Недостаточно прав: требуется администратор.")
        return redirect("catalog")
    return None


def track_view_history(request: HttpRequest, property_obj: dict[str, Any]) -> None:
    """
    История просмотров хранится только в сессии (cookie), без БД.
    """
    try:
        pid = int(property_obj.get("id"))
    except Exception:
        return
    items: list[dict[str, Any]] = request.session.get("view_history", [])
    items = [x for x in items if x.get("id") != pid]
    items.insert(
        0,
        {
            "id": pid,
            "address": property_obj.get("address"),
            "price": property_obj.get("price"),
            "discountPrice": property_obj.get("discountPrice"),
            "status": property_obj.get("status"),
        },
    )
    request.session["view_history"] = items[:50]

