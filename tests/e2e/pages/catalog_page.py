from selenium.webdriver.common.by import By

from .base_page import BasePage


class CatalogPage(BasePage):
    HEADING = (By.CSS_SELECTOR, "h1.h4")
    FILTER_FORM = (By.CSS_SELECTOR, "form[method='get']")
    APPLY_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    PROPERTY_CARDS = (By.CSS_SELECTOR, ".card.h-100")

    def get_heading(self) -> str:
        return self._find(self.HEADING).text

    def property_cards_count(self) -> int:
        return len(self.driver.find_elements(*self.PROPERTY_CARDS))

    def apply_filters(self):
        self.click(self.APPLY_BUTTON)
        return self
