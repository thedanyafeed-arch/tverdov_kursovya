import pytest
from selenium.webdriver.common.by import By


@pytest.mark.e2e
class TestNavbar:
    def test_guest_nav_links(self, home_page):
        assert home_page.is_visible((By.LINK_TEXT, "Войти"))
        assert home_page.is_visible((By.LINK_TEXT, "Регистрация"))
        assert home_page.is_visible((By.LINK_TEXT, "Каталог"))

    def test_authenticated_nav_links(self, login_page, open_page, test_user_credentials):
        creds = test_user_credentials
        login_page.login(creds["email"], creds["password"])

        open_page("catalog/", None)
        assert login_page.is_visible((By.LINK_TEXT, "Кабинет"))
        assert login_page.is_visible((By.LINK_TEXT, "Выйти"))
        assert creds["email"] in login_page.driver.page_source
