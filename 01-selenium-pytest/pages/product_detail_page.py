"""Tek urun detay sayfasi."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from core.base_page import BasePage, Locator
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price


class ProductDetailPage(BasePage):
    PAGE_NAME = "ProductDetail"
    URL_FRAGMENT = "inventory-item.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")

    NAME: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    DESCRIPTION: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-desc']")
    PRICE: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    BACK_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='back-to-products']")
    ADD_BUTTON: Locator = (By.CSS_SELECTOR, "button[id^='add-to-cart']")
    REMOVE_BUTTON: Locator = (By.CSS_SELECTOR, "button[id^='remove']")

    def __init__(self, driver, settings) -> None:
        super().__init__(driver, settings)
        self.header = HeaderComponent(driver, settings)

    def name(self) -> str:
        return self.get_text(self.NAME)

    def description(self) -> str:
        return self.get_text(self.DESCRIPTION)

    def price(self) -> float:
        return parse_price(self.get_text(self.PRICE))

    def add_to_cart(self) -> "ProductDetailPage":
        before = self.header.cart_count()
        self.click(self.ADD_BUTTON)
        self.wait_visible(self.REMOVE_BUTTON, timeout=10)
        self.header.wait_cart_count(before + 1)
        return self

    def back_to_products(self):
        self.click(self.BACK_BUTTON)
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.driver, self.settings).verify_loaded()
