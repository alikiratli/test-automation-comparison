"""Urun listesi (envanter) sayfasi."""
from __future__ import annotations

from dataclasses import dataclass

from selenium.webdriver.common.by import By

from core.base_page import BasePage, Locator
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price, slugify_product


@dataclass(frozen=True)
class Product:
    """Sayfadan okunan bir urunun degeri (value object)."""

    name: str
    description: str
    price: float

    def __str__(self) -> str:  # rapor ciktilari icin
        return f"{self.name} (${self.price:.2f})"


class SortOption:
    """Siralama dropdown'inin kabul ettigi degerler."""

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
    URL_FRAGMENT = "inventory.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='inventory-list']")

    INVENTORY_ITEM: Locator = (By.CSS_SELECTOR, ".inventory_item")
    ITEM_NAME: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    ITEM_DESC: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-desc']")
    ITEM_PRICE: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    ITEM_IMAGE: Locator = (By.CSS_SELECTOR, ".inventory_item_img img")
    SORT_DROPDOWN: Locator = (By.CSS_SELECTOR, "[data-test='product-sort-container']")
    ACTIVE_SORT_LABEL: Locator = (By.CSS_SELECTOR, ".active_option")
    PAGE_TITLE: Locator = (By.CSS_SELECTOR, "[data-test='title']")

    def __init__(self, driver, settings) -> None:
        super().__init__(driver, settings)
        # Kompozisyon: header her sayfada ayni sekilde kullanilabilir.
        self.header = HeaderComponent(driver, settings)

    # --- Sorgular ------------------------------------------------------ #
    def product_count(self) -> int:
        return self.count(self.INVENTORY_ITEM)

    def product_names(self) -> list[str]:
        return self.get_texts(self.ITEM_NAME)

    def product_prices(self) -> list[float]:
        return [parse_price(text) for text in self.get_texts(self.ITEM_PRICE)]

    def products(self) -> list[Product]:
        """Tum urunleri tek gecisde okur.

        DIKKAT - PERFORMANS: Her `find_elements` cagrisi ayri bir WebDriver
        HTTP istegidir. 6 urun x 3 alan = 18 istek yerine 3 toplu istek
        yaparak sureyi yaklasik 5 kat kisaltiyoruz. Playwright'ta ayni
        optimizasyon `locator.all_text_contents()` ile yapilir.
        """
        names = self.get_texts(self.ITEM_NAME)
        descriptions = self.get_texts(self.ITEM_DESC)
        prices = self.get_texts(self.ITEM_PRICE)
        return [
            Product(name=n, description=d, price=parse_price(p))
            for n, d, p in zip(names, descriptions, prices)
        ]

    def page_title(self) -> str:
        return self.get_text(self.PAGE_TITLE)

    def active_sort_label(self) -> str:
        return self.get_text(self.ACTIVE_SORT_LABEL)

    def broken_image_count(self) -> int:
        """Yuklenemeyen gorselleri sayar (problem_user senaryosu icin).

        naturalWidth == 0 -> tarayici gorseli indiremedi. Bu bilgi yalnizca
        JavaScript ile alinabilir; saf Selenium API'sinde karsiligi yoktur.
        """
        script = """
            return Array.from(document.querySelectorAll(arguments[0]))
                .filter(img => !img.complete || img.naturalWidth === 0).length;
        """
        return int(self.driver.execute_script(script, ".inventory_item_img img"))

    def distinct_image_sources(self) -> int:
        srcs = [e.get_attribute("src") for e in self.driver.find_elements(*self.ITEM_IMAGE)]
        return len(set(srcs))

    # --- Eylemler ------------------------------------------------------ #
    def sort_by(self, option: str) -> "InventoryPage":
        self.select_by_value(self.SORT_DROPDOWN, option)
        # React listeyi yeniden cizer. Etiket guncellenene kadar bekleyerek
        # eski siralamayi okuma riskini ortadan kaldiriyoruz.
        expected_label = SortOption.LABELS[option]
        self.wait_for(
            lambda d: d.find_element(*self.ACTIVE_SORT_LABEL).text.strip() == expected_label,
            timeout=10,
            state=f"siralama etiketi '{expected_label}'",
            locator=self.ACTIVE_SORT_LABEL,
        )
        return self

    def _add_button(self, product_name: str) -> Locator:
        return (By.CSS_SELECTOR, f"[data-test='add-to-cart-{slugify_product(product_name)}']")

    def _remove_button(self, product_name: str) -> Locator:
        return (By.CSS_SELECTOR, f"[data-test='remove-{slugify_product(product_name)}']")

    def add_to_cart(self, product_name: str) -> "InventoryPage":
        before = self.header.cart_count()
        self.click(self._add_button(product_name))
        # Butonun "Remove"a donmesi, islemin tamamlandiginin en guclu kanitidir.
        self.wait_visible(self._remove_button(product_name), timeout=10)
        self.header.wait_cart_count(before + 1)
        self.log.info("Sepete eklendi: %s", product_name)
        return self

    def remove_from_cart(self, product_name: str) -> "InventoryPage":
        before = self.header.cart_count()
        self.click(self._remove_button(product_name))
        self.wait_visible(self._add_button(product_name), timeout=10)
        self.header.wait_cart_count(max(before - 1, 0))
        self.log.info("Sepetten cikarildi: %s", product_name)
        return self

    def add_many_to_cart(self, product_names: list[str]) -> "InventoryPage":
        for name in product_names:
            self.add_to_cart(name)
        return self

    def is_in_cart(self, product_name: str) -> bool:
        return self.exists(self._remove_button(product_name))

    def open_product_detail(self, product_name: str):
        self.click((By.XPATH, f"//div[text()='{product_name}']"))
        from pages.product_detail_page import ProductDetailPage

        return ProductDetailPage(self.driver, self.settings).verify_loaded()
