from .media_urls import api_origin_from_settings


def global_ui_context(request):
    role_name = request.session.get("role_name")
    return {
        "is_api_authenticated": bool(request.session.get("access_token")),
        "current_user": request.session.get("user_info"),
        "role_name": role_name,
        "can_manage": role_name in {"manager", "admin"},
        "is_admin": role_name == "admin",
        "api_origin": api_origin_from_settings(),
    }

