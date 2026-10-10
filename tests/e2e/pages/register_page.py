from selenium.webdriver.common.by import By

from .base_page import BasePage


class RegisterPage(BasePage):
    EMAIL = (By.ID, "id_email")
    PASSWORD = (By.ID, "id_password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    LOGIN_LINK = (By.LINK_TEXT, "Войти")

    def register(self, email: str, password: str):
        self.fill_field(self.EMAIL, email)
        self.fill_field(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self

    def wait_for_feedback(self, timeout: int = 10):
        def _done(_driver) -> bool:
            if "/login/" in _driver.current_url:
                return True
            if self.get_field_errors() or self.get_alert_messages():
                return True
            return False

        self.wait_until(_done, timeout=timeout)
        return self

    def go_to_login(self):
        self.click(self.LOGIN_LINK)
        return self
