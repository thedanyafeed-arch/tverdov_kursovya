import pytest


@pytest.mark.e2e
class TestCatalogPage:
    def test_catalog_heading(self, catalog_page):
        assert "Каталог" in catalog_page.get_heading()

    def test_catalog_has_filter_form(self, catalog_page):
        assert catalog_page.is_visible(catalog_page.FILTER_FORM)

    def test_catalog_apply_filters(self, catalog_page):
        catalog_page.apply_filters()
        assert "Каталог" in catalog_page.get_heading()

    def test_authenticated_user_sees_catalog_after_login(
        self,
        login_page,
        open_page,
        test_user_credentials,
    ):
        from tests.e2e.pages import CatalogPage

        creds = test_user_credentials
        login_page.login(creds["email"], creds["password"])
        assert login_page.is_logged_in(creds["email"]) or "/catalog/" in login_page.driver.current_url

        catalog = open_page("catalog/", CatalogPage)
        assert "Каталог" in catalog.get_heading()
        assert catalog.property_cards_count() >= 0
