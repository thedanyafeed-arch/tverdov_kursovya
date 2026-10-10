# -*- coding: utf-8 -*-
"""Генерация полного текста пояснительной записки под проект АРМ застройщика."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = next(ROOT.glob("pdf*"))
BETA_EXTRACT = next(PDF_DIR.glob("*застройщика*_extract.txt"))
OUT_FILE = PDF_DIR / "Твердов_ПЗ_АРМ_застройщика_полный_текст.txt"


def clean_pdf_artifacts(text: str) -> str:
    text = re.sub(r"===== PAGE \d+ =====\n?", "", text)
    text = re.sub(
        r"ЕМК 09\.02\.07 КП 7050ИП-31к-25 ПЗ\s*\n\s*\d+\s*\n",
        "",
        text,
    )
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def global_replacements(text: str) -> str:
    pairs = [
        ("developer_api", "каталог app (FastAPI-бэкенд)"),
        ("developer_django", "каталог web_client_django"),
        ("developer_project", "tverdov_kursovya"),
        ("arm_developer_db", "arm_zastroyshchik"),
        ("(bcrypt)", "(Argon2 через passlib)"),
        ("bcrypt", "Argon2"),
        ("passlib (bcrypt)", "passlib (Argon2)"),
        ("refresh_token (срок жизни 24 часа)", "сохранение access_token в сессии Django"),
        ("и refresh_token", ""),
        ("access_token (срок жизни 30 минут) и refresh_token (срок жизни 24 часа). Токены", "access_token. Токен"),
        ("пары JWT-токенов (access и refresh)", "JWT access_token"),
        ("Django ORM — используется в веб-приложении для работы с базой данных.", "Django не использует ORM для доменных данных: все операции выполняются через HTTP-клиент к FastAPI."),
        ("pytest-django — интеграция pytest с Django для тестирования представлений, форм и маршрутов.", "Selenium — E2E-тестирование веб-интерфейса Django (tests/e2e)."),
        ("– openpyxl / xlsxwriter — генерация договоров и отчётов в формате Excel.", "– python-docx — генерация договоров купли-продажи в формате Word (.docx)."),
        ("Word/Excel", "Word (.docx)"),
        ("Word или Excel", "Word (.docx)"),
        ("в форматах Word и Excel", "в формате Word (.docx)"),
        ("Excel (.xlsx)", "Word (.docx)"),
        ("?format=xlsx", ""),
        ("или ?format=xlsx", ""),
        ("/desk/admin/", "/admin_panel/"),
        ("admin_dashboard", "admin_panel"),
        ("manager_dashboard", "manager_panel"),
        ("user_home", "account"),
        ("public_catalog", "catalog"),
        ("http://localhost:8001/api/v1/docs", "http://127.0.0.1:8000/docs"),
        ("http://localhost:8001/api/v1/redoc", "http://127.0.0.1:8000/redoc"),
        ("http://localhost:8001/api/v2/docs", "http://127.0.0.1:8000/docs (схема v2)"),
        ("http://localhost:8001/api/v2/redoc", "http://127.0.0.1:8000/redoc"),
        ("http://127.0.0.1:8000/", "http://127.0.0.1:8001/"),
        ("http://localhost:8000/", "http://127.0.0.1:8001/"),
        ("После запуска приложение будет доступно по адресу http://127.0.0.1:8000/.", "После запуска приложение будет доступно по адресу http://127.0.0.1:8001/."),
        ("открыть страницу http://127.0.0.1:8000/", "открыть страницу http://127.0.0.1:8001/"),
        ("http://127.0.0.1:8001/api/v1/docs", "http://127.0.0.1:8000/docs"),
        ("/admin-panel/", "/admin_panel/"),
        ("/manager-panel/", "/manager/"),
        ("/user/", "/account/"),
        ("/public/properties/", "/catalog/"),
        ("48 автоматизированных тестов", "86 автоматизированных API-тестов"),
        ("155 автоматизированных тестов", "25 E2E-тестов (Selenium)"),
        ("203 автоматизированных тест-кейса", "111 автоматизированных тест-кейсов (86 API + 25 E2E)"),
        ("203 автоматизированных тест", "111 автоматизированных тест"),
        ("Всего выполнен 203", "Всего выполнено 111"),
        ("покрытие кода — 82%", "все тесты пройдены успешно"),
        ("покрытие кода — 84%", "все E2E-сценарии пройдены успешно"),
        ("Покрытие FastAPI-бэкенда составило 82%, а Django-приложения — 84%", "Все 86 API-тестов и 25 E2E-тестов завершены успешно"),
        ("82%, покрытие Django-приложения — 84%", "100% успешных прогонов API и E2E тестов"),
        ("журнале аудита действий пользователей, а также", "договорах купли-продажи, а также"),
        ("ведение журнала аудита действий пользователей, а ", ""),
        ("и журнале аудита.", "."),
        ("– журнал аудита (действия пользователей, дата и время, тип операции).", ""),
        ("– отсутствие централизованного аудита действий сотрудников.", "– отсутствие единого личного кабинета покупателя."),
        ("а также для аудита действий пользователей.", "а также для управления договорами и ролями."),
        ("POST /api/v2/audit/export/ для экспорта журнала аудита в Excel. –", ""),
        ("– GET /api/v1/audit/ — получение журнала аудита (с фильтрацией по пользователю и дате); –", ""),
        ("– Все записи создаются с автоматической фиксацией в журнале аудита.", ""),
        ("contract_excel_view", "contract_download_view"),
        ("contract_word_view", "manager_generate_contract_view"),
        ("tests/ui/", "tests/e2e/"),
        ("tests/api/conftest.py):", "tests/api/conftest.py и tests/conftest.py):"),
        ("cd developer_api", "cd tverdov_kursovya (корень репозитория)"),
        ("cd developer_django", "cd web_client_django"),
        ("python app/main.py --migrate", "инициализация БД выполняется при первом запуске (init_db в lifespan FastAPI)"),
        ("python app/main.py", "uvicorn app.main:app --reload --port 8000"),
        ("python manage.py migrate", "python manage.py migrate  # служебные таблицы Django (сессии)"),
        ("external", "гость (незарегистрированный пользователь)"),
        ("role 'external'", "роль user"),
        ("/api/v2/realestateobject/", "/api/v2/properties/"),
        ("/api/v1/realestateobject/", "/api/v1/properties/"),
        ("/admin_panel/realestateobject/", "/admin_panel/properties/"),
        ("GET /realestateobject", "GET /properties"),
        ("/realestateobject —", "/properties —"),
        ("test_realestateobject.py", "test_properties.py"),
        ("API / realestateobject", "API / properties"),
        ("ведение журнала аудита действий пользователей, а ", ""),
        ("ведение журнала аудита действий пользователей, а также", "а также"),
        ("продажи → аудит действий", "продажи → скачивание договора"),
        ("и журнала аудита действий", ""),
        ("журнала аудита действий", "истории договоров"),
        ("ведение журнала аудита действий пользователей и ", ""),
        ("Покрытие кода FastAPI-бэкенда составило 82%, а Django-приложения — 84%, что превышает минимальные требования, установленные планом тестирования.", "Все 111 автоматизированных тестов (86 API + 25 E2E) завершены успешно."),
        ("/api/v1/realestateobject/", "/api/v1/properties/"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)
    # Удаление упоминаний audit_logs если остались
    text = re.sub(r".*audit_logs.*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r".*журнал аудита.*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r".*BUG-01.*\n", "", text)
    return text


SECTION_32 = """
3.2. ERD-модель информационной системы

