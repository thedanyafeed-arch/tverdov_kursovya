import pytest


@pytest.mark.e2e
class TestRegistrationPage:
    def test_register_page_elements(self, register_page):
        assert register_page.is_visible(register_page.EMAIL)
        assert register_page.is_visible(register_page.PASSWORD)

    def test_register_new_user_success_message(self, register_page, get_faker_email):
        email = get_faker_email
        register_page.register(email, "Password123")
        register_page.wait_for_feedback()
        assert register_page.has_alert_containing("создан") or "/login/" in register_page.driver.current_url

    def test_register_invalid_email_field_error(self, register_page):
        register_page.register("not-email", "Password123")
        register_page.wait_for_feedback()
        assert register_page.has_field_error_containing("Некорректный email")

    @pytest.mark.parametrize(
        "password,expected",
        [
            ("123", "минимум 6"),
            ("", "Укажите пароль"),
        ],
    )
    def test_register_weak_password_field_error(self, register_page, get_faker_email, password, expected):
        register_page.register(get_faker_email, password)
        register_page.wait_for_feedback()
        assert register_page.has_field_error_containing(expected)

    def test_register_duplicate_email_api_message(self, register_page, test_user_credentials):
        creds = test_user_credentials
        register_page.register(creds["email"], creds["password"])
        register_page.wait_for_feedback()
        assert (
            register_page.has_alert_containing("уже существует")
            or register_page.has_field_error_containing("email")
        )

    def test_navigate_to_login(self, register_page, login_page):
        register_page.go_to_login()
        assert login_page.is_visible(login_page.EMAIL)
