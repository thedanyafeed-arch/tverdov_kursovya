from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    EMAIL = (By.ID, "id_email")
    PASSWORD = (By.ID, "id_password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    REGISTER_LINK = (By.LINK_TEXT, "Регистрация")

    def enter_email(self, email: str):
        return self.fill_field(self.EMAIL, email)

    def enter_password(self, password: str):
        return self.fill_field(self.PASSWORD, password)

    def submit(self):
        self.click(self.SUBMIT)
        return self

    def wait_for_login_result(self, email: str | None = None, timeout: int = 20):
        """Ждём редирект в каталог, email в шапке или сообщение об ошибке/успехе."""

        def _done(driver) -> bool:
            if "/catalog/" in driver.current_url or "/account/" in driver.current_url:
                return True
            if email and email in driver.page_source:
                return True
            for alert in driver.find_elements(By.CSS_SELECTOR, ".alert"):
                text = alert.text
                if any(
                    part in text
                    for part in (
                        "Вход выполнен",
                        "Неверный email или пароль",
                        "Некорректный email",
                        "уже существует",
                    )
                ):
                    return True
            if driver.find_elements(By.CSS_SELECTOR, ".field-error"):
                return True
            return False

        self.wait_until(_done, timeout=timeout, message="Нет ответа после входа (проверьте API и pytest_user@example.com)")
        return self

    def login(self, email: str, password: str, *, wait: bool = True):
        self.enter_email(email)
        self.enter_password(password)
        self.submit()
        if wait:
            self.wait_for_login_result(email)
        return self

    def submit_without_wait(self, email: str, password: str):
        self.enter_email(email)
        self.enter_password(password)
        self.submit()
        return self

    def is_logged_in(self, email: str) -> bool:
        return email in self.driver.page_source and "/login/" not in self.driver.current_url

    def go_to_register(self):
        self.click(self.REGISTER_LINK)
        return self
