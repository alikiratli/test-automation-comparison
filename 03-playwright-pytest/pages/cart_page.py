"""Sepet sayfasi - Playwright surumu."""
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page, expect

from config.settings import Settings
from core.base_page import BasePage
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price, slugify_product


@dataclass(frozen=True)
class CartLine:
    name: str
    price: float
    quantity: int

    @property
    def line_total(self) -> float:
        return round(self.price * self.quantity, 2)


class CartPage(BasePage):
    PAGE_NAME = "Cart"
    URL_PATH = "/cart.html"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.header = HeaderComponent(page, settings)
        self.cart_list = page.get_by_test_id("cart-list")
        self.cart_items = page.locator(".cart_item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.item_quantities = page.get_by_test_id("item-quantity")
        self.checkout_button = page.get_by_test_id("checkout")
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")

    def verify_loaded(self, timeout: int | None = None) -> "CartPage":
        expect(self.page).to_have_url(self.settings.cart_url)
        expect(self.cart_list).to_be_visible()
        return self

    def open_cart_page(self) -> "CartPage":
        self.navigate(self.settings.cart_url)
        return self.verify_loaded()

    # --- Sorgular ------------------------------------------------------ #
    def item_count(self) -> int:
        return self.cart_items.count()

    def is_empty(self) -> bool:
        return self.item_count() == 0

    def get_item_names(self) -> list[str]:
        return [t.strip() for t in self.item_names.all_text_contents()]

    def lines(self) -> list[CartLine]:
        if self.is_empty():
            return []
        names = [t.strip() for t in self.item_names.all_text_contents()]
        prices = [parse_price(t) for t in self.item_prices.all_text_contents()]
        quantities = [int(t.strip()) for t in self.item_quantities.all_text_contents()]
        return [
            CartLine(name=n, price=p, quantity=q)
            for n, p, q in zip(names, prices, quantities)
        ]

    def subtotal(self) -> float:
        return round(sum(line.line_total for line in self.lines()), 2)

    def contains(self, product_name: str) -> bool:
        return product_name in self.get_item_names()

    # --- Dogrulamalar -------------------------------------------------- #
    def expect_item_count(self, expected: int) -> "CartPage":
        expect(self.cart_items).to_have_count(expected)
        return self

    def expect_contains(self, product_name: str) -> "CartPage":
        expect(self.item_names.filter(has_text=product_name)).to_have_count(1)
        return self

    def expect_empty(self) -> "CartPage":
        expect(self.cart_items).to_have_count(0)
        return self

    # --- Eylemler ------------------------------------------------------ #
    def remove(self, product_name: str) -> "CartPage":
        before = self.item_count()
        self.page.get_by_test_id(f"remove-{slugify_product(product_name)}").click()
        expect(self.cart_items).to_have_count(before - 1)
        return self

    def remove_all(self) -> "CartPage":
        for name in reversed(self.get_item_names()):
            self.remove(name)
        return self

    def proceed_to_checkout(self):
        self.checkout_button.click()
        from pages.checkout_page import CheckoutInformationPage

        return CheckoutInformationPage(self.page, self.settings).verify_loaded()

    def continue_shopping(self):
        self.continue_shopping_button.click()
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page, self.settings).verify_loaded()
