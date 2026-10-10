"""Фикстуры Selenium E2E для Django-клиента."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

DJANGO_ROOT = Path(__file__).resolve().parents[2] / "web_client_django"
if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_web.settings")

import pytest
from faker import Faker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from tests.e2e.pages import CatalogPage, HomePage, LoginPage, RegisterPage

fake = Faker("ru_RU")
fake_en = Faker()

# FastAPI обычно на :8000, Django-клиент — на :8001 (см. web_client_django/README.md)
DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
SELENIUM_BROWSER = os.getenv("SELENIUM_BROWSER", "chrome")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "pytest_user@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "Password123")
TEST_MANAGER_EMAIL = os.getenv("TEST_MANAGER_EMAIL", "pytest_manager@example.com")
TEST_MANAGER_PASSWORD = os.getenv("TEST_MANAGER_PASSWORD", "Password123")


def _host_reachable(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _looks_like_django_home(html: str) -> bool:
    """Отличаем Django UI от FastAPI/Swagger на том же хосте."""
    markers = ("АРМ застройщика", "id_email", "csrfmiddlewaretoken", "Перейти в каталог")
    return any(marker in html for marker in markers)


def _fetch_homepage(url: str) -> str:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "pytest-e2e"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _ensure_api_test_user() -> None:
    """Создаёт pytest_user@example.com через API, если его ещё нет (как tests/api)."""
    import json
    import urllib.error
    import urllib.request

    api_base = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v2").rstrip("/")
    email = TEST_USER_EMAIL
    password = TEST_USER_PASSWORD

    login_req = urllib.request.Request(
        f"{api_base}/auth/login",
        data=f"username={email}&password={password}".encode(),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(login_req, timeout=5):
            return
    except urllib.error.HTTPError:
        pass

    register_body = json.dumps({"email": email, "password": password}).encode()
    register_req = urllib.request.Request(
        f"{api_base}/auth/register",
        data=register_body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(register_req, timeout=5):
            return
    except urllib.error.HTTPError as exc:
        if exc.code not in (400, 409):
            raise


@pytest.fixture(scope="session", autouse=True)
def ensure_e2e_test_user(django_base_url):
    try:
        _ensure_api_test_user()
    except Exception as exc:
        pytest.skip(f"Не удалось подготовить тестового пользователя API: {exc}")


@pytest.fixture(scope="session")
def django_base_url() -> str:
    if not _host_reachable(DJANGO_BASE_URL):
        pytest.skip(
            f"Сервер недоступен по {DJANGO_BASE_URL}. "
            "Запустите Django: cd web_client_django && python manage.py runserver 8001"
        )
    try:
        html = _fetch_homepage(f"{DJANGO_BASE_URL}/")
    except Exception as exc:
        pytest.skip(f"Не удалось открыть {DJANGO_BASE_URL}/: {exc}")

    if not _looks_like_django_home(html):
        pytest.skip(
            f"По адресу {DJANGO_BASE_URL} отвечает не Django-клиент "
            "(скорее всего FastAPI на :8000). "
            "Запустите Django на другом порту и задайте: "
            '$env:DJANGO_BASE_URL="http://127.0.0.1:8001"'
        )
    return DJANGO_BASE_URL


@pytest.fixture
def get_faker_email():
    return fake_en.email()


@pytest.fixture
def get_faker_password():
    return fake_en.password(
        length=12,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )


@pytest.fixture
def browser(django_base_url):
    if SELENIUM_BROWSER == "firefox":
        options = FirefoxOptions()
        service = webdriver.FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    else:
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(8)
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def _reset_browser(browser):
    yield
    try:
        browser.delete_all_cookies()
        browser.get("about:blank")
    except Exception:
        pass


@pytest.fixture
def open_page(browser, django_base_url):
    def _open(path: str = "", page_class=None):
        url = f"{django_base_url}/{path.lstrip('/')}"
        browser.get(url)
        if page_class:
            page = page_class(browser)
            page.wait_for_page_load()
            return page
        return browser

    return _open


@pytest.fixture
def home_page(open_page):
    return open_page("", HomePage)


@pytest.fixture
def login_page(open_page):
    return open_page("login/", LoginPage)


@pytest.fixture
def register_page(open_page):
    return open_page("register/", RegisterPage)


@pytest.fixture
def catalog_page(open_page):
    return open_page("catalog/", CatalogPage)


@pytest.fixture
def test_user_credentials():
    return {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}


@pytest.fixture
def test_manager_credentials():
    return {"email": TEST_MANAGER_EMAIL, "password": TEST_MANAGER_PASSWORD}
