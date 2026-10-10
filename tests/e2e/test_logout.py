import pytest
from selenium.webdriver.common.by import By


@pytest.mark.e2e
class TestLogout:
    def test_logout_returns_to_login(self, login_page, open_page, test_user_credentials):
        creds = test_user_credentials
        login_page.login(creds["email"], creds["password"])

        open_page("", None)
        login_page.driver.find_element(By.LINK_TEXT, "Выйти").click()
        login_page.wait.until(lambda d: "/login/" in d.current_url)
        assert login_page.is_visible(login_page.EMAIL)
