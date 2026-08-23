"""Sepet sayfasi."""
from __future__ import annotations

from dataclasses import dataclass

from selenium.webdriver.common.by import By

from core.base_page import BasePage, Locator
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
    URL_FRAGMENT = "cart.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='cart-list']")

    CART_ITEM: Locator = (By.CSS_SELECTOR, ".cart_item")
    ITEM_NAME: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    ITEM_PRICE: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    ITEM_QUANTITY: Locator = (By.CSS_SELECTOR, "[data-test='item-quantity']")
    CHECKOUT_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='checkout']")
    CONTINUE_SHOPPING_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='continue-shopping']")

    def __init__(self, driver, settings) -> None:
        super().__init__(driver, settings)
        self.header = HeaderComponent(driver, settings)

    # --- Sorgular ------------------------------------------------------ #
    def is_empty(self) -> bool:
        return self.count(self.CART_ITEM) == 0

    def item_count(self) -> int:
        return self.count(self.CART_ITEM)

    def item_names(self) -> list[str]:
        return self.get_texts(self.ITEM_NAME) if not self.is_empty() else []

    def lines(self) -> list[CartLine]:
        if self.is_empty():
            return []
        names = self.get_texts(self.ITEM_NAME)
        prices = self.get_texts(self.ITEM_PRICE)
        quantities = self.get_texts(self.ITEM_QUANTITY)
        return [
            CartLine(name=n, price=parse_price(p), quantity=int(q))
            for n, p, q in zip(names, prices, quantities)
        ]

    def subtotal(self) -> float:
        return round(sum(line.line_total for line in self.lines()), 2)

    def contains(self, product_name: str) -> bool:
        return product_name in self.item_names()

    # --- Eylemler ------------------------------------------------------ #
    def open_cart_page(self) -> "CartPage":
        self.open(self.settings.cart_url)
        return self.verify_loaded()

    def remove(self, product_name: str) -> "CartPage":
        locator = (By.CSS_SELECTOR, f"[data-test='remove-{slugify_product(product_name)}']")
        before = self.item_count()
        self.click(locator)
        self.wait_for(
            lambda d: self.count(self.CART_ITEM) == before - 1,
            timeout=10,
            state=f"sepet satiri {before - 1}'e dustu",
        )
        self.log.info("Sepetten silindi: %s", product_name)
        return self

    def remove_all(self) -> "CartPage":
        # Listeyi geriye dogru islemek, DOM yeniden ciziminde indeks kaymasini
        # engeller. Ileri dogru donmek klasik bir "stale element" tuzagidir.
        for name in reversed(self.item_names()):
            self.remove(name)
        return self

    def proceed_to_checkout(self):
        self.click(self.CHECKOUT_BUTTON)
        from pages.checkout_page import CheckoutInformationPage

        return CheckoutInformationPage(self.driver, self.settings).verify_loaded()

    def continue_shopping(self):
        self.click(self.CONTINUE_SHOPPING_BUTTON)
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.driver, self.settings).verify_loaded()
