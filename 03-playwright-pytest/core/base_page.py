"""Playwright icin temel sayfa sinifi.

BU DOSYAYI SELENIUM PROJESINDEKI core/base_page.py ILE KARSILASTIRIN:

    Selenium surumu  : ~250 satir
    Playwright surumu: ~90 satir

FARKIN NEDENI:
  1. AUTO-WAITING
     `locator.click()` cagrildiginda Playwright, elemanin:
       - DOM'a eklenmesini
       - gorunur olmasini
       - stabil olmasini (animasyon bitmis)
       - etkinlestirilmis (enabled) olmasini
       - ustunde baska eleman OLMAMASINI (actionability)
     otomatik bekler. Selenium'da bunlarin hepsi elle yazilir.

  2. LOCATOR'LAR TEMBELDIR (lazy)
     `page.locator(...)` DOM'da arama YAPMAZ; sadece bir "tarif" tutar. Arama
     her etkilesimde yeniden yapilir. Bu yuzden Playwright'ta
     StaleElementReferenceException DIYE BIR SEY YOKTUR - Selenium projesindeki
     `_with_stale_retry` mekanizmasinin tamami gereksizdir.

  3. WEB-FIRST ASSERTIONS
     `expect(locator).to_have_text("X")` kosul saglanana kadar TEKRAR DENER.
     Selenium'daki `assert element.text == "X"` ise tek seferliktir; bu yuzden
     ondan once ayrica bir WebDriverWait yazmak gerekir.
"""
from __future__ import annotations

import logging

from playwright.sync_api import Locator, Page, Response, expect

from config.settings import Settings

log = logging.getLogger(__name__)


class BasePage:
    """Ortak sayfa davranislari."""

    URL_PATH: str = ""
    PAGE_NAME: str = "BasePage"

    def __init__(self, page: Page, settings: Settings) -> None:
        self.page = page
        self.settings = settings
        self.log = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Navigasyon
    # ------------------------------------------------------------------ #
    def navigate(self, url: str | None = None) -> Response | None:
        target = url or f"{self.settings.base_url}{self.URL_PATH}"
        self.log.info("Adrese git: %s", target)
        return self.page.goto(target, wait_until="domcontentloaded")

    def verify_loaded(self, timeout: int | None = None) -> "BasePage":
        """Alt siniflar bunu ezerek kendi isaretci elemanlarini dogrular."""
        if self.URL_PATH:
            expect(self.page).to_have_url(
                f"{self.settings.base_url}{self.URL_PATH}",
                timeout=timeout or self.settings.expect_timeout,
            )
        return self

    @property
    def url(self) -> str:
        return self.page.url

    @property
    def title(self) -> str:
        return self.page.title()

    # ------------------------------------------------------------------ #
    # Yardimcilar
    # ------------------------------------------------------------------ #
    def by_test_id(self, value: str) -> Locator:
        """data-test attribute'una gore locator.

        Playwright'ta test id attribute adi yapilandirilabilir:
            playwright.selectors.set_test_id_attribute("data-test")
        Bunu conftest.py icinde bir kez ayarliyoruz; boylece
        `page.get_by_test_id("username")` dogrudan calisir.
        """
        return self.page.get_by_test_id(value)

    def wait_for_network_idle(self, timeout: int | None = None) -> None:
        """Tum ag istekleri bitene kadar bekler.

        SELENIUM'DA KARSILIGI YOKTUR. Selenium tarayicinin ag katmanini
        gormez; benzer bir bekleme ancak JS ile taklit edilebilir.
        """
        self.page.wait_for_load_state(
            "networkidle", timeout=timeout or self.settings.navigation_timeout
        )

    def screenshot(self, path: str, full_page: bool = True) -> bytes:
        return self.page.screenshot(path=path, full_page=full_page)

    def collect_console_errors(self) -> list[str]:
        """Sayfa uzerinde biriken konsol hatalarini doner.

        Dinleyici conftest.py'de kurulur ve page nesnesine ilistirilir.
        Selenium'da bu YALNIZCA Chromium'da ve ancak sonradan cekilerek
        mumkundur; Playwright'ta olay tabanli ve tum tarayicilarda calisir.
        """
        return getattr(self.page, "_console_errors", [])
