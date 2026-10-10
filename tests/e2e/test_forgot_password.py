import pytest


@pytest.mark.e2e
class TestForgotPasswordPage:
    def test_forgot_password_page(self, open_page):
        from tests.e2e.pages.base_page import BasePage

        page = open_page("forgot-password/", BasePage)
        assert page.page_contains("Восстановление пароля")
        assert page.page_contains("Сменить пароль в профиле")