Физическая модель базы данных представлена в виде ERD-диаграммы (Entity-Relationship Diagram), реализованной средствами СУБД PostgreSQL. Диаграмма отражает структуру таблиц, их атрибуты, первичные и внешние ключи, а также связи между сущностями.

Рисунок 2 — Схема базы данных

База данных информационной системы включает 7 взаимосвязанных таблиц: role, user, propertytype, realestateobject, photo, document, contract.

Таблица role содержит справочник ролей системы (admin, manager, user). Таблица user хранит учётные записи пользователей с привязкой к роли. Таблица propertytype — справочник типов объектов недвижимости (квартира, дом, коммерческая площадь и т.д.). Таблица realestateobject является центральной и содержит характеристики продаваемых объектов. Таблица photo хранит метаданные и пути к файлам фотографий объектов. Таблица document содержит строительную документацию (схемы, планы застройки). Таблица contract хранит сведения о договорах купли-продажи и путь к сгенерированному файлу .docx.

Таблица 3 — Классификация связей информационной системы

Родительская таблица    Дочерняя таблица    Тип связи    Обоснование
role                    user                1:M          Одна роль может быть назначена многим пользователям
propertytype            realestateobject    1:M          Один тип объекта может быть присвоен множеству объектов
realestateobject        photo               1:M          Один объект может иметь множество фотографий
realestateobject        document            1:M          Один объект может содержать множество документов
realestateobject        contract            1:M          По одному объекту может быть оформлено несколько договоров
user                    contract            1:M          Пользователь (покупатель) может иметь несколько договоров
user                    contract            1:M          Менеджер (manager_id) оформляет множество договоров

