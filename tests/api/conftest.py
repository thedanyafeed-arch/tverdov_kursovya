"""Фикстуры интеграционных тестов FastAPI."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from fastapi_pagination.utils import disable_installed_extensions_check

from app.core.security import get_password_hash
from app.db.database import engine, init_db
from app.main import app_v1

disable_installed_extensions_check()
from app.models.property_type import PropertyType
from app.models.role import Role
from app.models.user import User

API_V1_PREFIX = ""
API_V2_PREFIX = "/api/v2"

TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "Password123")
TEST_ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "pytest_admin@example.com")
TEST_MANAGER_EMAIL = os.getenv("TEST_MANAGER_EMAIL", "pytest_manager@example.com")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "pytest_user@example.com")


@pytest.fixture(scope="session")
def db_initialized():
    init_db()
    yield


@pytest.fixture(scope="session")
def test_users(db_initialized) -> dict[str, dict[str, Any]]:
    """Создаёт фиксированных пользователей для всей сессии тестов."""
    emails = [TEST_ADMIN_EMAIL, TEST_MANAGER_EMAIL, TEST_USER_EMAIL]
    with Session(engine) as session:
        for email in emails:
            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                session.delete(user)
        session.commit()

        roles = {
            r.name: r
            for r in session.exec(select(Role)).all()
        }
        now = datetime.now().isoformat()
        users_data = [
            ("admin", TEST_ADMIN_EMAIL, roles["admin"].id),
            ("manager", TEST_MANAGER_EMAIL, roles["manager"].id),
            ("user", TEST_USER_EMAIL, roles["user"].id),
        ]
        created: dict[str, User] = {}
        for role_name, email, role_id in users_data:
            u = User(
                email=email,
                hashed_password=get_password_hash(TEST_PASSWORD),
                role_id=role_id,
                is_active=True,
                created_at=now,
            )
            session.add(u)
            created[role_name] = u
        session.commit()
        for u in created.values():
            session.refresh(u)

        result = {
            role: {
                "id": u.id,
                "email": u.email,
                "password": TEST_PASSWORD,
            }
            for role, u in created.items()
        }
    yield result
    with Session(engine) as session:
        for email in emails:
            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                session.delete(user)
        session.commit()


@pytest.fixture
def unique_email() -> str:
    return f"pytest_{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app_v1)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def api_v2_prefix() -> str:
    return API_V2_PREFIX


@pytest.fixture
def api_v1_prefix() -> str:
    return API_V1_PREFIX


@pytest.fixture
async def admin_token(async_client: AsyncClient, test_users) -> str:
    from tests.api.helpers import login_and_get_token

    return await login_and_get_token(
        async_client,
        API_V2_PREFIX,
        test_users["admin"]["email"],
        test_users["admin"]["password"],
    )


@pytest.fixture
async def manager_token(async_client: AsyncClient, test_users) -> str:
    from tests.api.helpers import login_and_get_token

    return await login_and_get_token(
        async_client,
        API_V2_PREFIX,
        test_users["manager"]["email"],
        test_users["manager"]["password"],
    )


@pytest.fixture
async def user_token(async_client: AsyncClient, test_users) -> str:
    from tests.api.helpers import login_and_get_token

    return await login_and_get_token(
        async_client,
        API_V2_PREFIX,
        test_users["user"]["email"],
        test_users["user"]["password"],
    )


@pytest.fixture
def auth_headers_admin(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_manager(manager_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
def auth_headers_user(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def property_type_id(db_initialized) -> int:
    with Session(engine) as session:
        pt = session.exec(select(PropertyType)).first()
        if pt is None:
            pt = PropertyType(name="квартира")
            session.add(pt)
            session.commit()
            session.refresh(pt)
        return pt.id
