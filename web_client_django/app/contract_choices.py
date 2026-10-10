"""Варианты для форм договора: объекты (тип — адрес), клиент и менеджер по email из API."""

from __future__ import annotations

from typing import Any

from .property_labels import format_property_label, list_all_properties_flat, load_type_names
from .services.api_client import ApiClient, ApiClientError


def _ensure_option(choices: list[tuple[str, str]], value_id: int | None, label: str) -> None:
    if value_id is None:
        return
    s = str(int(value_id))
    if any(s == c[0] for c in choices):
        return
    choices.append((s, label))


def property_select_choices(client: ApiClient, contract: dict[str, Any] | None = None) -> list[tuple[str, str]]:
    type_names = load_type_names(client)
    items = list_all_properties_flat(client)
    seen_ids: set[int] = set()
    out: list[tuple[str, str]] = []
    for p in sorted(items, key=lambda x: int(x.get("id") or 0)):
        pid = int(p["id"])
        seen_ids.add(pid)
        out.append((str(pid), format_property_label(p, type_names)))

    if contract and contract.get("realEstateObjectId") is not None:
        oid = int(contract["realEstateObjectId"])
        if oid not in seen_ids:
            try:
                extra = client.get_property(oid)
                out.append((str(oid), format_property_label(extra, type_names)))
            except ApiClientError:
                _ensure_option(out, oid, format_property_label({"id": oid, "address": "", "propertyTypeId": None}, type_names))

    out.sort(key=lambda x: int(x[0]))
    return out


def _ids_from_contracts_fallback(client: ApiClient, contract: dict[str, Any]) -> tuple[list[int], list[int]]:
    uids: set[int] = set()
    mids: set[int] = set()
    try:
        ctrs = client.list_all_contracts()
    except ApiClientError:
        ctrs = []
    for c in ctrs:
        if c.get("userId") is not None:
            uids.add(int(c["userId"]))
        if c.get("managerId") is not None:
            mids.add(int(c["managerId"]))
    if contract.get("userId") is not None:
        uids.add(int(contract["userId"]))
    if contract.get("managerId") is not None:
        mids.add(int(contract["managerId"]))
    return sorted(uids), sorted(mids)


def user_and_manager_select_choices(
    client: ApiClient, contract: dict[str, Any]
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    try:
        users = client.list_users()
    except ApiClientError:
        users = None

    if users:
        email_by_uid: dict[int, str] = {}
        role_by_uid: dict[int, str] = {}
        for u in users:
            uid = int(u["id"])
            email_by_uid[uid] = (str(u.get("email") or "")).strip() or "—"
            role_by_uid[uid] = str(u.get("roleName") or "").lower()

        buyers = [(str(uid), email_by_uid[uid]) for uid in sorted(email_by_uid)]
        mgr_ids = sorted(uid for uid, r in role_by_uid.items() if r in {"manager", "admin"})
        managers = [(str(uid), email_by_uid[uid]) for uid in mgr_ids]
        if contract.get("managerId") is not None:
            mid = int(contract["managerId"])
            have_mid = {int(x[0]) for x in managers}
            if mid not in have_mid:
                managers.append((str(mid), email_by_uid.get(mid, "—")))
                managers.sort(key=lambda x: int(x[0]))

        return buyers, managers

    uids, mids = _ids_from_contracts_fallback(client, contract)
    buyers = [(str(i), f"Клиент №{i} (нет email в API)") for i in uids]
    managers = [(str(i), f"Ответственный №{i}") for i in mids]
    return buyers, managers


def apply_contract_full_choices(form, client: ApiClient, contract: dict[str, Any]) -> None:
    form.fields["real_estate_object_id"].choices = property_select_choices(client, contract)
    buyer_ch, mgr_ch = user_and_manager_select_choices(client, contract)
    form.fields["user_id"].choices = buyer_ch
    form.fields["manager_id"].choices = mgr_ch