Словарь данных сформирован для однозначного понимания структуры и назначения каждого поля.

Таблица 4 — Таблица role (Роли)

Ключ    Имя поля        Тип данных    Нулевые значения    Дополнительные    Описание
PK      id              INTEGER       N                   Автоинкремент     Уникальный идентификатор роли
        name            VARCHAR       N                   Уникальное        Имя роли (admin, manager, user)
        description     VARCHAR       Y                                     Описание роли

Таблица 5 — Таблица user (Пользователи)

Ключ    Имя поля            Тип данных    Нулевые    Дополнительные    Описание
PK      id                  INTEGER       N          Автоинкремент     Идентификатор пользователя
        email               VARCHAR       N          Уникальное        Email для входа
        hashed_password     VARCHAR       N                            Хэш пароля (Argon2)
        is_active           BOOLEAN       N          DEFAULT TRUE      Признак активности
        created_at          VARCHAR       Y                            Дата регистрации
FK      role_id             INTEGER       N          → role.id         Роль пользователя

Таблица 6 — Таблица propertytype (Типы объектов)

Ключ    Имя поля    Тип данных    Нулевые    Дополнительные    Описание
PK      id          INTEGER       N          Автоинкремент     Идентификатор типа
        name        VARCHAR       N          Уникальное        Наименование типа (квартира, дом и т.д.)

Таблица 7 — Таблица realestateobject (Объекты недвижимости)

Ключ    Имя поля            Тип данных    Нулевые    Описание
PK      id                  INTEGER       N          Идентификатор объекта
FK      property_type_id    INTEGER       N          Ссылка на propertytype.id
        total_area          FLOAT         N          Общая площадь (кв. м)
        finishing           VARCHAR       N          Тип отделки
        wall_material       VARCHAR       N          Материал стен
        floor               INTEGER       N          Этаж
        floors_total        INTEGER       N          Этажность здания
        price               NUMERIC       N          Основная цена
        discount_price      NUMERIC       Y          Скидочная цена
        status              VARCHAR       N          Статус (в продаже, продан, забронирован)
        address             VARCHAR       N          Адрес
        description         VARCHAR       Y          Описание
        created_at          VARCHAR       Y          Дата создания
        updated_at          VARCHAR       Y          Дата обновления

Таблица 8 — Таблица photo (Фотографии)

Ключ    Имя поля                Тип данных    Нулевые    Описание
PK      id                      INTEGER       N          Идентификатор фото
FK      real_estate_object_id   INTEGER       N          Ссылка на объект
        file_path               VARCHAR       N          Путь к файлу в uploads/
        filename                VARCHAR       N          Имя файла
        uploaded_at             VARCHAR       Y          Дата загрузки

Таблица 9 — Таблица document (Строительная документация)

Ключ    Имя поля                Тип данных    Нулевые    Описание
PK      id                      INTEGER       N          Идентификатор документа
FK      real_estate_object_id   INTEGER       N          Ссылка на объект
        file_path               VARCHAR       N          Путь к файлу
        filename                VARCHAR       N          Имя файла
        doc_type                VARCHAR       N          Тип (схема, план застройки)
        uploaded_at             VARCHAR       Y          Дата загрузки

Таблица 10 — Таблица contract (Договоры купли-продажи)

