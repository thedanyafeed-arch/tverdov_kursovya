from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.db.database import init_db, close_db
from app.api.v1.auth_router import router as auth_router
from app.api.v1.property_router import router as property_router
from app.api.v1.photo_router import router as photo_router
from app.api.v1.document_router import router as document_router
from app.api.v1.contract_router import router as contract_router
from app.api.v1.property_type_router import router as property_type_router
from app.api.v2.auth_router import router as auth_router_v2
from app.api.v2.property_router import router as property_router_v2
from app.api.v2.photo_router import router as photo_router_v2
from app.api.v2.document_router import router as document_router_v2
from app.api.v2.contract_router import router as contract_router_v2
from app.api.v2.property_type_router import router as property_type_router_v2
from fastapi_pagination import add_pagination
from app.core.swagger_ui import setup_custom_docs
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
@asynccontextmanager
async def on_startup(app: FastAPI):
    """Инициализация и завершение работы приложения"""
    init_db()
    yield
    close_db()

# Создаём основное приложение с отключённой встроенной документацией
app_v1 = FastAPI(
    title="АРМ застройщика API",
    description="REST API для автоматизированного рабочего места застройщика. Позволяет управлять объектами недвижимости, документацией, фото и генерировать договоры.",
    version="1.0.0",
    contact={
        "name": "Твердов Даниил Сергеевич",
        "email": "tverdov.ds@example.com"
    },
    docs_url=None,          # Отключаем стандартный Swagger
    redoc_url=None,         # Отключаем ReDoc
    openapi_url="/api/v1/openapi.json",  # Путь к OpenAPI-схеме
    lifespan=on_startup
)




# Подключаем кастомную (offline) документацию
setup_custom_docs(app_v1)







# Подключаем все роутеры из v1
app_v1.include_router(auth_router)
app_v1.include_router(property_router)
app_v1.include_router(photo_router)
app_v1.include_router(document_router)
app_v1.include_router(contract_router)
app_v1.include_router(property_type_router)
app_v1.include_router(auth_router_v2, prefix="/api/v2")
app_v1.include_router(property_router_v2, prefix="/api/v2")
app_v1.include_router(photo_router_v2, prefix="/api/v2")
app_v1.include_router(document_router_v2, prefix="/api/v2")
app_v1.include_router(contract_router_v2, prefix="/api/v2")
app_v1.include_router(property_type_router_v2, prefix="/api/v2")

# Включаем поддержку пагинации
add_pagination(app_v1)

# Раздача статических файлов:
# - /uploads → фото, документы, договоры
# - /dist   → offline Swagger UI
def custom_openapi():
    return custom_openapi_v1()


def _apply_bearer_security(
    openapi_schema: dict,
    public_operations: set[tuple[str, str]],
    token_url: str,
) -> dict:
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": token_url,
                    "scopes": {},
                }
            },
        }
    }

    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if isinstance(operation, dict) and method in {"get", "post", "put", "patch", "delete"}:
                if (path, method) in public_operations:
                    continue
                operation["security"] = [{"BearerAuth": []}]
    return openapi_schema


def _build_openapi(
    filtered_paths: dict[str, dict],
    title: str,
    version: str,
    public_operations: set[tuple[str, str]],
    token_url: str,
) -> dict:
    openapi_schema = get_openapi(
        title=title,
        version=version,
        routes=app_v1.routes,
        description=app_v1.description,
        contact=app_v1.contact,
    )
    openapi_schema["paths"] = filtered_paths
    return _apply_bearer_security(openapi_schema, public_operations, token_url)


openapi_v1_schema: dict | None = None
openapi_v2_schema: dict | None = None


def custom_openapi_v1():
    global openapi_v1_schema
    if openapi_v1_schema:
        return openapi_v1_schema

    base_schema = get_openapi(
        title=app_v1.title,
        version=app_v1.version,
        routes=app_v1.routes,
        description=app_v1.description,
        contact=app_v1.contact,
    )
    filtered_paths = {
        path: item
        for path, item in base_schema.get("paths", {}).items()
        if not path.startswith("/api/v2/")
    }
    public_operations_v1 = {
        ("/auth/login", "post"),
        ("/auth/register", "post"),
        ("/auth/logout", "post"),
        ("/properties", "get"),
        ("/properties/{property_id}", "get"),
        ("/documents/{property_id}", "get"),
        ("/photos", "get"),
        ("/photos/{property_id}", "get"),
        ("/property-types", "get"),
    }
    openapi_v1_schema = _build_openapi(
        filtered_paths,
        f"{app_v1.title} v1",
        app_v1.version,
        public_operations_v1,
        "/auth/login",
    )
    return openapi_v1_schema


def custom_openapi_v2():
    global openapi_v2_schema
    if openapi_v2_schema:
        return openapi_v2_schema

    base_schema = get_openapi(
        title=app_v1.title,
        version=app_v1.version,
        routes=app_v1.routes,
        description=app_v1.description,
        contact=app_v1.contact,
    )
    filtered_paths = {
        path: item
        for path, item in base_schema.get("paths", {}).items()
        if path.startswith("/api/v2/")
    }
    public_operations_v2 = {
        ("/api/v2/auth/login", "post"),
        ("/api/v2/auth/register", "post"),
        ("/api/v2/auth/logout", "post"),
        ("/api/v2/properties", "get"),
        ("/api/v2/properties/{property_id}", "get"),
        ("/api/v2/documents/{property_id}", "get"),
        ("/api/v2/photos", "get"),
        ("/api/v2/photos/{property_id}", "get"),
        ("/api/v2/property-types", "get"),
    }
    openapi_v2_schema = _build_openapi(
        filtered_paths,
        f"{app_v1.title} v2",
        app_v1.version,
        public_operations_v2,
        "/api/v2/auth/login",
    )
    return openapi_v2_schema


@app_v1.get("/api/v2/openapi.json", include_in_schema=False)
def get_openapi_v2():
    return JSONResponse(custom_openapi_v2())

app_v1.openapi = custom_openapi
app_v1.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app_v1.mount("/dist", StaticFiles(directory="dist"), name="dist")