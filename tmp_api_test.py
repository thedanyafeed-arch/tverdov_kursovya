import json
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.db.database import engine, init_db
from app.main import app_v1
from app.models.contract import Contract
from app.models.document import Document
from app.models.photo import Photo
from app.models.property_type import PropertyType
from app.models.real_estate_object import RealEstateObject
from app.models.role import Role
from app.models.user import User


results = []


def rec(name, method, path, status, expected, detail=None):
    ok = status in expected
    results.append(
        {
            "name": name,
            "method": method,
            "path": path,
            "status": status,
            "expected": expected,
            "ok": ok,
            "detail": detail,
        }
    )


def main():
    init_db()
    with Session(engine) as s:
        for m in s.exec(select(Contract)).all():
            s.delete(m)
        for m in s.exec(select(Document)).all():
            s.delete(m)
        for m in s.exec(select(Photo)).all():
            s.delete(m)
        for m in s.exec(select(RealEstateObject)).all():
            s.delete(m)
        for m in s.exec(
            select(User).where(
                User.email.in_(
                    [
                        "admin_test@example.com",
                        "manager_test@example.com",
                        "user_test@example.com",
                        "new_user_test@example.com",
                    ]
                )
            )
        ).all():
            s.delete(m)
        s.commit()

        role_admin = s.exec(select(Role).where(Role.name == "admin")).first()
        role_manager = s.exec(select(Role).where(Role.name == "manager")).first()
        role_user = s.exec(select(Role).where(Role.name == "user")).first()

        admin = User(
            email="admin_test@example.com",
            hashed_password=get_password_hash("Password123"),
            role_id=role_admin.id,
            is_active=True,
            created_at=datetime.now().isoformat(),
        )
        manager = User(
            email="manager_test@example.com",
            hashed_password=get_password_hash("Password123"),
            role_id=role_manager.id,
            is_active=True,
            created_at=datetime.now().isoformat(),
        )
        user = User(
            email="user_test@example.com",
            hashed_password=get_password_hash("Password123"),
            role_id=role_user.id,
            is_active=True,
            created_at=datetime.now().isoformat(),
        )
        s.add(admin)
        s.add(manager)
        s.add(user)
        s.commit()
        s.refresh(admin)
        s.refresh(manager)
        s.refresh(user)

        ptype = s.exec(select(PropertyType)).first()
        if ptype is None:
            ptype = PropertyType(name="квартира")
            s.add(ptype)
            s.commit()
            s.refresh(ptype)

    client = TestClient(app_v1)

    def login(email, password):
        return client.post("/api/v2/auth/login", data={"username": email, "password": password})

    r = login("user_test@example.com", "Password123")
    user_token = r.json().get("access_token") if r.status_code == 200 else None
    rec("auth login user", "POST", "/api/v2/auth/login", r.status_code, [200], r.text[:300])

    r = login("manager_test@example.com", "Password123")
    manager_token = r.json().get("access_token") if r.status_code == 200 else None
    rec("auth login manager", "POST", "/api/v2/auth/login", r.status_code, [200], r.text[:300])

    r = login("admin_test@example.com", "Password123")
    admin_token = r.json().get("access_token") if r.status_code == 200 else None
    rec("auth login admin", "POST", "/api/v2/auth/login", r.status_code, [200], r.text[:300])

    headers_user = {"Authorization": f"Bearer {user_token}"} if user_token else {}
    headers_manager = {"Authorization": f"Bearer {manager_token}"} if manager_token else {}
    headers_admin = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

    r = client.post("/api/v2/auth/register", json={"email": "new_user_test@example.com", "password": "Password123"})
    rec("auth register", "POST", "/api/v2/auth/register", r.status_code, [201], r.text[:300])

    r = client.get("/api/v2/auth/me", headers=headers_user)
    rec("auth me", "GET", "/api/v2/auth/me", r.status_code, [200], r.text[:300])

    r = client.patch("/api/v2/auth/me", json={"email": "user_test@example.com"}, headers=headers_user)
    rec("auth update me", "PATCH", "/api/v2/auth/me", r.status_code, [200], r.text[:300])

    r = client.post("/api/v2/auth/logout")
    rec("auth logout", "POST", "/api/v2/auth/logout", r.status_code, [200], r.text[:300])

    r = client.get("/api/v2/property-types")
    rec("property-types list", "GET", "/api/v2/property-types", r.status_code, [200], r.text[:300])

    r = client.post("/api/v2/property-types", json={"name": "таунхаус"}, headers=headers_manager)
    rec("property-types create", "POST", "/api/v2/property-types", r.status_code, [201, 409], r.text[:300])
    created_type_id = r.json().get("id") if r.status_code == 201 else None

    if created_type_id:
        r2 = client.put(
            f"/api/v2/property-types/{created_type_id}",
            json={"name": "таунхаус-plus"},
            headers=headers_manager,
        )
        rec("property-types update", "PUT", f"/api/v2/property-types/{created_type_id}", r2.status_code, [200], r2.text[:300])

    with Session(engine) as s:
        ptype = s.exec(select(PropertyType)).first()
        ptype_id = ptype.id

    payload_property = {
        "propertyTypeId": ptype_id,
        "totalArea": 45.5,
        "finishing": "чистовая",
        "wallMaterial": "кирпич",
        "floor": 3,
        "floorsTotal": 9,
        "price": 3500000.00,
        "discountPrice": 3300000.00,
        "status": "в продаже",
        "address": "Екатеринбург, Тестовая 1",
        "description": "тестовый объект",
    }
    r = client.post("/api/v2/properties", json=payload_property, headers=headers_manager)
    rec("properties create", "POST", "/api/v2/properties", r.status_code, [201], r.text[:300])
    property_id = r.json().get("id") if r.status_code == 201 else None

    r = client.get("/api/v2/properties")
    rec("properties list", "GET", "/api/v2/properties", r.status_code, [200], r.text[:300])

    r = client.get("/api/v2/properties", params={"min_price": 0})
    rec("properties list min_price=0", "GET", "/api/v2/properties?min_price=0", r.status_code, [200], r.text[:300])

    if property_id:
        r = client.get(f"/api/v2/properties/{property_id}")
        rec("properties get by id", "GET", f"/api/v2/properties/{property_id}", r.status_code, [200], r.text[:300])

        r = client.patch(
            f"/api/v2/properties/{property_id}/status",
            params={"new_status": "забронирован"},
            headers=headers_manager,
        )
        rec("properties patch status", "PATCH", f"/api/v2/properties/{property_id}/status", r.status_code, [200], r.text[:300])

        r = client.post(f"/api/v2/properties/{property_id}/reserve", headers=headers_user)
        rec("properties reserve conflict", "POST", f"/api/v2/properties/{property_id}/reserve", r.status_code, [409], r.text[:300])

        replace_payload = {
            "propertyTypeId": ptype_id,
            "totalArea": 46.0,
            "finishing": "чистовая",
            "wallMaterial": "кирпич",
            "floor": 4,
            "floorsTotal": 9,
            "price": 3600000.00,
            "discountPrice": 3200000.00,
            "status": "в продаже",
            "address": "Екатеринбург, Тестовая 2",
            "description": "updated",
        }
        r = client.put(f"/api/v2/properties/{property_id}", json=replace_payload, headers=headers_manager)
        rec("properties put replace", "PUT", f"/api/v2/properties/{property_id}", r.status_code, [200], r.text[:300])

    photo_id = None
    if property_id:
        r = client.post(
            f"/api/v2/photos/upload/{property_id}",
            files={"file": ("photo.jpg", b"fake-image", "image/jpeg")},
            headers=headers_manager,
        )
        rec("photos upload", "POST", f"/api/v2/photos/upload/{property_id}", r.status_code, [201], r.text[:300])
        photo_id = r.json().get("id") if r.status_code == 201 else None

        r = client.get("/api/v2/photos")
        rec("photos list all", "GET", "/api/v2/photos", r.status_code, [200], r.text[:300])

        r = client.get(f"/api/v2/photos/{property_id}")
        rec("photos list by property", "GET", f"/api/v2/photos/{property_id}", r.status_code, [200], r.text[:300])

        if photo_id:
            r = client.put(
                f"/api/v2/photos/{photo_id}",
                files={"file": ("photo2.jpg", b"fake-image-2", "image/jpeg")},
                headers=headers_manager,
            )
            rec("photos update", "PUT", f"/api/v2/photos/{photo_id}", r.status_code, [200], r.text[:300])

    doc_id = None
    if property_id:
        r = client.post(
            f"/api/v2/documents/upload/{property_id}",
            params={"doc_type": "схема"},
            files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
            headers=headers_manager,
        )
        rec("documents upload", "POST", f"/api/v2/documents/upload/{property_id}", r.status_code, [201], r.text[:300])
        doc_id = r.json().get("id") if r.status_code == 201 else None

        r = client.get(f"/api/v2/documents/{property_id}")
        rec("documents list by property", "GET", f"/api/v2/documents/{property_id}", r.status_code, [200], r.text[:300])

        r = client.get("/api/v2/documents", headers=headers_manager)
        rec("documents list all", "GET", "/api/v2/documents", r.status_code, [200], r.text[:300])

        if doc_id:
            r = client.get(f"/api/v2/documents/download/{doc_id}")
            rec("documents download", "GET", f"/api/v2/documents/download/{doc_id}", r.status_code, [200], r.text[:300])

            r = client.put(
                f"/api/v2/documents/{doc_id}",
                params={"doc_type": "план"},
                files={"file": ("doc2.pdf", b"%PDF-1.4 fake2", "application/pdf")},
                headers=headers_manager,
            )
            rec("documents update", "PUT", f"/api/v2/documents/{doc_id}", r.status_code, [200], r.text[:300])

    contract_id = None
    if property_id:
        r = client.post(f"/api/v2/contracts/generate/{property_id}", headers=headers_user)
        rec("contracts generate", "POST", f"/api/v2/contracts/generate/{property_id}", r.status_code, [201], r.text[:300])
        contract_id = r.json().get("id") if r.status_code == 201 else None

        r = client.get("/api/v2/contracts", headers=headers_user)
        rec("contracts mine", "GET", "/api/v2/contracts", r.status_code, [200], r.text[:300])

        r = client.get("/api/v2/contracts/all", headers=headers_manager)
        rec("contracts all", "GET", "/api/v2/contracts/all", r.status_code, [200], r.text[:300])

        if contract_id:
            r = client.get(f"/api/v2/contracts/{contract_id}", headers=headers_user)
            rec("contracts get", "GET", f"/api/v2/contracts/{contract_id}", r.status_code, [200], r.text[:300])

            r = client.get(f"/api/v2/contracts/{contract_id}/download", headers=headers_user)
            rec("contracts download", "GET", f"/api/v2/contracts/{contract_id}/download", r.status_code, [200], r.text[:300])

            r = client.patch(f"/api/v2/contracts/{contract_id}", json={"status": "подписан"}, headers=headers_manager)
            rec("contracts patch", "PATCH", f"/api/v2/contracts/{contract_id}", r.status_code, [200], r.text[:300])

            with Session(engine) as s:
                admin_u = s.exec(select(User).where(User.email == "admin_test@example.com")).first()
                manager_u = s.exec(select(User).where(User.email == "manager_test@example.com")).first()

            r = client.put(
                f"/api/v2/contracts/{contract_id}",
                json={
                    "realEstateObjectId": property_id,
                    "userId": admin_u.id,
                    "managerId": manager_u.id,
                    "contractDate": "2026-04-25",
                    "status": "подписан",
                },
                headers=headers_manager,
            )
            rec("contracts put", "PUT", f"/api/v2/contracts/{contract_id}", r.status_code, [200], r.text[:300])

    with Session(engine) as s:
        target_user = s.exec(select(User).where(User.email == "new_user_test@example.com")).first()
    if target_user:
        r = client.patch(
            f"/api/v2/auth/users/{target_user.id}/role",
            params={"role_name": "manager"},
            headers=headers_admin,
        )
        rec("auth assign role", "PATCH", f"/api/v2/auth/users/{target_user.id}/role", r.status_code, [200], r.text[:300])

    if property_id:
        with Session(engine) as s:
            doc = s.exec(select(Document).where(Document.real_estate_object_id == property_id)).first()
            photo = s.exec(select(Photo).where(Photo.real_estate_object_id == property_id)).first()
            contract = s.exec(select(Contract).where(Contract.real_estate_object_id == property_id)).first()

        if doc:
            r = client.delete(f"/api/v2/documents/{doc.id}", headers=headers_manager)
            rec("documents delete", "DELETE", f"/api/v2/documents/{doc.id}", r.status_code, [204], r.text[:300])

        if photo:
            r = client.delete(f"/api/v2/photos/{photo.id}", headers=headers_manager)
            rec("photos delete", "DELETE", f"/api/v2/photos/{photo.id}", r.status_code, [204], r.text[:300])

        if contract:
            r = client.delete(f"/api/v2/contracts/{contract.id}", headers=headers_manager)
            rec("contracts delete", "DELETE", f"/api/v2/contracts/{contract.id}", r.status_code, [204], r.text[:300])

        r = client.delete(f"/api/v2/properties/{property_id}", headers=headers_manager)
        rec("properties delete", "DELETE", f"/api/v2/properties/{property_id}", r.status_code, [204], r.text[:300])

    if created_type_id:
        r = client.delete(f"/api/v2/property-types/{created_type_id}", headers=headers_manager)
        rec("property-types delete", "DELETE", f"/api/v2/property-types/{created_type_id}", r.status_code, [204], r.text[:300])

    if target_user:
        r = client.delete(f"/api/v2/auth/users/{target_user.id}", headers=headers_admin)
        rec("auth delete user", "DELETE", f"/api/v2/auth/users/{target_user.id}", r.status_code, [204], r.text[:300])

    summary = {
        "total": len(results),
        "passed": sum(1 for x in results if x["ok"]),
        "failed": sum(1 for x in results if not x["ok"]),
        "failures": [x for x in results if not x["ok"]],
    }
    report_path = Path("tmp_api_test_report.json")
    report_path.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"REPORT_SAVED:{report_path}")
    print(f"TOTAL={summary['total']} PASSED={summary['passed']} FAILED={summary['failed']}")


if __name__ == "__main__":
    main()