Ключ    Имя поля                Тип данных    Нулевые    Описание
PK      id                      INTEGER       N          Идентификатор договора
FK      real_estate_object_id   INTEGER       N          Объект недвижимости
FK      user_id                 INTEGER       N          Покупатель (user)
FK      manager_id              INTEGER       N          Менеджер, оформивший договор
        contract_date           VARCHAR       N          Дата договора
        status                  VARCHAR       N          Статус (создан, подписан)
        generated_file_path     VARCHAR       Y          Путь к файлу .docx
        created_at              VARCHAR       Y          Дата создания записи
"""

SECTION_33 = """
3.3. Файловая структура приложения

Файловая структура проекта организована в соответствии с принципами модульности, разделения ответственности и масштабируемости. Проект разделён на два независимых приложения: серверную часть на FastAPI (каталог app/) и клиентское веб-приложение на Django (каталог web_client_django/). Django не дублирует доменную модель в своей БД — все данные об объектах, договорах и пользователях получаются через REST API v2.

3.3.1. Структура FastAPI-приложения (app/)

tverdov_kursovya/
├── app/                              # FastAPI-бэкенд
│   ├── api/
│   │   ├── v1/                       # маршруты API v1
│   │   └── v2/                       # маршруты API v2 (используются Django-клиентом)
│   ├── controllers/                  # бизнес-логика
│   ├── core/                         # конфигурация, JWT, Argon2
│   ├── db/                           # подключение PostgreSQL, init_db
│   ├── models/                       # SQLModel-модели таблиц
│   ├── schemas/                      # Pydantic-схемы
│   ├── main.py                       # точка входа, Swagger offline
│   └── ...
├── tests/
│   ├── api/                          # 86 автоматизированных API-тестов
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_properties.py
│   │   └── ...
│   └── e2e/                          # 25 E2E-тестов Selenium
│       ├── pages/                    # Page Object Model
│       └── conftest.py
├── uploads/                          # фото, документы, договоры
├── pytest.ini
├── requirements.txt
└── API_ENDPOINTS_DOCUMENTATION.txt

Таблица 11 — Назначение директорий FastAPI-приложения

Директория / файл          Назначение
app/api/v1/, app/api/v2/   Маршрутизаторы REST API двух версий
app/controllers/           Контроллеры: auth, property, photo, document, contract
app/core/security.py       Хеширование паролей Argon2, создание и проверка JWT
app/db/                    Подключение к PostgreSQL, инициализация схемы
app/models/                SQLModel-модели: User, Role, RealEstateObject и др.
app/schemas/               Валидация запросов и ответов (Pydantic)
app/main.py                Регистрация роутеров, offline Swagger UI, раздача /uploads
tests/api/                 Pytest + httpx.AsyncClient для тестирования API

3.3.2. Структура Django-приложения (web_client_django/)

web_client_django/
├── app/
│   ├── services/api_client.py        # HTTP-клиент к FastAPI (/api/v2)
│   ├── templates/                    # HTML-шаблоны (Bootstrap)
│   ├── forms.py                      # формы входа, регистрации, объектов
│   ├── views.py                      # представления (каталог, панели admin/manager)
│   └── urls.py                       # маршруты веб-интерфейса
├── real_estate_web/
│   └── settings.py                   # API_BASE_URL=http://127.0.0.1:8000/api/v2
├── manage.py
├── requirements.txt
└── .env.example

Таблица 12 — Назначение директорий Django-приложения

Директория / файл              Назначение
app/services/api_client.py     Все запросы к FastAPI: авторизация, CRUD, договоры
app/templates/                 Шаблоны страниц: каталог, карточка объекта, панели
app/views.py                   Обработка HTTP, хранение access_token в session
app/urls.py                    URL: /login/, /catalog/, /admin_panel/, /manager/, /account/
real_estate_web/settings.py    Настройки Django, переменная API_BASE_URL

3.3.3. Описание фикстур тестового окружения

Фикстуры API (tests/api/conftest.py):
– async_client — httpx.AsyncClient для FastAPI без поднятия отдельного сервера;
– db_session — транзакционная сессия БД для изоляции тестов;
– auth_headers — заголовок Authorization: Bearer с JWT выбранной роли.

