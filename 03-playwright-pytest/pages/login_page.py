"""Login sayfasi - Playwright surumu.

SELENIUM SURUMUYLE KARSILASTIRIN (01-selenium-pytest/pages/login_page.py):

    Selenium:  USERNAME_INPUT = (By.CSS_SELECTOR, "[data-test='username']")
               -> tuple, driver'a verilmesi gereken pasif veri

    Playwright: self.username_input = page.get_by_test_id("username")
               -> Locator nesnesi; kendi basina tiklanabilir, beklenebilir,
                  dogrulanabilir. "Ne yapacagini bilen" bir nesne.
"""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from config.settings import Settings
from core.base_page import BasePage


class LoginPage(BasePage):
    PAGE_NAME = "Login"
    URL_PATH = "/"

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        # Locator'lar __init__ icinde kurulur ama DOM'A HENUZ DOKUNMAZ.
        # Tembel (lazy) yapilari sayesinde sayfa yuklenmeden de tanimlanabilirler.
        self.username_input = page.get_by_test_id("username")
        self.password_input = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error_message = page.get_by_test_id("error")
        self.error_close_button = page.locator(".error-button")
        self.login_logo = page.locator(".login_logo")
        self.credentials_box = page.locator("#login_credentials")

    # --- Eylemler ------------------------------------------------------ #
    def open_login_page(self) -> "LoginPage":
        self.navigate(self.settings.login_url)
        expect(self.login_button).to_be_visible()
        return self

    def fill_credentials(self, username: str, password: str) -> "LoginPage":
        # fill() alani once temizler, sonra yazar - Selenium'daki
        # clear() + send_keys() ikilisini tek cagriya indirir.
        self.username_input.fill(username)
        self.password_input.fill(password)
        return self

    def submit(self) -> None:
        self.login_button.click()

    def login(self, username: str, password: str):
        """Giris yapar ve ULASILAN sayfanin objesini doner."""
        self.log.info("Giris denemesi: '%s'", username)
        self.fill_credentials(username, password)

        # expect_navigation yerine "yarisan bekleme" kuruyoruz: ya envanter
        # sayfasi acilir ya da hata mesaji cikar. Selenium'da ayni sey ozel
        # bir lambda + WebDriverWait ile yazilmisti.
        self.submit()
        self.page.wait_for_load_state("domcontentloaded")

        from pages.inventory_page import InventoryPage

        if "inventory.html" in self.page.url:
            self.log.info("Giris basarili")
            return InventoryPage(self.page, self.settings).verify_loaded()

        expect(self.error_message).to_be_visible()
        self.log.info("Giris reddedildi")
        return self

    def login_expecting_success(self, username: str, password: str):
        page = self.login(username, password)
        if isinstance(page, LoginPage):
            raise AssertionError(
                f"'{username}' ile giris basarisiz: {self.error_message.inner_text()}"
            )
        return page

    def dismiss_error(self) -> "LoginPage":
        self.error_close_button.click()
        expect(self.error_message).not_to_be_visible()
        return self

    # --- Dogrulamalar (web-first assertions) --------------------------- #
    def expect_error(self, expected_text: str) -> "LoginPage":
        """Hata mesajini TEKRAR DENEYEREK dogrular.

        `expect(...)` kosul saglanana kadar (varsayilan 5sn) yeniden dener.
        Selenium'da bunun icin once WebDriverWait, sonra assert yazmak
        gerekirdi - iki ayri adim.
        """
        expect(self.error_message).to_have_text(expected_text)
        return self

    def expect_still_on_login_page(self) -> "LoginPage":
        expect(self.page).not_to_have_url(self.settings.inventory_url)
        expect(self.login_button).to_be_visible()
        return self

    def expect_field_marked_invalid(self, field_name: str) -> "LoginPage":
        """Hatali alan 'error' CSS sinifiyla isaretlenmis olmali.

        `to_have_class` regex kabul eder; sinif listesinin tamamini yazmak
        yerine yalnizca aranan parcayi eslestirebiliriz.
        """
        field = self.page.get_by_test_id(field_name)
        expect(field).to_have_class(re.compile(r"error"))
        return self

    def expect_password_masked(self) -> "LoginPage":
        expect(self.password_input).to_have_attribute("type", "password")
        return self
