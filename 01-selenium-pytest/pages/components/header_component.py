"""Ust bar (header) bileseni.

KARSILASTIRMA NOTU - COMPONENT OBJECT DESENI:
    Header her sayfada bulunur. Onu her Page Object'e kopyalamak yerine ayri
    bir "component object" yapip kompozisyonla eklemek, POM'un olceklenebilir
    halidir. Robot Framework'te ayni sey `resources/pages/common.resource`
    icindeki paylasilan keyword'lerle, Playwright'ta ise component-locator
    fonksiyonlariyla yapilir.
"""
from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.base_page import BasePage, Locator


class HeaderComponent(BasePage):
    PAGE_NAME = "Header"

    CART_LINK: Locator = (By.CSS_SELECTOR, "[data-test='shopping-cart-link']")
    CART_BADGE: Locator = (By.CSS_SELECTOR, "[data-test='shopping-cart-badge']")
    BURGER_BUTTON: Locator = (By.ID, "react-burger-menu-btn")
    MENU_WRAP: Locator = (By.CSS_SELECTOR, ".bm-menu-wrap")
    CLOSE_MENU_BUTTON: Locator = (By.ID, "react-burger-cross-btn")
    LOGOUT_LINK: Locator = (By.ID, "logout_sidebar_link")
    ALL_ITEMS_LINK: Locator = (By.ID, "inventory_sidebar_link")
    ABOUT_LINK: Locator = (By.ID, "about_sidebar_link")
    RESET_APP_LINK: Locator = (By.ID, "reset_sidebar_link")
    APP_LOGO: Locator = (By.CSS_SELECTOR, ".app_logo")

    # --- Sepet --------------------------------------------------------- #
    def cart_count(self) -> int:
        """Sepet rozetindeki sayiyi doner; rozet yoksa 0.

        Rozet React ile sonradan basildigi icin dogrudan `.text` okumak yaris
        durumu (race condition) yaratir. `element_has_stable_text` kosulu ayni
        degeri ust uste iki kez gorene kadar bekleyerek bunu engeller.
        """
        if not self.exists(self.CART_BADGE):
            return 0
        from core.waits import element_has_stable_text

        value = self.wait_for(
            element_has_stable_text(self.CART_BADGE),
            timeout=5,
            state="sepet rozeti kararli",
            locator=self.CART_BADGE,
        )
        return int(value)

    def wait_cart_count(self, expected: int, timeout: float = 10) -> None:
        if expected == 0:
            self.wait_invisible(self.CART_BADGE, timeout)
            return
        self.wait_for(
            lambda d: self.exists(self.CART_BADGE)
            and d.find_element(*self.CART_BADGE).text.strip() == str(expected),
            timeout=timeout,
            state=f"sepet rozeti = {expected}",
            locator=self.CART_BADGE,
        )

    def open_cart(self):
        self.click(self.CART_LINK)
        from pages.cart_page import CartPage

        return CartPage(self.driver, self.settings).verify_loaded()

    # --- Yan menu ------------------------------------------------------ #
    MENU_ITEM = (By.CSS_SELECTOR, ".bm-item.menu-item")

    def open_menu(self) -> "HeaderComponent":
        self.click(self.BURGER_BUTTON)
        # Menu sagdan kayarak acilir. aria-hidden niteligi animasyon BASLARKEN
        # 'false' olur - yani "acilmaya basladi" demektir, "acildi" demek degil.
        self.wait_for(
            lambda d: d.find_element(*self.MENU_WRAP).get_attribute("aria-hidden") == "false",
            timeout=10,
            state="yan menu acilmaya basladi",
            locator=self.MENU_WRAP,
        )
        # GERCEK BIR SORUNUN COZUMU:
        #   Yalnizca aria-hidden beklendiginde menu ogelerinin metinleri
        #   ['', '', 'Logout', 'Reset App State'] olarak okunuyordu. Sebep:
        #   Selenium, viewport disindaki (henuz kaymasi bitmemis) elemanlar
        #   icin `.text` degerini BOS doner. Animasyonun gercekten bittigini
        #   anlamanin guvenilir yolu, tum ogelerin metninin dolmasini beklemek.
        #
        #   KARSILASTIRMA: Playwright'ta `expect(locator).to_be_visible()`
        #   ve click, elemanin konumunun sabitlenmesini zaten bekler; bu ek
        #   kontrole ihtiyac duyulmaz.
        self.wait_for(
            lambda d: all(
                e.text.strip() for e in d.find_elements(*self.MENU_ITEM)
            )
            and len(d.find_elements(*self.MENU_ITEM)) >= 4,
            timeout=10,
            state="menu ogeleri tamamen goruntulendi",
            locator=self.MENU_ITEM,
        )
        return self

    def close_menu(self) -> "HeaderComponent":
        self.click(self.CLOSE_MENU_BUTTON)
        self.wait_for(
            lambda d: d.find_element(*self.MENU_WRAP).get_attribute("aria-hidden") == "true",
            timeout=10,
            state="yan menu kapanmaya basladi",
            locator=self.MENU_WRAP,
        )
        # Kapanma animasyonu da bitene kadar bekle: menu ogeleri gorunmez olmali.
        self.wait_for(
            EC.invisibility_of_element_located(self.LOGOUT_LINK),
            timeout=10,
            state="menu tamamen kapandi",
            locator=self.LOGOUT_LINK,
        )
        return self

    def logout(self):
        self.open_menu()
        self.click(self.LOGOUT_LINK)
        from pages.login_page import LoginPage

        return LoginPage(self.driver, self.settings).verify_loaded()

    def reset_app_state(self) -> "HeaderComponent":
        """Sepeti ve uygulama durumunu sifirlar (test izolasyonu icin)."""
        self.open_menu()
        self.click(self.RESET_APP_LINK)
        self.close_menu()
        # SauceDemo'da 'Reset App State' rozeti DOM'dan silmez; sayfa
        # yenilendiginde temizlenir. Bu, uygulamanin bilinen bir davranisidir.
        self.driver.refresh()
        self.wait_document_ready()
        return self

    def menu_items(self) -> list[str]:
        self.open_menu()
        items = self.get_texts(self.MENU_ITEM)
        self.close_menu()
        return items
