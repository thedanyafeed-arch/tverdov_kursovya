"""Сборка абсолютных URL файлов из ответов FastAPI (поле filePath — относительный путь)."""

from __future__ import annotations

from django.conf import settings


def api_origin_from_settings() -> str:
    api_origin = settings.API_BASE_URL
    if isinstance(api_origin, str) and api_origin.endswith("/api/v2"):
        api_origin = api_origin[: -len("/api/v2")]
    return api_origin.rstrip("/")


def api_upload_absolute_url(file_path: str | None, origin: str | None = None) -> str:
    """Склеивает origin со слешем и путь filePath вида uploads/photo.jpg или /uploads/...."""
    if not file_path:
        return ""
    fp = str(file_path).strip().replace("\\", "/")
    if fp.startswith(("http://", "https://")):
        return fp
    base = (origin if origin is not None else api_origin_from_settings()).rstrip("/")
    if not fp.startswith("/"):
        fp = "/" + fp
    return base + fp


def attach_photo_src(photo: dict, origin: str | None = None) -> dict:
    o = api_origin_from_settings() if origin is None else origin
    out = {**photo, "absoluteUrl": api_upload_absolute_url(photo.get("filePath"), o)}
    return out
