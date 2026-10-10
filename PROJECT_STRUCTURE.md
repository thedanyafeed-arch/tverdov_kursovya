# Структура проекта «АРМ застройщика»

Клиент-серверная система: **FastAPI** (бизнес-логика, REST API, PostgreSQL) + **Django** (HTML-интерфейс, HTTP-клиент к API v2) + автотесты **pytest** (API + Selenium E2E).

```
tverdov_kursovya/
│
├── app/                          # FastAPI-бэкенд
│   ├── api/
│   │   ├── v1/                   # Маршруты API v1 (пути без префикса: /auth, /properties, …)
│   │   │   ├── auth_router.py
│   │   │   ├── property_router.py
│   │   │   ├── property_type_router.py
│   │   │   ├── photo_router.py
│   │   │   ├── document_router.py
│   │   │   └── contract_router.py
│   │   └── v2/                   # Маршруты API v2 (префикс /api/v2)
│   │       ├── auth_router.py
│   │       ├── property_router.py
│   │       ├── property_type_router.py
│   │       ├── photo_router.py
│   │       ├── document_router.py
│   │       └── contract_router.py
│   ├── controllers/              # Бизнес-логика (общая для v1 и v2)
│   │   ├── auth_controller.py
│   │   ├── property_controller.py
│   │   ├── photo_controller.py
│   │   ├── document_controller.py
│   │   └── contract_controller.py
│   ├── models/                   # SQLModel / ORM
│   │   ├── base.py               # CamelModel (camelCase в JSON)
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── property_type.py
│   │   ├── real_estate_object.py
│   │   ├── photo.py
│   │   ├── document.py
│   │   └── contract.py
│   ├── schemas/                  # Pydantic-схемы запросов/ответов
│   │   ├── user_schema.py
│   │   ├── property_schema.py
│   │   ├── property_type_schema.py
│   │   ├── photo_schema.py
│   │   ├── document_schema.py
│   │   └── contract_schema.py
│   ├── core/
│   │   ├── config.py             # Настройки из .env
│   │   ├── security.py           # JWT, Argon2, зависимости ролей
│   │   ├── swagger_ui.py         # Offline Swagger: /api/v1/docs, /api/v2/docs
│   │   └── utils.py
│   ├── db/
│   │   ├── database.py           # Engine, init_db, начальные роли/типы
│   │   └── session.py            # get_session()
│   ├── main.py                   # Точка входа FastAPI, роутеры, /uploads
│   └── get_password_hash.py      # Утилита хеширования пароля
│
├── web_client_django/            # Django web-клиент (только UI + HTTP к API)
│   ├── real_estate_web/          # Настройки проекта Django
│   │   ├── settings.py           # API_BASE_URL → http://127.0.0.1:8000/api/v2
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── app/
│   │   ├── views.py              # Страницы: каталог, login, admin_panel, manager, account
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── services/
│   │   │   └── api_client.py     # HTTP-клиент ко всем эндпоинтам v2
│   │   ├── utils.py              # JWT из session, декораторы require_admin/…
│   │   ├── media_urls.py         # URL загрузок FastAPI (/uploads)
│   │   ├── property_labels.py
│   │   ├── contract_choices.py
│   │   ├── context_processors.py
│   │   ├── templatetags/
│   │   └── controlers/           # Вспомогательные обёртки (историческое имя папки)
│   ├── templates/                # HTML (Bootstrap)
│   │   ├── catalog/
│   │   ├── registration/
│   │   ├── admin_panel/
│   │   ├── manager/
│   │   ├── account/
│   │   └── partials/
│   ├── static/                   # CSS, JS
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── tests/                        # Автотесты (корень репозитория)
│   ├── conftest.py               # Общие настройки pytest
│   ├── api/                      # 86 интеграционных тестов FastAPI (httpx)
│   │   ├── conftest.py           # API_V1_PREFIX="", API_V2_PREFIX="/api/v2"
│   │   ├── helpers.py
│   │   ├── test_auth.py
│   │   ├── test_auth_extra.py
│   │   ├── test_properties.py
│   │   ├── test_property_types.py
│   │   ├── test_property_types_v2.py
│   │   ├── test_photos.py
│   │   ├── test_documents.py
│   │   └── test_contracts.py
│   └── e2e/                      # 25 UI-тестов Selenium (Django :8001)
│       ├── conftest.py
│       ├── pages/                # Page Object Model
│       └── test_*.py
│
├── uploads/                      # Файлы: photos/, documents/, contracts/
├── dist/                         # Статика offline Swagger UI
├── scripts/                      # Вспомогательные скрипты
├── pdf документы/                # ПЗ, PlantUML, примеры
│
├── API_ENDPOINTS_DOCUMENTATION.txt
├── PROJECT_STRUCTURE.md          # Этот файл
├── ARCHITECTURE.md
├── UML_DOCUMENTATION.md
├── uml_class_diagram.puml
├── pytest.ini
├── requirements.txt              # Зависимости FastAPI
├── requirements-dev.txt          # pytest, httpx, selenium, …
└── insert_properties.sql           # Пример SQL-данных
```

