from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .contract_choices import apply_contract_full_choices
from .media_urls import api_origin_from_settings, api_upload_absolute_url, attach_photo_src
from .forms import (
    AssignRoleForm,
    ContractFullForm,
    ContractPatchForm,
    DeleteUserForm,
    LoginForm,
    ProfileUpdateForm,
    PropertyFilterForm,
    PropertyForm,
    RegisterForm,
    SimplePropertyTypeForm,
    UploadDocumentForm,
    UploadPhotoForm,
    UploadPhotosForm,
)
from .property_labels import build_user_email_map, property_display_by_ids
from .services.api_client import ApiClient, ApiClientError
from .utils import (
    api_client,
    extract_role_from_token,
    is_manager_or_admin,
    require_admin,
    require_api_auth,
    require_manager,
    track_view_history,
)


def _enrich_contracts_for_ui(client: ApiClient, contracts: list[dict]) -> list[tuple[dict, str, str, str]]:
    """Договор, подпись объекта (тип — адрес), email клиента, email менеджера."""
    oids = {int(c["realEstateObjectId"]) for c in contracts if c.get("realEstateObjectId") is not None}
    pmap = property_display_by_ids(client, oids)
    emap = build_user_email_map(client)
    rows: list[tuple[dict, str, str, str]] = []
    for c in contracts:
        oid = c.get("realEstateObjectId")
        obj_label = pmap.get(int(oid), "—") if oid is not None else "—"
        uid = c.get("userId")
        mid = c.get("managerId")
        client_em = emap.get(int(uid), "—") if uid is not None else "—"
        mgr_em = emap.get(int(mid), "—") if mid is not None else "—"
        rows.append((c, obj_label, client_em, mgr_em))
    return rows


