# API v2: изменения относительно v1

Этот файл фиксирует, что было добавлено/изменено в `v2` по сравнению с `v1`.

## 1) Версионирование и документация

- Добавлены новые роутеры в `app/api/v2`.
- `v1` и `v2` теперь имеют раздельные Swagger страницы:
  - `GET /api/v1/docs`
  - `GET /api/v2/docs`
- Разделены OpenAPI схемы:
  - `GET /api/v1/openapi.json` содержит только `v1` пути.
  - `GET /api/v2/openapi.json` содержит только `v2` пути.
- В Swagger для OAuth2 поля авторизации визуально переименованы с `username` на `Email`.

## 2) Роутеры v2

Добавлены:

- `app/api/v2/auth_router.py`
- `app/api/v2/property_router.py`
- `app/api/v2/photo_router.py`
- `app/api/v2/document_router.py`
- `app/api/v2/contract_router.py`
- `app/api/v2/property_type_router.py`

Подключение выполнено в `app/main.py` под префиксом `/api/v2`.

## 3) Аутентификация и Swagger Authorize

- Логин в `v1` и `v2` переведен на `OAuth2PasswordRequestForm`.
- Для Swagger включен `oauth2 password flow`:
  - `v1 tokenUrl`: `/auth/login`
  - `v2 tokenUrl`: `/api/v2/auth/login`
- После авторизации в Swagger токен автоматически используется в защищенных запросах.

## 4) Изменения в контрактах v2

### Auth

- `GET /api/v2/auth/me` использует безопасный response DTO `UserPublic` (без `hashed_password`).
- `POST /api/v2/auth/register` возвращает `201 Created`.
- `PATCH /api/v2/auth/users/{user_id}/role` валидирует роль по pattern.
- `DELETE /api/v2/auth/users/{user_id}` возвращает корректный пустой `204`.

### Properties

- Добавлена валидация диапазонов:
  - `min_price <= max_price`
  - `min_area <= max_area`
- Добавлена валидация `status_filter`.
- `POST /api/v2/properties/{property_id}/reserve`:
  - возвращает `409`, если объект уже продан;
  - возвращает `409`, если объект уже забронирован.
- `DELETE /api/v2/properties/{property_id}` возвращает пустой `204`.

### Property types

- Добавлены отдельные схемы:
  - `PropertyTypeCreate`
  - `PropertyTypeUpdate`
- `POST /api/v2/property-types` возвращает `409` при дубликате.
- `PUT /api/v2/property-types/{type_id}`:
  - `404`, если тип не найден;
  - `409`, если новое имя уже занято.
- `DELETE /api/v2/property-types/{type_id}`:
  - `404`, если тип не найден;
  - пустой `204` при успешном удалении.

### Photos / Documents / Contracts

- Для upload операций выставлен `201 Created` там, где создается ресурс.
- Для delete операций выставлен корректный пустой `204`.
- Выравнены summary/description и response-контракты для `v2`.

## 5) Новые схемы

- Добавлен файл `app/schemas/property_type_schema.py`.
- В `app/schemas/user_schema.py` добавлена схема `UserPublic`.

## 6) Что осталось без изменений

- Роутеры и поведение `v1` сохранены (обратная совместимость).
- Бизнес-логика контроллеров в основном общая между `v1` и `v2`; ключевые улучшения внедрены на уровне API-контрактов и валидации.