## Запуск

| Компонент | Команда | URL |
|-----------|---------|-----|
| FastAPI | `uvicorn app.main:app_v1 --reload --port 8000` | http://127.0.0.1:8000 |
| Swagger v1 / v2 | — | /api/v1/docs , /api/v2/docs |
| Django | `cd web_client_django && python manage.py runserver 8001` | http://127.0.0.1:8001 |

Перед запуском: PostgreSQL, файл `app/.env` (DATABASE_URL, SECRET_KEY), для Django — `web_client_django/.env` с `API_BASE_URL=http://127.0.0.1:8000/api/v2`.

## Тесты

```bash
pytest tests/api
pytest tests/e2e -m e2e    # нужны запущенные FastAPI :8000 и Django :8001
```

## Версии API

| Версия | Префикс путей | Использование |
|--------|---------------|---------------|
| v1 | нет (`/properties`, `/auth/…`) | Базовая реализация, тесты v1 |
| v2 | `/api/v2` | Django-клиент, улучшенная валидация и коды ответов |

Подробное описание эндпоинтов: `API_ENDPOINTS_DOCUMENTATION.txt` (Часть 1 — полный v1, Часть 2 — только отличия v2).

## Основные компоненты FastAPI

### Роутеры (`app/api/v1/`, `app/api/v2/`)
Тонкий слой: приём HTTP, зависимости `get_session`, `get_current_user`, `admin_required`, `manager_required`, вызов контроллеров.

### Контроллеры (`app/controllers/`)
Правила предметной области: проверка ролей, работа с файлами в `uploads/`, генерация договоров **python-docx**, CRUD через SQLModel.

### Модели (`app/models/`)
Таблицы PostgreSQL: `role`, `user`, `propertytype`, `realestateobject`, `photo`, `document`, `contract`.

### Безопасность (`app/core/security.py`)
- Хеширование паролей: **Argon2** (passlib)
- JWT в заголовке `Authorization: Bearer`
- Зависимости: `get_current_user`, `admin_required`, `manager_required`

### `app/main.py`
- Подключение роутеров v1 и v2 (`include_router(..., prefix="/api/v2")` для v2)
- Пагинация: `fastapi-pagination`
- Раздача `/uploads` и `/dist`
- Отдельные OpenAPI-схемы для v1 и v2

## Django web-клиент

Django **не дублирует** доменные данные в своей БД: все операции через `app/services/api_client.py` к **API v2**.

Основные URL интерфейса:
- `/`, `/catalog/`, `/properties/<id>/` — каталог
- `/login/`, `/register/`, `/logout/`
- `/admin_panel/...` — CRUD объектов, типы, пользователи, медиа
- `/manager/...` — статусы, договоры
- `/account/...` — профиль, договоры пользователя

Сессия Django хранит `access_token` и `role_name` после входа.
