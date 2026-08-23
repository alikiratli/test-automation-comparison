"""Ust bar bileseni - Playwright surumu."""
from __future__ import annotations

from playwright.sync_api import Page, expect

from config.settings import Settings
from core.base_page import BasePage


class HeaderComponent(BasePage):
    PAGE_NAME = "Header"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.burger_button = page.locator("#react-burger-menu-btn")
        self.close_menu_button = page.locator("#react-burger-cross-btn")
        self.menu_wrap = page.locator(".bm-menu-wrap")
        self.logout_link = page.locator("#logout_sidebar_link")
        self.all_items_link = page.locator("#inventory_sidebar_link")
        self.reset_link = page.locator("#reset_sidebar_link")
        self.app_logo = page.locator(".app_logo")
        self.menu_items = page.locator(".bm-item.menu-item")

    # --- Sepet --------------------------------------------------------- #
    def cart_count(self) -> int:
        """Sepet rozetindeki sayi; rozet yoksa 0.

        SELENIUM ILE FARK:
            Selenium surumunde bu metot, React'in rozeti asenkron guncellemesi
            yuzunden 'metin ust uste iki kez ayni kalsin' seklinde OZEL BIR
            BEKLEME KOSULU (core/waits.py::element_has_stable_text) kullaniyordu.
            Playwright'ta `count()` ve `inner_text()` zaten locator'i o an
            yeniden cozdugu, `expect_cart_count` de tekrar denedigi icin
            o mekanizmaya gerek kalmadi.
        """
        if self.cart_badge.count() == 0:
            return 0
        return int(self.cart_badge.inner_text().strip())

    def expect_cart_count(self, expected: int) -> "HeaderComponent":
        """Rozet beklenen degere ULASANA KADAR tekrar dener."""
        if expected == 0:
            expect(self.cart_badge).to_have_count(0)
        else:
            expect(self.cart_badge).to_have_text(str(expected))
        return self

    def open_cart(self):
        self.cart_link.click()
        from pages.cart_page import CartPage

        return CartPage(self.page, self.settings).verify_loaded()

    # --- Yan menu ------------------------------------------------------ #
    def open_menu(self) -> "HeaderComponent":
        """Menuyu acar.

        SELENIUM ILE FARK:
            Selenium surumunde animasyon bitene kadar aria-hidden='false'
            beklemek ZORUNLUYDU; aksi halde 'element not interactable' hatasi
            aliniyordu. Playwright'in "actionability" kontrolu elemanin
            KONUMUNUN SABITLENMESINI de bekledigi icin ek bir onlem gerekmez.
            Yine de niyeti acikca belirtmek adina dogrulamayi biraktik.
        """
        self.burger_button.click()
        expect(self.logout_link).to_be_visible()
        return self

    def close_menu(self) -> "HeaderComponent":
        self.close_menu_button.click()
        expect(self.logout_link).not_to_be_visible()
        return self

    def logout(self):
        self.open_menu()
        self.logout_link.click()
        from pages.login_page import LoginPage

        return LoginPage(self.page, self.settings)

    def reset_app_state(self) -> "HeaderComponent":
        self.open_menu()
        self.reset_link.click()
        self.close_menu()
        self.page.reload()
        return self

    def get_menu_items(self) -> list[str]:
        self.open_menu()
        # all_text_contents(): tum eslesmelerin metnini TEK CAGRIDA doner.
        # Selenium'da bunun icin find_elements + dongü gerekir.
        items = [text.strip() for text in self.menu_items.all_text_contents()]
        self.close_menu()
        return items