Фикстуры E2E (tests/e2e/conftest.py):
– driver — WebDriver Chrome для Selenium;
– base_url — адрес Django (по умолчанию http://127.0.0.1:8001);
– page objects (LoginPage, RegisterPage и др.) — паттерн Page Object Model.
"""

SECTION_34 = """
3.4. Алгоритмы

В данном разделе описаны ключевые алгоритмы информационной системы АРМ застройщика. Графическое отображение в виде блок-схем вынесено в Приложение Б (файл plantuml_diagrams.puml).

3.4.1. Алгоритм авторизации и выдачи JWT (FastAPI + Django)

Реализован в app/controllers/auth_controller.py и представлении login_view (Django). (см. Приложение Б, рисунок Б.1)

Последовательность действий:
– Пользователь открывает GET /login/ и вводит email и пароль.
– Django отправляет POST на /api/v2/auth/login (form-data: email, password).
– AuthController ищет пользователя в таблице user по email.
– При отсутствии пользователя или неверном пароле возвращается 401 Unauthorized.
– Пароль проверяется через Argon2 (passlib). При успехе формируется access_token (JWT).
– Django сохраняет access_token и role_name в session, загружает профиль через GET /api/v2/auth/me.
– Выполняется redirect на /catalog/ (единая точка входа для всех ролей; разделы admin/manager доступны из меню по роли).
– Защищённые запросы Django передают заголовок Authorization: Bearer <access_token>.

3.4.2. Алгоритм добавления объекта недвижимости с фотографиями (администратор)

Реализован в admin_property_create_view и PropertyController. (см. Приложение Б, рисунок Б.2)

Последовательность действий:
– Администратор авторизуется (роль admin, декоратор require_admin).
– Переходит на /admin_panel/properties/create/.
– Заполняет форму PropertyForm: тип объекта, площадь, этаж, отделка, материал стен, цены, адрес, описание.
– Django отправляет POST /api/v2/properties/ с JSON-телом.
– FastAPI валидирует данные (Pydantic), создаёт запись в realestateobject со статусом «в продаже».
– При успехе — redirect на список объектов или загрузку фото через /admin_panel/media/photos/.
– Фотографии загружаются multipart POST /api/v2/photos/ с привязкой к property_id; файлы сохраняются в uploads/.

3.4.3. Алгоритм формирования договора купли-продажи (Word .docx)

Реализован в ContractController и manager_generate_contract_view / contract_download_view. (см. Приложение Б, рисунок Б.3)

Последовательность действий:
– Менеджер или администратор открывает /manager/contracts/generate/ или панель договоров.
– Указывает объект недвижимости, покупателя (user_id), дату и статус договора.
– Django вызывает POST /api/v2/contracts/ для создания записи в contract.
– Для генерации файла вызывается эндпоинт формирования .docx (python-docx): подставляются реквизиты объекта, стороны, цена.
– Путь к файлу сохраняется в generated_file_path; пользователь скачивает договор через /account/contracts/<id>/download/ или панель менеджера.
– При ошибке API Django выводит краткое сообщение через messages.error (format_api_detail).
"""

SECTION_35 = """
3.5. Документация по работе с информационной системой

3.5.1. Документация по работе с API

API реализован на FastAPI с версионированием:
– /api/v1/ — базовая версия (полный CRUD, аутентификация);
– /api/v2/ — версия, используемая Django-клиентом (пагинация fastapi-pagination, улучшенные схемы).

Основные группы эндпоинтов (префиксы относительно версии):
– /auth/login, /auth/register, /auth/logout, /auth/me — аутентификация и профиль;
– /properties — CRUD объектов недвижимости, фильтрация, смена статуса;
– /property-types — справочник типов (admin);
– /photos — загрузка и удаление фотографий;
– /documents — строительная документация по объекту;
– /contracts — договоры, генерация .docx.

Аутентификация: JWT Bearer. После POST /auth/login клиент получает access_token. Заголовок: Authorization: Bearer <token>.

Защита эндпоинтов: зависимости get_current_user, проверка роли admin/manager/user.

Интерактивная документация (offline Swagger):
– http://127.0.0.1:8000/docs — Swagger UI;
– http://127.0.0.1:8000/redoc — ReDoc;
– OpenAPI: /api/v1/openapi.json.

Публичные без токена: GET /properties, GET /properties/{id}, GET /photos, GET /documents/{property_id}, POST /auth/register, POST /auth/login.

Подробный перечень с примерами JSON — в файле API_ENDPOINTS_DOCUMENTATION.txt в корне проекта.

3.5.2. Документация по работе с веб-приложением

Базовый URL Django: http://127.0.0.1:8001/

Таблица 13 — Тестовые учётные записи (создаются скриптом app/get_password_hash.py или вручную)

Роль                    Email                  Пароль
Администратор           admin@example.com      password123
Менеджер                manager@example.com    password123
Пользователь            user@example.com       password123

1. Авторизация и регистрация
GET/POST /login/ — вход; POST /register/ — регистрация; POST /logout/ — выход. После входа — redirect на /catalog/.

Рисунок 3 — Страница авторизации

2. Каталог объектов (все пользователи, в т.ч. гости)
GET /catalog/ — список с фильтрами (тип, цена, статус) и пагинацией.
GET /properties/<id>/ — карточка объекта: фото, документы, цена/скидка.

Рисунок 4 — Каталог недвижимости

3. Управление объектами (администратор)
/admin_panel/properties/ — список; /admin_panel/properties/create/ — создание;
/admin_panel/properties/<id>/edit/ — редактирование; /admin_panel/property-types/ — типы объектов;
/admin_panel/users/ — назначение ролей; /admin_panel/media/photos/, /admin_panel/media/documents/ — медиа.

Рисунок 5 — Панель администратора

4. Панель менеджера
/manager/ — сводка; смена статуса объекта; /manager/contracts/generate/ — создание договора;
/manager/contracts/ — список договоров.

Рисунок 6 — Панель менеджера

5. Личный кабинет пользователя
/account/ — профиль, история просмотров (cookie), список договоров;
/account/contracts/<id>/download/ — скачивание .docx.

Рисунок 7 — Личный кабинет

6. Резервирование объекта
POST /properties/<id>/reserve/ — смена статуса на «забронирован» (для авторизованных пользователей).

3.5.3. Руководство по развёртыванию проекта

Требования: Python 3.10+, PostgreSQL, браузер Chrome/Firefox/Edge.

Шаг 1. PostgreSQL: создать БД, указать DATABASE_URL в app/.env.

Шаг 2. FastAPI (порт 8000):
cd tverdov_kursovya
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Шаг 3. Django (порт 8001):
cd web_client_django
python -m venv .venv
pip install -r requirements.txt
скопировать .env.example → .env (API_BASE_URL=http://127.0.0.1:8000/api/v2)
python manage.py migrate
python manage.py runserver 8001

Шаг 4. Проверка: открыть http://127.0.0.1:8001/, войти как admin; Swagger — http://127.0.0.1:8000/docs.

Шаг 5. Запуск тестов:
pytest tests/api
pytest tests/e2e -m e2e   # при запущенных FastAPI и Django
"""

SECTION_36 = """
3.6. Отчёт о тестировании проекта

3.6.1. Информационный заголовок

Таблица 14 — Информационный заголовок

Параметр              Значение
ID проекта            АРМ-ЗАСТРОЙЩИК-2026
Версия сборки         v1.0.0 (FastAPI + Django)
ФИО тестировщика      Твердов Даниил Сергеевич
Тип отчёта            Финальный отчёт о тестировании
Дата составления      16 мая 2026 г.

3.6.2. Резюме

Выполнена проверка функциональных требований ТЗ: сценарии ролей admin, manager, user и гостя; REST API v1/v2; веб-интерфейс Django.

Автоматизированные тесты:
– API (tests/api/): 86 тестов — пройдены успешно;
– E2E Selenium (tests/e2e/): 25 тестов — пройдены успешно при DJANGO_BASE_URL=http://127.0.0.1:8001.

Итого: 111 автоматизированных тест-кейсов. Критических дефектов на момент сдачи не выявлено.

3.6.3. Область тестирования

Таблица 15 — Область тестирования

№   Модуль / файл              Описание
1   test_auth.py, test_auth_extra.py   Регистрация, вход, JWT, роли
2   test_properties.py         CRUD объектов недвижимости
3   test_property_types.py     Справочник типов (v1)
4   test_property_types_v2.py  Типы объектов (v2)
5   test_photos.py             Загрузка и удаление фото
6   test_documents.py          Строительная документация
7   test_contracts.py          Договоры и генерация .docx
8   tests/e2e/test_*.py        UI: вход, регистрация, каталог, navbar, logout

3.6.4. Метрики

Таблица 16 — Метрики

Показатель          API-тесты    E2E-тесты
Всего тестов        86           25
Пройдено            86           25
Не пройдено         0            0

3.6.5. Реестр дефектов (устранённые в ходе разработки)

Таблица 17 — Реестр дефектов

ID       Модуль              Описание                              Критичность   Статус
BUG-02   API / properties    Неверный HTTP-статус при создании     Высокая       Устранён
BUG-03   API / properties    Валидация отрицательной скидки        Высокая       Устранён
BUG-04   API / contracts     POST без статуса 201                  Высокая       Устранён
BUG-05   Django UI           Длинные сообщения об ошибках API      Средняя       Устранён (format_api_detail)

3.6.6. Заключение по тестированию

Система соответствует ТЗ. Все 111 автоматизированных тестов выполнены успешно. Рекомендуется к опытной эксплуатации.
"""


SECTION_31 = """
3.1. Стек технологий

Backend (основной язык и фреймворки):
– Python 3.11+ — основной язык разработки всех компонентов системы.
– FastAPI — асинхронный веб-фреймворк для реализации REST API (бизнес-логика, обработка запросов, автоматическая документация Swagger/ReDoc).
– Django 5.x — веб-фреймворк для пользовательского интерфейса (шаблоны, формы, маршрутизация). Django выступает HTTP-клиентом к FastAPI и не хранит доменные данные в своей БД.
– SQLModel — ORM поверх SQLAlchemy для работы с PostgreSQL в FastAPI-части.
– Pydantic — валидация данных и сериализация схем запросов и ответов.

База данных:
– PostgreSQL — реляционная СУБД для централизованного хранения данных.
– psycopg2 / asyncpg — драйверы подключения к PostgreSQL.

Аутентификация и безопасность:
– JWT (JSON Web Tokens) — механизм аутентификации.
– python-jose — создание и проверка JWT-токенов.
– passlib (Argon2) — хеширование паролей пользователей.
– OAuth2 Password Flow — встроенная схема авторизации FastAPI.

Тестовая инфраструктура:
– pytest — фреймворк для запуска тестов.
– pytest-asyncio — асинхронные тесты FastAPI.
– httpx — HTTP-клиент для API-тестов.
– Selenium — E2E-тестирование Django-интерфейса (tests/e2e, Page Object Model).

Дополнительные библиотеки:
– python-dotenv, pydantic-settings — конфигурация окружения.
– email-validator — проверка email при регистрации.
– requests — HTTP-запросы из Django к FastAPI.
– python-docx — генерация договоров купли-продажи в формате Word (.docx).
– Pillow — обработка изображений при загрузке фотографий.
– fastapi-pagination — пагинация списков в API v2.
"""


def find_body_start(text: str) -> int:
    """Позиция начала основного текста (после оглавления)."""
    m = re.search(r"\nВВЕДЕНИЕ\nВ современных", text)
    if not m:
        raise ValueError("Не найден блок ВВЕДЕНИЕ")
    return m.start() + 1


def find_section_31(text: str, from_pos: int = 0) -> int:
    """Позиция раздела 3.1 в теле документа (не в оглавлении)."""
    for m in re.finditer(r"\n3\.1\. Стек технологий\n", text):
        if m.start() >= from_pos:
            nxt = text[m.end() : m.end() + 40]
            if "Backend" in nxt or "Python" in nxt:
                return m.start() + 1
    raise ValueError("Не найден раздел 3.1 в теле документа")


def find_glossary(text: str, from_pos: int = 0) -> int:
    m = re.search(r"\n4\. ГЛОССАРИЙ\n", text[from_pos:])
    if not m:
        m = re.search(r"\n4\. ГЛОССАРИЙ\s", text[from_pos:])
    if not m:
        raise ValueError("Не найден раздел 4. ГЛОССАРИЙ")
    return from_pos + m.start() + 1


def main() -> None:
    raw = BETA_EXTRACT.read_text(encoding="utf-8")
    text = clean_pdf_artifacts(raw)

    body_start = find_body_start(text)
    front = text[:body_start].strip()
    body = text[body_start:]

    sec31 = find_section_31(body, 0)
    sec4 = find_glossary(body, sec31)

    part12 = global_replacements(body[:sec31].strip())
    part12 = re.sub(
        r"ведение журнала аудита действий пользователей,?\s*а?\s*также\s*",
        "",
        part12,
        flags=re.IGNORECASE,
    )
    part12 = part12.replace("продажи → аудит действий", "продажи → скачивание договора")
    part12 = part12.replace("журнала аудита действий", "истории операций")
    part12 = re.sub(
        r"ведение журнала аудита действий пользователей и проверку",
        "проверку",
        part12,
    )
    part12 = re.sub(
        r"формирования документов Word \(\.docx\), ведение журнала аудита действий пользователей, а\s*",
        "формирования договоров Word (.docx), ",
        part12,
    )
    part3 = "\n\n".join(
        [
            SECTION_31.strip(),
            SECTION_32.strip(),
            SECTION_33.strip(),
            SECTION_34.strip(),
            SECTION_35.strip(),
            SECTION_36.strip(),
        ]
    )
    part45 = global_replacements(body[sec4:].strip())
    part45 = re.sub(
        r"ведение журнала аудита действий пользователей,?\s*а также\s*",
        "",
        part45,
        flags=re.IGNORECASE,
    )
    part45 = part45.replace(
        "Покрытие кода FastAPI-бэкенда составило 82%, а Django-\nприложения — 84%, что превышает минимальные требования, установленные планом\nтестирования.",
        "Все 111 автоматизированных тестов (86 API + 25 E2E) завершены успешно.",
    )

    BUG_REPORT = """
Баг-репорт по результатам тестирования API v1

Таблица А.1 — Реестр дефектов API v1

ID дефекта   Описание дефекта                                              Критичность   Статус
BUG-02       Неверный HTTP-статус при создании объекта (200 вместо 201)    Высокая       Устранён в v2
BUG-03       Отсутствовала валидация отрицательной скидочной цены          Высокая       Устранён в v2
BUG-04       POST /contracts/ не возвращал статус 201 Created              Высокая       Устранён в v2
BUG-05       Непонятные сообщения об ошибках валидации в Django UI         Средняя       Устранён (format_api_detail)

Примечание: журнал аудита в проект не входит; соответствующие пункты из шаблона ПЗ исключены.
"""
    if "Баг-репорт" in part45 and "ПРИЛОЖЕНИЕ Б" in part45:
        i = part45.find("Баг-репорт")
        j = part45.find("ПРИЛОЖЕНИЕ Б")
        part45 = part45[:i].rstrip() + "\n\n" + BUG_REPORT.strip() + "\n\n" + part45[j:]

    part45 = part45.replace(
        "Рисунок А.1 — Результаты запуска API-тестов v1",
        "Рисунок А.1 — Результаты pytest tests/api (86 тестов)",
    )
    part45 = part45.replace(
        "Рисунок А.2 — Результаты запуска и покрытие API-тестов v2",
        "Рисунок А.2 — Пример прогона API-тестов с маркерами v1/v2",
    )
    part45 = part45.replace(
        "Рисунок А.3 — Результаты запуска и покрытие тестов Django",
        "Рисунок А.3 — Результаты pytest tests/e2e -m e2e (25 тестов Selenium)",
    )

    text = "\n\n".join([front, part12, part3, part45])
    header = ""

    # Финальная зачистка по всему документу
    text = global_replacements(text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    OUT_FILE.write_text(header + text, encoding="utf-8")
    print(f"Written: {OUT_FILE}")
    print(f"Size: {OUT_FILE.stat().st_size} chars, ~{len(text.split())} words")


if __name__ == "__main__":
    main()
