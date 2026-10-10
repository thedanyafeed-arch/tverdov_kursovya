import pytest


@pytest.mark.e2e
class TestIndexPage:
    def test_home_page_title(self, home_page):
        assert "АРМ" in home_page.get_title_text()

    def test_navigate_to_catalog(self, home_page):
        from tests.e2e.pages import CatalogPage

        home_page.go_to_catalog()
        catalog = CatalogPage(home_page.driver)
        assert "Каталог" in catalog.get_heading()

    def test_navigate_to_login(self, home_page, login_page):
        home_page.go_to_login()
        assert login_page.is_visible(login_page.EMAIL)
