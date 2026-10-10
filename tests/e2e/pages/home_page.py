from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage


class HomePage(BasePage):
    TITLE = (By.CSS_SELECTOR, "h1.display-6")
    CATALOG_LINK = (By.LINK_TEXT, "Перейти в каталог")
    LOGIN_LINK = (By.LINK_TEXT, "Войти")

    def get_title_text(self) -> str:
        return self._find(self.TITLE).text

    def go_to_catalog(self):
        self.click(self.CATALOG_LINK)
        self.wait.until(EC.url_contains("/catalog/"))
        return self

    def go_to_login(self):
        self.click(self.LOGIN_LINK)
        return self
