"""Checkout akisi - Playwright surumu (3 adim = 3 sinif)."""
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page, expect

from config.settings import Settings
from core.base_page import BasePage
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price


class BusinessRuleError(AssertionError):
    """Uygulama is kuralinin ihlali."""


@dataclass(frozen=True)
class CheckoutTotals:
    subtotal: float
    tax: float
    total: float

    def validate(self, tax_rate: float = 0.08, tolerance: float = 0.01) -> None:
        expected_tax = round(self.subtotal * tax_rate, 2)
        if abs(self.tax - expected_tax) > tolerance:
            raise BusinessRuleError(
                f"KDV hatali. Ara toplam={self.subtotal:.2f}, oran={tax_rate}, "
                f"beklenen={expected_tax:.2f}, ekranda={self.tax:.2f}"
            )
        expected_total = round(self.subtotal + self.tax, 2)
        if abs(self.total - expected_total) > tolerance:
            raise BusinessRuleError(
                f"Genel toplam hatali. Beklenen={expected_total:.2f}, "
                f"ekranda={self.total:.2f}"
            )


class CheckoutInformationPage(BasePage):
    """Adim 1: musteri bilgileri."""

    PAGE_NAME = "CheckoutInformation"
    URL_PATH = "/checkout-step-one.html"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.first_name = page.get_by_test_id("firstName")
        self.last_name = page.get_by_test_id("lastName")
        self.postal_code = page.get_by_test_id("postalCode")
        self.continue_button = page.get_by_test_id("continue")
        self.cancel_button = page.get_by_test_id("cancel")
        self.error_message = page.get_by_test_id("error")

    def verify_loaded(self, timeout: int | None = None) -> "CheckoutInformationPage":
        expect(self.page).to_have_url(self.settings.checkout_step_one_url)
        expect(self.first_name).to_be_visible()
        return self

    def fill_form(self, first_name: str, last_name: str, postal_code: str):
        # fill("") alani temizler; Selenium'daki clear()/send_keys ayrimina
        # burada gerek yok - tek metot her iki durumu da karsilar.
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.postal_code.fill(postal_code)
        return self

    def submit(self, first_name: str, last_name: str, postal_code: str):
        """Formu gonderir; sonuca gore ozet sayfasi VEYA kendisini doner."""
        self.fill_form(first_name, last_name, postal_code)
        self.continue_button.click()
        self.page.wait_for_load_state("domcontentloaded")

        if "checkout-step-two.html" in self.page.url:
            return CheckoutOverviewPage(self.page, self.settings).verify_loaded()
        expect(self.error_message).to_be_visible()
        return self

    def expect_error(self, expected: str) -> "CheckoutInformationPage":
        expect(self.error_message).to_have_text(expected)
        return self

    def error_text(self) -> str:
        return self.error_message.inner_text().strip() if self.error_message.count() else ""

    def cancel(self):
        self.cancel_button.click()
        from pages.cart_page import CartPage

        return CartPage(self.page, self.settings).verify_loaded()


class CheckoutOverviewPage(BasePage):
    """Adim 2: siparis ozeti."""

    PAGE_NAME = "CheckoutOverview"
    URL_PATH = "/checkout-step-two.html"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.header = HeaderComponent(page, settings)
        self.cart_items = page.locator(".cart_item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.subtotal_label = page.get_by_test_id("subtotal-label")
        self.tax_label = page.get_by_test_id("tax-label")
        self.total_label = page.get_by_test_id("total-label")
        self.payment_info = page.get_by_test_id("payment-info-value")
        self.shipping_info = page.get_by_test_id("shipping-info-value")
        self.finish_button = page.get_by_test_id("finish")
        self.cancel_button = page.get_by_test_id("cancel")

    def verify_loaded(self, timeout: int | None = None) -> "CheckoutOverviewPage":
        expect(self.page).to_have_url(self.settings.checkout_step_two_url)
        expect(self.finish_button).to_be_visible()
        return self

    def get_item_names(self) -> list[str]:
        return [t.strip() for t in self.item_names.all_text_contents()]

    def get_item_prices(self) -> list[float]:
        return [parse_price(t) for t in self.item_prices.all_text_contents()]

    def totals(self) -> CheckoutTotals:
        return CheckoutTotals(
            subtotal=parse_price(self.subtotal_label.inner_text()),
            tax=parse_price(self.tax_label.inner_text()),
            total=parse_price(self.total_label.inner_text()),
        )

    def finish(self):
        self.finish_button.click()
        return CheckoutCompletePage(self.page, self.settings).verify_loaded()

    def cancel(self):
        self.cancel_button.click()
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page, self.settings).verify_loaded()


class CheckoutCompletePage(BasePage):
    """Adim 3: siparis tamamlandi."""

    PAGE_NAME = "CheckoutComplete"
    URL_PATH = "/checkout-complete.html"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.header = HeaderComponent(page, settings)
        self.complete_header = page.get_by_test_id("complete-header")
        self.complete_text = page.get_by_test_id("complete-text")
        self.pony_image = page.get_by_test_id("pony-express")
        self.back_home_button = page.get_by_test_id("back-to-products")

    def verify_loaded(self, timeout: int | None = None) -> "CheckoutCompletePage":
        expect(self.page).to_have_url(self.settings.checkout_complete_url)
        expect(self.complete_header).to_be_visible()
        return self

    def expect_order_confirmed(self) -> "CheckoutCompletePage":
        expect(self.complete_header).to_have_text("Thank you for your order!")
        expect(self.complete_text).to_contain_text("dispatched")
        expect(self.pony_image).to_be_visible()
        self.header.expect_cart_count(0)
        return self

    def header_text(self) -> str:
        return self.complete_header.inner_text().strip()

    def back_to_products(self):
        self.back_home_button.click()
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page, self.settings).verify_loaded()