def _property_type_labels(client: ApiClient) -> dict[int, str]:
    try:
        items = client.list_property_types()
        return {int(t["id"]): str(t["name"]) for t in items}
    except ApiClientError:
        return {}


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = ApiClient()
        try:
            token_payload = client.login(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            request.session["access_token"] = token_payload["access_token"]
            request.session["token_type"] = token_payload.get("token_type", "bearer")
            request.session["role_name"] = extract_role_from_token(token_payload["access_token"])
            user_info = api_client(request).me()
            request.session["user_info"] = user_info
            messages.success(request, "Вход выполнен.")
            return redirect("catalog")
        except ApiClientError as exc:
            messages.error(request, exc.user_message)
    return render(request, "registration/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request: HttpRequest) -> HttpResponse:
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = ApiClient()
        try:
            client.register(form.cleaned_data["email"], form.cleaned_data["password"])
            messages.success(request, "Пользователь создан. Теперь можно войти.")
            return redirect("login")
        except ApiClientError as exc:
            messages.error(request, exc.user_message)
    return render(request, "registration/register.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.session.get("access_token"):
        try:
            api_client(request).logout()
        except ApiClientError:
            pass
    request.session.flush()
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect("login")


@require_http_methods(["GET"])
def forgot_password_view(request: HttpRequest) -> HttpResponse:
    # В проекте не реализуем email-восстановление пароля.
    # Смена пароля выполняется в профиле после входа.
    return render(request, "registration/forgot_password.html")


@require_http_methods(["GET"])
def catalog_view(request: HttpRequest) -> HttpResponse:
    form = PropertyFilterForm(request.GET or None)
    filters: dict = {}
    client = api_client(request)
    property_types: list = []
    try:
        property_types = client.list_property_types()
    except ApiClientError:
        property_types = []

    # динамически наполняем выпадающий список типов
    type_choices = [("", "Любой тип")] + [(str(t["id"]), str(t["name"])) for t in property_types]
    form.fields["property_type_id"].choices = type_choices

    if form.is_valid():
        for key, value in form.cleaned_data.items():
            if value in (None, ""):
                continue
            if key == "property_type_id":
                filters[key] = int(value)
            else:
                filters[key] = value
    filters.setdefault("size", 12)
    filters.setdefault("page", 1)

    query_copy = request.GET.copy()
    query_copy.pop("page", None)
    preserved_query = query_copy.urlencode()

    properties_page: dict = {"items": []}
    try:
        properties_page = client.list_properties(filters=filters)
    except ApiClientError as exc:
        messages.error(request, f"Ошибка загрузки каталога: {exc}")

    origin = api_origin_from_settings()
    cover_urls: dict[int, str] = {}
    try:
        all_photo_rows = client.list_all_photos()
    except ApiClientError:
        all_photo_rows = []
    best_photo: dict[int, tuple[int, dict]] = {}
    for ph in all_photo_rows:
        raw_pid = ph.get("realEstateObjectId")
        if raw_pid is None:
            continue
        pid = int(raw_pid)
        ph_num = ph.get("id") or 0
        cur = best_photo.get(pid)
        if cur is None or ph_num < cur[0]:
            best_photo[pid] = (ph_num, ph)
    for pid, (_, ph) in best_photo.items():
        cover_urls[pid] = api_upload_absolute_url(ph.get("filePath"), origin)

    items_out: list[dict] = []
    for raw in properties_page.get("items", []):
        row = dict(raw)
        rid = raw.get("id")
        row["cover_photo_url"] = cover_urls.get(int(rid)) if rid is not None else None
        items_out.append(row)
    properties_page_render = dict(properties_page)
    properties_page_render["items"] = items_out

    return render(
        request,
        "catalog/list.html",
        {
            "form": form,
            "page_obj": properties_page_render,
            "property_types": property_types,
            "preserved_query": preserved_query,
        },
    )


@require_http_methods(["GET", "POST"])
def property_detail_view(request: HttpRequest, property_id: int) -> HttpResponse:
    client = api_client(request)

    if request.method == "POST":
        if not is_manager_or_admin(request):
            messages.error(request, "Недостаточно прав для изменения медиа.")
            return redirect(reverse("property_detail", kwargs={"property_id": property_id}))

        action = request.POST.get("action")
        try:
            if action == "upload_photo":
                form = UploadPhotoForm(request.POST, request.FILES)
                if form.is_valid():
                    client.upload_photo(property_id, form.cleaned_data["file"])
                    messages.success(request, "Фото загружено.")
                else:
                    messages.error(request, "Выберите корректный файл фото.")
            elif action == "update_photo":
                photo_id = int(request.POST.get("photo_id"))
                file_obj = request.FILES.get("file")
                if not file_obj:
                    raise ValueError("Не выбран файл фото")
                client.update_photo(photo_id, file_obj)
                messages.success(request, "Фото обновлено.")
            elif action == "delete_photo":
                client.delete_photo(int(request.POST.get("photo_id")))
                messages.success(request, "Фото удалено.")
            elif action == "upload_document":
                form = UploadDocumentForm(request.POST, request.FILES)
                if form.is_valid():
                    client.upload_document(property_id, form.cleaned_data["file"], form.cleaned_data["doc_type"])
                    messages.success(request, "Документ загружен.")
                else:
                    messages.error(request, "Проверьте файл и тип документа.")
            elif action == "update_document":
                doc_id = int(request.POST.get("doc_id"))
                doc_type = request.POST.get("doc_type", "").strip()
                file_obj = request.FILES.get("file")
                if not file_obj or not doc_type:
                    raise ValueError("Для обновления нужен файл и тип документа")
                client.update_document(doc_id, file_obj, doc_type)
                messages.success(request, "Документ обновлен.")
            elif action == "delete_document":
                client.delete_document(int(request.POST.get("doc_id")))
                messages.success(request, "Документ удален.")
        except (ValueError, TypeError):
            messages.error(request, "Некорректные параметры действия.")
        except ApiClientError as exc:
            messages.error(request, f"Ошибка изменения медиа: {exc}")
        return redirect(reverse("property_detail", kwargs={"property_id": property_id}))

    try:
        property_obj = client.get_property(property_id)
        photos_raw = client.list_property_photos(property_id)
        photos = [attach_photo_src(ph) for ph in photos_raw]
        documents = client.list_property_documents(property_id)
        track_view_history(request, property_obj)
    except ApiClientError as exc:
        messages.error(request, f"Ошибка загрузки объекта: {exc}")
        return redirect("catalog")

    type_labels = _property_type_labels(client)
    tid = property_obj.get("propertyTypeId")
    property_type_display = (
        type_labels.get(int(tid), "—") if tid is not None else "—"
    )

    return render(
        request,
        "catalog/detail.html",
        {
            "property": property_obj,
            "property_type_display": property_type_display,
            "photos": photos,
            "documents": documents,
            "photo_form": UploadPhotoForm(),
            "document_form": UploadDocumentForm(),
        },
    )


@require_http_methods(["POST"])
def reserve_property_view(request: HttpRequest, property_id: int) -> HttpResponse:
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect
    try:
        api_client(request)._request("POST", f"/properties/{property_id}/reserve")
        messages.success(request, "Объект забронирован.")
    except ApiClientError as exc:
        messages.error(request, f"Ошибка бронирования: {exc}")
    return redirect(reverse("property_detail", kwargs={"property_id": property_id}))


def account_view(request: HttpRequest) -> HttpResponse:
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect
    client = api_client(request)
    contracts: list = []
    try:
        contracts = client.list_contracts()
    except ApiClientError as exc:
        messages.error(request, f"Не удалось загрузить договоры: {exc}")
    history = request.session.get("view_history", [])
    enriched = _enrich_contracts_for_ui(client, contracts)
    info = request.session.get("user_info") or {}
    self_id = info.get("id")
    self_email = (str(info.get("email") or "")).strip()
    if self_id is not None and self_email:
        patched: list[tuple[dict, str, str, str]] = []
        for c, obj_l, cli_em, mgr_em in enriched:
            if c.get("userId") is not None and int(c["userId"]) == int(self_id):
                cli_em = self_email
            patched.append((c, obj_l, cli_em, mgr_em))
        enriched = patched
    return render(
        request,
        "account/index.html",
        {"contracts_enriched": enriched, "contracts": contracts, "history": history},
    )


@require_http_methods(["GET", "POST"])
def profile_view(request: HttpRequest) -> HttpResponse:
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect

    form = ProfileUpdateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payload = {}
        if form.cleaned_data.get("email"):
            payload["email"] = form.cleaned_data["email"]
        if form.cleaned_data.get("password"):
            payload["password"] = form.cleaned_data["password"]
        if not payload:
            messages.info(request, "Нет изменений.")
            return redirect("profile")
        try:
            api_client(request).update_me(payload)
            request.session["user_info"] = api_client(request).me()
            messages.success(request, "Профиль обновлён.")
            return redirect("profile")
        except ApiClientError as exc:
            messages.error(request, f"Ошибка обновления профиля: {exc}")

    return render(request, "account/profile.html", {"form": form})


def contract_download_view(request: HttpRequest, contract_id: int) -> HttpResponse:
    auth_redirect = require_api_auth(request)
    if auth_redirect:
        return auth_redirect
    try:
        content = api_client(request).download_contract(contract_id)
    except ApiClientError as exc:
        messages.error(request, f"Ошибка скачивания договора: {exc}")
        return redirect("account")
    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="contract_{contract_id}.docx"'
    return response


def manager_panel_view(request: HttpRequest) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    client = api_client(request)
    properties_page = {"items": []}
    contracts: list = []
    try:
        properties_page = client.list_properties(filters={"page": 1, "size": 50})
        contracts = client.list_all_contracts()
    except ApiClientError as exc:
        messages.error(request, f"Не удалось загрузить панель менеджера: {exc}")
    enriched = _enrich_contracts_for_ui(client, contracts)
    return render(
        request,
        "manager/index.html",
        {
            "properties": properties_page.get("items", []),
            "contracts_enriched": enriched,
            "properties_for_select": properties_page.get("items", []),
        },
    )


@require_http_methods(["POST"])
def manager_change_status_view(request: HttpRequest, property_id: int) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    new_status = request.POST.get("new_status", "").strip()
    if not new_status:
        messages.error(request, "Не указан статус.")
        return redirect("manager_panel")
    try:
        api_client(request).update_property_status(property_id, new_status)
        messages.success(request, "Статус обновлён.")
    except ApiClientError as exc:
        messages.error(request, f"Ошибка смены статуса: {exc}")
    return redirect("manager_panel")


@require_http_methods(["POST"])
def manager_generate_contract_view(request: HttpRequest) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    property_id = request.POST.get("property_id")
    try:
        api_client(request).generate_contract(int(property_id), None)
        messages.success(request, "Договор создан.")
    except (ValueError, TypeError):
        messages.error(request, "Укажите корректный объект.")
    except ApiClientError as exc:
        messages.error(request, f"Ошибка генерации договора: {exc}")
    return redirect("manager_panel")


def manager_contracts_list_view(request: HttpRequest) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    client = api_client(request)
    contracts = []
    try:
        contracts = client.list_all_contracts()
    except ApiClientError as exc:
        messages.error(request, f"Не удалось загрузить договоры: {exc}")
    enriched = _enrich_contracts_for_ui(client, contracts)
    return render(request, "manager/contracts_list.html", {"contracts_enriched": enriched})


@require_http_methods(["GET", "POST"])
def manager_contract_detail_view(request: HttpRequest, contract_id: int) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    client = api_client(request)
    try:
        contract = client.get_contract(contract_id)
    except ApiClientError as exc:
        messages.error(request, str(exc))
        return redirect("manager_contracts_list")

    oid = contract.get("realEstateObjectId")
    if oid is not None:
        property_title = property_display_by_ids(client, [int(oid)]).get(int(oid), "—")
    else:
        property_title = "—"
    uid = contract.get("userId")
    mid = contract.get("managerId")
    emap = build_user_email_map(client)
    client_email = emap.get(int(uid), "—") if uid is not None else "—"
    manager_email = emap.get(int(mid), "—") if mid is not None else "—"

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "delete":
                client.delete_contract(contract_id)
                messages.success(request, "Договор удалён.")
                return redirect("manager_contracts_list")
            if action == "patch":
                pf = ContractPatchForm(request.POST)
                if pf.is_valid():
                    payload = {}
                    st = pf.cleaned_data.get("status") or ""
                    if st.strip():
                        payload["status"] = st.strip()
                    cd = pf.cleaned_data.get("contract_date", "").strip()
                    if cd:
                        payload["contract_date"] = cd
                    if not payload:
                        messages.info(request, "Укажите хотя бы одно изменение.")
                        return redirect("manager_contract_detail", contract_id=contract_id)
                    client.patch_contract(contract_id, payload)
                    messages.success(request, "Договор обновлён.")
                    return redirect("manager_contract_detail", contract_id=contract_id)
                messages.error(request, "Проверьте форму изменения.")
            elif action == "full":
                ff = ContractFullForm(request.POST)
                apply_contract_full_choices(ff, client, contract)
                if ff.is_valid():
                    client.put_contract(
                        contract_id,
                        {
                            "real_estate_object_id": ff.cleaned_data["real_estate_object_id"],
                            "user_id": ff.cleaned_data["user_id"],
                            "manager_id": ff.cleaned_data["manager_id"],
                            "contract_date": ff.cleaned_data["contract_date"].strip(),
                            "status": ff.cleaned_data["status"],
                        },
                    )
                    messages.success(request, "Договор полностью обновлён.")
                    return redirect("manager_contract_detail", contract_id=contract_id)
                messages.error(request, "Проверьте все поля полного редактирования.")
        except ApiClientError as exc:
            messages.error(request, str(exc))

    patch_form = ContractPatchForm(
        initial={
            "status": contract.get("status", ""),
            "contract_date": contract.get("contractDate") or "",
        }
    )
    full_form = ContractFullForm(
        initial={
            "real_estate_object_id": contract.get("realEstateObjectId"),
            "user_id": contract.get("userId"),
            "manager_id": contract.get("managerId"),
            "contract_date": contract.get("contractDate") or "",
            "status": contract.get("status"),
        }
    )
    apply_contract_full_choices(full_form, client, contract)

    return render(
        request,
        "manager/contract_detail.html",
        {
            "contract": contract,
            "patch_form": patch_form,
            "full_form": full_form,
            "property_title": property_title,
            "client_email": client_email,
            "manager_email": manager_email,
        },
    )


def admin_properties_list_view(request: HttpRequest) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    client = api_client(request)
    properties_page = {"items": []}
    try:
        properties_page = client.list_properties(filters={"page": 1, "size": 50})
    except ApiClientError as exc:
        messages.error(request, f"Ошибка загрузки объектов: {exc}")
    return render(request, "admin_panel/properties_list.html", {"properties": properties_page.get("items", [])})


@require_http_methods(["GET", "POST"])
def admin_property_create_view(request: HttpRequest) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect

    client = api_client(request)
    property_types = []
    try:
        property_types = client.list_property_types()
    except ApiClientError:
        property_types = []
    type_choices = [(str(t["id"]), str(t["name"])) for t in property_types]

    form = PropertyForm(request.POST or None)
    form.fields["property_type_id"].choices = type_choices
    photos_form = UploadPhotosForm()
    created_property = None

    if request.method == "POST" and request.POST.get("action") != "upload_photos" and form.is_valid():
        try:
            payload = form.cleaned_data.copy()
            payload["property_type_id"] = int(payload["property_type_id"])
            created_property = api_client(request).create_property(payload)
            messages.success(request, "Объект создан.")
        except ApiClientError as exc:
            messages.error(request, f"Ошибка создания: {exc}")
    # загрузка фото сразу после создания (вторая кнопка на той же странице)
    if request.method == "POST" and request.POST.get("action") == "upload_photos":
        manager_redirect = require_manager(request)
        if manager_redirect:
            return manager_redirect
        try:
            prop_id = int(request.POST.get("property_id"))
        except Exception:
            messages.error(request, "Некорректный ID объекта.")
            return redirect("admin_property_create")
        photos_form = UploadPhotosForm(request.POST, request.FILES)
        if photos_form.is_valid():
            files = request.FILES.getlist("files")
            if not files:
                messages.error(request, "Выберите файлы фото.")
            else:
                ok = 0
                for f in files:
                    try:
                        api_client(request).upload_photo(prop_id, f)
                        ok += 1
                    except ApiClientError as exc:
                        messages.error(request, f"Не удалось загрузить {f.name}: {exc}")
                if ok:
                    messages.success(request, f"Загружено фото: {ok}.")
        else:
            messages.error(request, "Проверьте выбранные файлы.")
        return redirect(reverse("admin_property_edit", kwargs={"property_id": prop_id}))

    return render(
        request,
        "admin_panel/property_form.html",
        {
            "form": form,
            "title": "Создать объект",
            "created_property": created_property,
            "photos_form": photos_form,
        },
    )


@require_http_methods(["GET", "POST"])
def admin_property_edit_view(request: HttpRequest, property_id: int) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect

    client = api_client(request)
    try:
        current = client.get_property(property_id)
    except ApiClientError as exc:
        messages.error(request, f"Объект не найден: {exc}")
        return redirect("admin_properties_list")

    initial = {
        "property_type_id": current.get("propertyTypeId"),
        "total_area": current.get("totalArea"),
        "finishing": current.get("finishing"),
        "wall_material": current.get("wallMaterial"),
        "floor": current.get("floor"),
        "floors_total": current.get("floorsTotal"),
        "price": current.get("price"),
        "discount_price": current.get("discountPrice"),
        "status": current.get("status"),
        "address": current.get("address"),
        "description": current.get("description"),
    }
    # choices для типа недвижимости
    property_types = []
    try:
        property_types = client.list_property_types()
    except ApiClientError:
        property_types = []
    type_choices = [(str(t["id"]), str(t["name"])) for t in property_types]

    photos: list = []
    try:
        origin = api_origin_from_settings()
        photos = [attach_photo_src(ph, origin) for ph in client.list_property_photos(property_id)]
    except ApiClientError:
        photos = []

    form = PropertyForm(request.POST or None, initial=initial)
    form.fields["property_type_id"].choices = type_choices

    if request.method == "POST":
        action = request.POST.get("action")
        if action:
            if not is_manager_or_admin(request):
                messages.error(request, "Недостаточно прав.")
                return redirect("catalog")
            try:
                if action == "upload_photo":
                    pform = UploadPhotoForm(request.POST, request.FILES)
                    if pform.is_valid():
                        client.upload_photo(property_id, pform.cleaned_data["file"])
                        messages.success(request, "Фото загружено.")
                    else:
                        messages.error(request, "Выберите файл фото.")
                elif action == "upload_photos":
                    mform = UploadPhotosForm(request.POST, request.FILES)
                    if mform.is_valid():
                        files_list = request.FILES.getlist("files")
                        if files_list:
                            ok = 0
                            for f in files_list:
                                try:
                                    client.upload_photo(property_id, f)
                                    ok += 1
                                except ApiClientError as exc:
                                    messages.error(request, f"Не удалось загрузить {f.name}: {exc}")
                            if ok:
                                messages.success(request, f"Загружено фото: {ok}.")
                        else:
                            messages.error(request, "Выберите файлы фото.")
                    else:
                        messages.error(request, "Проверьте выбранные файлы.")
                elif action == "update_photo":
                    photo_tid = int(request.POST.get("photo_id"))
                    file_obj = request.FILES.get("file")
                    if file_obj:
                        client.update_photo(photo_tid, file_obj)
                        messages.success(request, "Фото обновлено.")
                    else:
                        messages.error(request, "Выберите файл для замены.")
                elif action == "delete_photo":
                    client.delete_photo(int(request.POST.get("photo_id")))
                    messages.success(request, "Фото удалено.")
                else:
                    messages.error(request, "Неизвестное действие с файлами.")
            except (ValueError, TypeError):
                messages.error(request, "Некорректные параметры.")
            except ApiClientError as exc:
                messages.error(request, str(exc))
            return redirect(reverse("admin_property_edit", kwargs={"property_id": property_id}))

        elif form.is_valid():
            try:
                payload = form.cleaned_data.copy()
                payload["property_type_id"] = int(payload["property_type_id"])
                client.update_property(property_id, payload)
                messages.success(request, "Объект обновлён.")
                return redirect(reverse("admin_property_edit", kwargs={"property_id": property_id}))
            except ApiClientError as exc:
                messages.error(request, f"Ошибка обновления: {exc}")

    return render(
        request,
        "admin_panel/property_form.html",
        {
            "form": form,
            "title": "Редактировать объект",
            "property_id_edit": property_id,
            "photos": photos,
            "photo_upload_form": UploadPhotoForm(),
            "bulk_photos_form": UploadPhotosForm(),
            "created_property": None,
        },
    )


@require_http_methods(["GET", "POST"])
def admin_property_types_view(request: HttpRequest) -> HttpResponse:
    redir = require_manager(request)
    if redir:
        return redir
    client = api_client(request)
    create_form = SimplePropertyTypeForm()

    if request.method == "POST":
        act = request.POST.get("post_action") or ""
        try:
            if act == "create":
                create_form = SimplePropertyTypeForm(request.POST)
                if create_form.is_valid():
                    client.create_property_type(create_form.cleaned_data["name"].strip())
                    messages.success(request, "Тип добавлен.")
                    return redirect("admin_property_types")
            elif act == "rename":
                tid = int(request.POST.get("type_id"))
                name = (request.POST.get("name") or "").strip()
                if not name:
                    messages.error(request, "Укажите название типа.")
                else:
                    client.update_property_type(tid, name)
                    messages.success(request, "Тип обновлён.")
                    return redirect("admin_property_types")
            elif act == "delete":
                tid = int(request.POST.get("type_id"))
                client.delete_property_type(tid)
                messages.success(request, "Тип удалён.")
                return redirect("admin_property_types")
        except ApiClientError as exc:
            messages.error(request, str(exc))
        except (TypeError, ValueError):
            messages.error(request, "Некорректные данные.")

    types_list: list = []
    try:
        types_list = client.list_property_types()
    except ApiClientError as exc:
        messages.error(request, str(exc))

    return render(
        request,
        "admin_panel/property_types.html",
        {"types_list": types_list, "create_form": create_form},
    )


@require_http_methods(["GET", "POST"])
def admin_users_view(request: HttpRequest) -> HttpResponse:
    redir = require_admin(request)
    if redir:
        return redir
    assign_form = AssignRoleForm()
    delete_form = DeleteUserForm()
    users_rows: list[dict] = []
    try:
        users_rows = api_client(request).list_users()
    except ApiClientError as exc:
        messages.error(request, str(exc))

    if request.method == "POST":
        which = request.POST.get("which")
        try:
            if which == "assign":
                assign_form = AssignRoleForm(request.POST)
                if assign_form.is_valid():
                    uid = assign_form.cleaned_data["user_id"]
                    rn = assign_form.cleaned_data["role_name"]
                    api_client(request).assign_user_role(uid, rn)
                    messages.success(request, "Роль сохранена.")
                    return redirect("admin_users")
            elif which == "delete":
                delete_form = DeleteUserForm(request.POST)
                if delete_form.is_valid():
                    api_client(request).delete_user_account(delete_form.cleaned_data["user_id"])
                    messages.success(request, "Пользователь удалён.")
                    return redirect("admin_users")
        except ApiClientError as exc:
            messages.error(request, str(exc))

    return render(
        request,
        "admin_panel/users.html",
        {
            "assign_form": assign_form,
            "delete_form": delete_form,
            "users_rows": users_rows,
        },
    )


@require_http_methods(["GET"])
def admin_all_photos_view(request: HttpRequest) -> HttpResponse:
    redir = require_manager(request)
    if redir:
        return redir
    photos: list = []
    try:
        photos = api_client(request).list_all_photos()
    except ApiClientError as exc:
        messages.error(request, str(exc))
    origin = api_origin_from_settings()
    client_req = api_client(request)
    pids = {int(ph["realEstateObjectId"]) for ph in photos if ph.get("realEstateObjectId") is not None}
    pmap = property_display_by_ids(client_req, pids)
    enriched = [
        (
            attach_photo_src(ph, origin),
            pmap.get(int(ph["realEstateObjectId"]), "—") if ph.get("realEstateObjectId") is not None else "—",
        )
        for ph in photos
    ]
    return render(request, "admin_panel/all_photos.html", {"photos_enriched": enriched})


@require_http_methods(["GET"])
def admin_all_documents_view(request: HttpRequest) -> HttpResponse:
    redir = require_manager(request)
    if redir:
        return redir
    docs: list = []
    try:
        docs = api_client(request).list_all_documents()
    except ApiClientError as exc:
        messages.error(request, str(exc))
    client_req = api_client(request)
    dids = {int(d["realEstateObjectId"]) for d in docs if d.get("realEstateObjectId") is not None}
    dmap = property_display_by_ids(client_req, dids)
    enriched = [
        (d, dmap.get(int(d["realEstateObjectId"]), "—") if d.get("realEstateObjectId") is not None else "—") for d in docs
    ]
    return render(request, "admin_panel/all_documents.html", {"docs_enriched": enriched})


@require_http_methods(["POST"])
def admin_property_delete_view(request: HttpRequest, property_id: int) -> HttpResponse:
    manager_redirect = require_manager(request)
    if manager_redirect:
        return manager_redirect
    try:
        api_client(request).delete_property(property_id)
        messages.success(request, "Объект удалён.")
    except ApiClientError as exc:
        messages.error(request, f"Ошибка удаления: {exc}")
    return redirect("admin_properties_list")


def document_download_view(request: HttpRequest, doc_id: int) -> HttpResponse:
    try:
        content = api_client(request).download_document(doc_id)
    except ApiClientError as exc:
        messages.error(request, f"Ошибка скачивания документа: {exc}")
        return redirect("catalog")
    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="document_{doc_id}"'
    return response

