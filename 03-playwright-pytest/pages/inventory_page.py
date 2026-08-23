"""Urun listesi sayfasi - Playwright surumu."""
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page, expect

from config.settings import Settings
from core.base_page import BasePage
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price, slugify_product


@dataclass(frozen=True)
class Product:
    name: str
    description: str
    price: float

    def __str__(self) -> str:
        return f"{self.name} (${self.price:.2f})"


class SortOption:
    NAME_A_TO_Z = "az"
    NAME_Z_TO_A = "za"
    PRICE_LOW_TO_HIGH = "lohi"
    PRICE_HIGH_TO_LOW = "hilo"

    LABELS = {
        NAME_A_TO_Z: "Name (A to Z)",
        NAME_Z_TO_A: "Name (Z to A)",
        PRICE_LOW_TO_HIGH: "Price (low to high)",
        PRICE_HIGH_TO_LOW: "Price (high to low)",
    }


class InventoryPage(BasePage):
    PAGE_NAME = "Inventory"
    URL_PATH = "/inventory.html"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.header = HeaderComponent(page, settings)
        self.inventory_list = page.get_by_test_id("inventory-list")
        self.items = page.locator(".inventory_item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_descriptions = page.get_by_test_id("inventory-item-desc")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.item_images = page.locator(".inventory_item_img img")
        self.sort_dropdown = page.get_by_test_id("product-sort-container")
        self.active_sort_label = page.locator(".active_option")
        self.page_title = page.get_by_test_id("title")

    def verify_loaded(self, timeout: int | None = None) -> "InventoryPage":
        expect(self.page).to_have_url(self.settings.inventory_url)
        expect(self.inventory_list).to_be_visible()
        return self

    # --- Sorgular ------------------------------------------------------ #
    def product_count(self) -> int:
        return self.items.count()

    def get_product_names(self) -> list[str]:
        return [t.strip() for t in self.item_names.all_text_contents()]

    def get_product_prices(self) -> list[float]:
        return [parse_price(t) for t in self.item_prices.all_text_contents()]

    def get_products(self) -> list[Product]:
        """Tum urunleri okur.

        `all_text_contents()` tek IPC cagrisiyla TUM eslesmeleri doner.
        Selenium'da her eleman icin ayri bir HTTP istegi gerekir; bu, ayni
        islemde Playwright'in belirgin sekilde hizli olmasinin sebeplerinden
        biridir.
        """
        names = [t.strip() for t in self.item_names.all_text_contents()]
        descriptions = [t.strip() for t in self.item_descriptions.all_text_contents()]
        prices = [parse_price(t) for t in self.item_prices.all_text_contents()]
        return [
            Product(name=n, description=d, price=p)
            for n, d, p in zip(names, descriptions, prices)
        ]

    def get_active_sort_label(self) -> str:
        return self.active_sort_label.inner_text().strip()

    def broken_image_count(self) -> int:
        """Yuklenemeyen gorselleri sayar."""
        return self.page.evaluate(
            """() => Array.from(document.querySelectorAll('.inventory_item_img img'))
                   .filter(img => !img.complete || img.naturalWidth === 0).length"""
        )

    def distinct_image_sources(self) -> int:
        sources = self.item_images.evaluate_all("nodes => nodes.map(n => n.src)")
        return len(set(sources))

    # --- Eylemler ------------------------------------------------------ #
    def sort_by(self, option: str) -> "InventoryPage":
        self.sort_dropdown.select_option(option)
        # Etiketin guncellenmesini bekle -> eski siralamayi okuma riski yok
        expect(self.active_sort_label).to_have_text(SortOption.LABELS[option])
        return self

    def _add_button(self, product_name: str) -> Locator:
        return self.page.get_by_test_id(f"add-to-cart-{slugify_product(product_name)}")

    def _remove_button(self, product_name: str) -> Locator:
        return self.page.get_by_test_id(f"remove-{slugify_product(product_name)}")

    def add_to_cart(self, product_name: str) -> "InventoryPage":
        before = self.header.cart_count()
        self._add_button(product_name).click()
        expect(self._remove_button(product_name)).to_be_visible()
        self.header.expect_cart_count(before + 1)
        self.log.info("Sepete eklendi: %s", product_name)
        return self

    def remove_from_cart(self, product_name: str) -> "InventoryPage":
        before = self.header.cart_count()
        self._remove_button(product_name).click()
        expect(self._add_button(product_name)).to_be_visible()
        self.header.expect_cart_count(max(before - 1, 0))
        return self

    def add_many_to_cart(self, product_names: list[str]) -> "InventoryPage":
        for name in product_names:
            self.add_to_cart(name)
        return self

    def is_in_cart(self, product_name: str) -> bool:
        return self._remove_button(product_name).count() > 0

    def expect_in_cart(self, product_name: str) -> "InventoryPage":
        expect(self._remove_button(product_name)).to_be_visible()
        return self

    def expect_not_in_cart(self, product_name: str) -> "InventoryPage":
        expect(self._add_button(product_name)).to_be_visible()
        return self

    def open_product_detail(self, product_name: str):
        # get_by_text: kullanicinin GORDUGU metne gore secim.
        # Playwright, kullanici odakli locator'lari (get_by_role, get_by_text,
        # get_by_label) tesvik eder; bunlar CSS/XPath'e gore kirilmaya daha
        # dayaniklidir cunku sayfanin yapisina degil ANLAMINA baglidirlar.
        self.page.get_by_text(product_name, exact=True).first.click()
        from pages.product_detail_page import ProductDetailPage

        return ProductDetailPage(self.page, self.settings).verify_loaded()
