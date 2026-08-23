"""Login sayfasi Page Object'i."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from core.base_page import BasePage, Locator


class LoginPage(BasePage):
    PAGE_NAME = "Login"
    URL_FRAGMENT = "saucedemo.com"
    UNIQUE_LOCATOR: Locator = (By.ID, "login-button")

    # --- Locator'lar --------------------------------------------------- #
    # Oncelik sirasi: data-test > id > isim > kararli CSS > XPath.
    # data-test attribute'u UI degisikliklerinden en az etkilenen secicidir.
    USERNAME_INPUT: Locator = (By.CSS_SELECTOR, "[data-test='username']")
    PASSWORD_INPUT: Locator = (By.CSS_SELECTOR, "[data-test='password']")
    LOGIN_BUTTON: Locator = (By.CSS_SELECTOR, "[data-test='login-button']")
    ERROR_MESSAGE: Locator = (By.CSS_SELECTOR, "[data-test='error']")
    ERROR_CLOSE_BUTTON: Locator = (By.CSS_SELECTOR, ".error-button")
    LOGIN_LOGO: Locator = (By.CSS_SELECTOR, ".login_logo")
    ACCEPTED_USERNAMES: Locator = (By.ID, "login_credentials")

    # --- Eylemler ------------------------------------------------------ #
    def open_login_page(self) -> "LoginPage":
        self.open(self.settings.login_url)
        self.verify_loaded()
        return self

    def enter_username(self, username: str) -> "LoginPage":
        # Bos string gonderilirse send_keys anlamsizdir; alani sadece temizle.
        if username:
            self.type_text(self.USERNAME_INPUT, username)
        else:
            self.wait_visible(self.USERNAME_INPUT).clear()
        return self

    def enter_password(self, password: str) -> "LoginPage":
        if password:
            self.type_text(self.PASSWORD_INPUT, password)
        else:
            self.wait_visible(self.PASSWORD_INPUT).clear()
        return self

    def submit(self) -> None:
        self.click(self.LOGIN_BUTTON)

    def login(self, username: str, password: str):
        """Giris yapar ve HANGI SAYFAYA gidildiyse onun objesini doner.

        Basarili giris -> InventoryPage, basarisiz -> LoginPage (self).
        Bu "sayfa gecisi dondurme" deseni, testin akisi takip etmesini saglar.
        """
        self.log.info("Giris denemesi: '%s'", username)
        self.enter_username(username)
        self.enter_password(password)
        self.submit()

        # Import'u burada yapiyoruz: LoginPage <-> InventoryPage dairesel
        # bagimliligini kirmak icin standart bir cozum.
        from pages.inventory_page import InventoryPage

        if self.wait_for(
            lambda d: "inventory.html" in d.current_url or self.exists(self.ERROR_MESSAGE),
            timeout=self.timeout,
            state="giris sonucu belirlendi",
        ):
            pass

        if "inventory.html" in self.current_url:
            self.log.info("Giris basarili -> envanter sayfasi")
            return InventoryPage(self.driver, self.settings).verify_loaded()

        self.log.info("Giris reddedildi -> login sayfasinda kalindi")
        return self

    def login_expecting_success(self, username: str, password: str):
        page = self.login(username, password)
        if isinstance(page, LoginPage):
            raise AssertionError(
                f"'{username}' ile giris beklenmedik sekilde basarisiz oldu: "
                f"{self.get_error_message()}"
            )
        return page

    def dismiss_error(self) -> "LoginPage":
        if self.is_visible(self.ERROR_CLOSE_BUTTON, timeout=2):
            self.click(self.ERROR_CLOSE_BUTTON)
            self.wait_invisible(self.ERROR_MESSAGE, timeout=5)
        return self

    # --- Sorgular ------------------------------------------------------ #
    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE) if self.exists(self.ERROR_MESSAGE) else ""

    def has_error(self) -> bool:
        return self.is_visible(self.ERROR_MESSAGE, timeout=5)

    def is_field_marked_invalid(self, field: Locator) -> bool:
        """SauceDemo hatali alanlara 'error' CSS sinifi ekler."""
        return "error" in self.get_attribute(field, "class")

    def accepted_usernames(self) -> list[str]:
        """Sayfada listelenen demo kullanicilarini doner (dokumantasyon amacli)."""
        raw = self.get_text(self.ACCEPTED_USERNAMES)
        return [line.strip() for line in raw.splitlines() if line.strip() and "_user" in line]
