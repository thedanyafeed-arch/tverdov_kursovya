import pytest


@pytest.mark.e2e
class TestLoginPage:
    def test_login_page_elements(self, login_page):
        assert login_page.is_visible(login_page.EMAIL)
        assert login_page.is_visible(login_page.PASSWORD)
        assert login_page.is_visible(login_page.SUBMIT)

    def test_login_invalid_credentials_shows_api_message(self, login_page):
        login_page.submit_without_wait("nobody@example.com", "WrongPassword1!")
        login_page.wait_for_login_result()
        assert login_page.has_alert_containing("Неверный email или пароль")

    @pytest.mark.parametrize(
        "email,expected",
        [
            ("not-email", "Некорректный email"),
            ("", "Укажите email"),
        ],
    )
    def test_login_invalid_email_field_error(self, login_page, email, expected):
        login_page.submit_without_wait(email, "Password123")
        login_page.wait.until(lambda _: login_page.get_field_errors() or login_page.get_alert_messages())
        assert login_page.has_field_error_containing(expected) or login_page.has_alert_containing(expected)
        assert "/login/" in login_page.driver.current_url

    def test_login_empty_password_field_error(self, login_page):
        login_page.submit_without_wait("user@example.com", "")
        login_page.wait.until(lambda _: login_page.get_field_errors())
        assert login_page.has_field_error_containing("Укажите пароль")

    def test_login_success_redirects_to_catalog(
        self,
        login_page,
        test_user_credentials,
    ):
        creds = test_user_credentials
        login_page.login(creds["email"], creds["password"])
        assert "/catalog/" in login_page.driver.current_url or login_page.has_alert_containing(
            "Вход выполнен"
        )

    def test_login_success_shows_user_in_navbar(
        self,
        login_page,
        test_user_credentials,
    ):
        creds = test_user_credentials
        login_page.login(creds["email"], creds["password"])
        assert login_page.is_logged_in(creds["email"]) or login_page.has_alert_containing(
            "Вход выполнен"
        )
