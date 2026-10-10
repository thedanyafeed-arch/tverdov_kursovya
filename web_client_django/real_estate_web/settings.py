from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "real_estate_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "app.context_processors.global_ui_context",
            ],
        },
    },
]

WSGI_APPLICATION = "real_estate_web.wsgi.application"

DATABASES = {
    "default": {
        # Проект работает как HTML-клиент для внешнего FastAPI:
        # Django НЕ хранит доменные данные и НЕ использует БД (SQLite запрещён).
        # Любая попытка обратиться к ORM должна падать сразу.
        "ENGINE": "django.db.backends.dummy",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Yekaterinburg"
USE_I18N = True
USE_TZ = True

#
# Статика по образцу из PDF: app/assets
# (оставляем также legacy /static, чтобы существующие файлы проекта продолжали работать)
STATIC_URL = "/app/assets/"
STATICFILES_DIRS = [BASE_DIR / "app" / "assets", BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v2")
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "20"))

# Сессии храним в подписанной cookie, без БД.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Базовые редиректы (в стиле PDF, но без django.contrib.auth).
LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/login/"
