from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Callable


class BasePage:
    """Базовый Page Object для Django UI."""

    def __init__(self, driver: WebDriver, timeout: int = 15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def wait_for_page_load(self):
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return self

    def _find(self, locator: tuple[str, str], timeout: int | None = None):
        return WebDriverWait(self.driver, timeout or 10).until(
            EC.visibility_of_element_located(locator)
        )

    def _clickable(self, locator: tuple[str, str], timeout: int | None = None):
        return WebDriverWait(self.driver, timeout or 10).until(
            EC.element_to_be_clickable(locator)
        )

    def fill_field(self, locator: tuple[str, str], value: str):
        field = self._find(locator)
        field.clear()
        field.send_keys(value)
        return self

    def click(self, locator: tuple[str, str]):
        self._clickable(locator).click()
        return self

    def is_visible(self, locator: tuple[str, str], timeout: int = 5) -> bool:
        try:
            self._find(locator, timeout=timeout)
            return True
        except TimeoutException:
            return False

    def get_alert_messages(self) -> list[str]:
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert")
        return [el.text.strip() for el in elements if el.text.strip()]

    def has_alert_containing(self, text: str) -> bool:
        return any(text in msg for msg in self.get_alert_messages())

    def get_field_errors(self) -> list[str]:
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".field-error")
        return [el.text.strip() for el in elements if el.text.strip()]

    def has_field_error_containing(self, text: str) -> bool:
        return any(text in err for err in self.get_field_errors())

    def page_contains(self, text: str) -> bool:
        return text in self.driver.page_source

    def wait_until(self, predicate: Callable, timeout: int | None = None, message: str = ""):
        WebDriverWait(self.driver, timeout or 15).until(predicate, message=message)
