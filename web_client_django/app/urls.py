from django.urls import path
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    # auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    # catalog
    path("catalog/", views.catalog_view, name="catalog"),
    path("properties/<int:property_id>/", views.property_detail_view, name="property_detail"),
    path("properties/<int:property_id>/reserve/", views.reserve_property_view, name="property_reserve"),
    # account
    path("account/", views.account_view, name="account"),
    path("account/profile/", views.profile_view, name="profile"),
    path("account/contracts/<int:contract_id>/download/", views.contract_download_view, name="contract_download"),
    # manager panel
    path("manager/", views.manager_panel_view, name="manager_panel"),
    path("manager/properties/<int:property_id>/status/", views.manager_change_status_view, name="manager_change_status"),
    path("manager/contracts/generate/", views.manager_generate_contract_view, name="manager_generate_contract"),
    path("manager/contracts/", views.manager_contracts_list_view, name="manager_contracts_list"),
    path(
        "manager/contracts/<int:contract_id>/",
        views.manager_contract_detail_view,
        name="manager_contract_detail",
    ),
    # admin panel (custom, не django-admin)
    path(
        "admin_panel/",
        RedirectView.as_view(permanent=False, pattern_name="admin_properties_list"),
        name="admin_panel",
    ),
    path("admin_panel/properties/", views.admin_properties_list_view, name="admin_properties_list"),
    path("admin_panel/properties/create/", views.admin_property_create_view, name="admin_property_create"),
    path("admin_panel/properties/<int:property_id>/edit/", views.admin_property_edit_view, name="admin_property_edit"),
    path("admin_panel/properties/<int:property_id>/delete/", views.admin_property_delete_view, name="admin_property_delete"),
    path("admin_panel/property-types/", views.admin_property_types_view, name="admin_property_types"),
    path("admin_panel/users/", views.admin_users_view, name="admin_users"),
    path("admin_panel/media/photos/", views.admin_all_photos_view, name="admin_all_photos"),
    path("admin_panel/media/documents/", views.admin_all_documents_view, name="admin_all_documents"),
    path("admin_panel/documents/<int:doc_id>/download/", views.document_download_view, name="document_download"),
]

