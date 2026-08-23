"""Urun detay sayfasi - Playwright surumu."""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from config.settings import Settings
from core.base_page import BasePage
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price


class ProductDetailPage(BasePage):
    PAGE_NAME = "ProductDetail"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.header = HeaderComponent(page, settings)
        self.name_label = page.get_by_test_id("inventory-item-name")
        self.description_label = page.get_by_test_id("inventory-item-desc")
        self.price_label = page.get_by_test_id("inventory-item-price")
        self.back_button = page.get_by_test_id("back-to-products")
        self.add_button = page.locator("button[id^='add-to-cart']")
        self.remove_button = page.locator("button[id^='remove']")

    def verify_loaded(self, timeout: int | None = None) -> "ProductDetailPage":
        # to_have_url regex kabul eder; URL'de sorgu parametresi oldugu icin
        # tam esitlik yerine desen kullaniyoruz.
        expect(self.page).to_have_url(re.compile(r"inventory-item\.html"))
        expect(self.name_label).to_be_visible()
        return self

    def name(self) -> str:
        return self.name_label.inner_text().strip()

    def description(self) -> str:
        return self.description_label.inner_text().strip()

    def price(self) -> float:
        return parse_price(self.price_label.inner_text())

    def add_to_cart(self) -> "ProductDetailPage":
        before = self.header.cart_count()
        self.add_button.click()
        expect(self.remove_button).to_be_visible()
        self.header.expect_cart_count(before + 1)
        return self

    def back_to_products(self):
        self.back_button.click()
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page, self.settings).verify_loaded()
