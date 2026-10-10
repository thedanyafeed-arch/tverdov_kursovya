"""Фильтры для корректного URL статики на стороне FastAPI (/uploads/...)."""

from __future__ import annotations

from django import template

from ..media_urls import api_origin_from_settings, api_upload_absolute_url

register = template.Library()


@register.filter
def upload_abs(path: str | None) -> str:
    return api_upload_absolute_url(path, api_origin_from_settings())


@register.simple_tag(takes_context=True)
def api_file_url(context, file_path):
    origin = context.get("api_origin")
    if origin is None:
        origin = api_origin_from_settings()
    return api_upload_absolute_url(file_path, origin)
