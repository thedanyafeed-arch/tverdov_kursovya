"""Человекочитаемые подписи объектов недвижимости (тип — адрес) по данным API."""

from __future__ import annotations

from typing import Iterable

from .services.api_client import ApiClient, ApiClientError


def load_type_names(client: ApiClient) -> dict[int, str]:
    try:
        return {int(t["id"]): str(t["name"]).strip() for t in client.list_property_types()}
    except ApiClientError:
        return {}


def format_property_label(p: dict, type_names: dict[int, str] | None = None) -> str:
    if type_names is None:
        type_names = {}
    addr = (str(p.get("address") or "")).strip()
    pt = p.get("propertyTypeId")
    tname = ""
    if pt is not None:
        tname = type_names.get(int(pt), "").strip()
    if tname and addr:
        return f"{tname} — {addr}"
    if addr:
        return addr
    if tname:
        return tname
    rid = p.get("id")
    return f"Объект ({rid})" if rid is not None else "—"


def list_all_properties_flat(client: ApiClient) -> list[dict]:
    """Все записи объекта недвижимости из постраничного каталога API."""
    page = 1
    agg: list[dict] = []
    while True:
        try:
            data = client.list_properties(filters={"page": page, "size": 100})
        except ApiClientError:
            break
        items = list(data.get("items") or [])
        agg.extend(items)
        pages = int(data.get("pages") or 1)
        cur = int(data.get("page") or page)
        if cur >= pages or not items:
            break
        page += 1
    return agg


def build_user_email_map(client: ApiClient) -> dict[int, str]:
    """id → email (GET /auth/users для manager/admin)."""
    try:
        users = client.list_users()
    except ApiClientError:
        return {}
    return {int(u["id"]): (str(u.get("email") or "")).strip() or "—" for u in users}


def property_display_by_ids(client: ApiClient, ids: Iterable[int]) -> dict[int, str]:
    """Точное имя объекта по id (не зависит от попадания в первую страницу каталога)."""
    id_set = {int(x) for x in ids if x is not None}
    if not id_set:
        return {}
    type_names = load_type_names(client)
    out: dict[int, str] = {}
    for pid in sorted(id_set):
        try:
            p = client.get_property(pid)
            out[pid] = format_property_label(p, type_names)
        except ApiClientError:
            out[pid] = "—"
    return out
