"""Checkout akisinin uc adimi.

SauceDemo checkout'u 3 sayfadir:
    1. checkout-step-one.html  -> musteri bilgileri formu
    2. checkout-step-two.html  -> ozet + tutarlar
    3. checkout-complete.html  -> tesekkur ekrani

Her adim ayri bir Page Object; adimlar birbirine "gecis metotlariyla" baglanir.
Bu, POM'un akis (flow) modellemesi icin onerilen bicimidir.
"""
from __future__ import annotations

from dataclasses import dataclass

from selenium.webdriver.common.by import By

from core.base_page import BasePage, Locator
from core.exceptions import BusinessRuleError
from pages.components.header_component import HeaderComponent
from utils.parsers import parse_price


@dataclass(frozen=True)
class CheckoutTotals:
    subtotal: float
    tax: float
    total: float

    def validate(self, tax_rate: float = 0.08, tolerance: float = 0.01) -> None:
        """Uygulamanin hesap dogrulugunu kontrol eder.

        Bu bir UI kontrolu degil, IS KURALI kontroludur. Otomasyonun asil
        degeri de buradadir: 'buton tiklandi mi' degil, 'hesap dogru mu'.
        """
        expected_tax = round(self.subtotal * tax_rate, 2)
        if abs(self.tax - expected_tax) > tolerance:
            raise BusinessRuleError(
                f"KDV hatali. Ara toplam={self.subtotal:.2f}, oran={tax_rate}, "
                f"beklenen KDV={expected_tax:.2f}, ekranda={self.tax:.2f}"
            )
        expected_total = round(self.subtotal + self.tax, 2)
        if abs(self.total - expected_total) > tolerance:
            raise BusinessRuleError(
                f"Genel toplam hatali. Beklenen={expected_total:.2f}, ekranda={self.total:.2f}"
            )


class CheckoutInformationPage(BasePage):
    """Adim 1: musteri bilgileri."""

    PAGE_NAME = "CheckoutInformation"
    URL_FRAGMENT = "checkout-step-one.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='firstName']")

    FIRST_NAME: Locator = (By.CSS_SELECTOR, "[data-test='firstName']")
    LAST_NAME: Locator = (By.CSS_SELECTOR, "[data-test='lastName']")
    POSTAL_CODE: Locator = (By.CSS_SELECTOR, "[data-test='postalCode']")
    CONTINUE_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='continue']")
    CANCEL_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='cancel']")
    ERROR_MESSAGE: Locator = (By.CSS_SELECTOR, "[data-test='error']")

    def fill(self, first_name: str, last_name: str, postal_code: str):
        self.log.info("Checkout formu dolduruluyor: %s %s / %s", first_name, last_name, postal_code)
        for locator, value in (
            (self.FIRST_NAME, first_name),
            (self.LAST_NAME, last_name),
            (self.POSTAL_CODE, postal_code),
        ):
            if value:
                self.type_text(locator, value)
            else:
                self.wait_visible(locator).clear()
        return self

    def continue_to_overview(self):
        self.click(self.CONTINUE_BUTTON)
        return CheckoutOverviewPage(self.driver, self.settings).verify_loaded()

    def continue_expecting_error(self) -> str:
        """Hatali formda 'Continue' -> hata mesajini doner."""
        self.click(self.CONTINUE_BUTTON)
        return self.get_text(self.ERROR_MESSAGE)

    def submit(self, first_name: str, last_name: str, postal_code: str):
        """Formu doldurup gonderir; sonuca gore sayfa VEYA hata mesaji doner."""
        self.fill(first_name, last_name, postal_code)
        self.click(self.CONTINUE_BUTTON)
        self.wait_for(
            lambda d: "checkout-step-two.html" in d.current_url
            or self.exists(self.ERROR_MESSAGE),
            timeout=self.timeout,
            state="form sonucu belirlendi",
        )
        if "checkout-step-two.html" in self.current_url:
            return CheckoutOverviewPage(self.driver, self.settings).verify_loaded()
        return self

    def error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE) if self.exists(self.ERROR_MESSAGE) else ""

    def cancel(self):
        self.click(self.CANCEL_BUTTON)
        from pages.cart_page import CartPage

        return CartPage(self.driver, self.settings).verify_loaded()


class CheckoutOverviewPage(BasePage):
    """Adim 2: siparis ozeti ve tutarlar."""

    PAGE_NAME = "CheckoutOverview"
    URL_FRAGMENT = "checkout-step-two.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='finish']")

    CART_ITEM: Locator = (By.CSS_SELECTOR, ".cart_item")
    ITEM_NAME: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    ITEM_PRICE: Locator = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    SUBTOTAL_LABEL: Locator = (By.CSS_SELECTOR, "[data-test='subtotal-label']")
    TAX_LABEL: Locator = (By.CSS_SELECTOR, "[data-test='tax-label']")
    TOTAL_LABEL: Locator = (By.CSS_SELECTOR, "[data-test='total-label']")
    PAYMENT_INFO: Locator = (By.CSS_SELECTOR, "[data-test='payment-info-value']")
    SHIPPING_INFO: Locator = (By.CSS_SELECTOR, "[data-test='shipping-info-value']")
    FINISH_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='finish']")
    CANCEL_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='cancel']")

    def __init__(self, driver, settings) -> None:
        super().__init__(driver, settings)
        self.header = HeaderComponent(driver, settings)

    def item_names(self) -> list[str]:
        return self.get_texts(self.ITEM_NAME)

    def item_prices(self) -> list[float]:
        return [parse_price(t) for t in self.get_texts(self.ITEM_PRICE)]

    def totals(self) -> CheckoutTotals:
        """Ekrandaki 'Item total / Tax / Total' degerlerini sayiya cevirir."""
        return CheckoutTotals(
            subtotal=parse_price(self.get_text(self.SUBTOTAL_LABEL)),
            tax=parse_price(self.get_text(self.TAX_LABEL)),
            total=parse_price(self.get_text(self.TOTAL_LABEL)),
        )

    def payment_information(self) -> str:
        return self.get_text(self.PAYMENT_INFO)

    def shipping_information(self) -> str:
        return self.get_text(self.SHIPPING_INFO)

    def finish(self):
        self.click(self.FINISH_BUTTON)
        return CheckoutCompletePage(self.driver, self.settings).verify_loaded()

    def cancel(self):
        self.click(self.CANCEL_BUTTON)
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.driver, self.settings).verify_loaded()


class CheckoutCompletePage(BasePage):
    """Adim 3: siparis tamamlandi."""

    PAGE_NAME = "CheckoutComplete"
    URL_FRAGMENT = "checkout-complete.html"
    UNIQUE_LOCATOR: Locator = (By.CSS_SELECTOR, "[data-test='complete-header']")

    HEADER: Locator = (By.CSS_SELECTOR, "[data-test='complete-header']")
    TEXT: Locator = (By.CSS_SELECTOR, "[data-test='complete-text']")
    PONY_IMAGE: Locator = (By.CSS_SELECTOR, "[data-test='pony-express']")
    BACK_HOME_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='back-to-products']")

    def __init__(self, driver, settings) -> None:
        super().__init__(driver, settings)
        self.header = HeaderComponent(driver, settings)

    def confirmation_header(self) -> str:
        return self.get_text(self.HEADER)

    def confirmation_text(self) -> str:
        return self.get_text(self.TEXT)

    def is_success_image_visible(self) -> bool:
        return self.is_visible(self.PONY_IMAGE, timeout=5)

    def back_to_products(self):
        self.click(self.BACK_HOME_BUTTON)
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.driver, self.settings).verify_loaded()
