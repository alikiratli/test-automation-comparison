"""Tum Page Object'lerin miras aldigi temel sinif.

Bu sinif Selenium'un "ham" API'sini guvenli hale getirir:
  * her etkilesimden once acik (explicit) bekleme
  * StaleElementReferenceException icin otomatik yeniden deneme
  * anlamli hata mesajlari
  * her adimin loglanmasi

KARSILASTIRMA NOTU:
    Playwright'ta bu dosyanin buyuk bolumu GEREKSIZDIR: auto-wait, retry ve
    aktarilabilir hata mesajlari framework'un icindedir. Robot Framework'te ise
    SeleniumLibrary keyword'leri (Wait Until Element Is Visible, Click Element)
    ayni islevi hazir sunar. Selenium'un "her sey elinizde" felsefesinin
    bedeli, asagidaki ~250 satirlik altyapinin her projede yeniden yazilmasidir.
"""
from __future__ import annotations

import time
from typing import Callable, Iterable, Sequence

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import Settings
from core import waits
from core.exceptions import ElementNotReadyError, PageNotLoadedError
from core.logger import get_logger

Locator = tuple[str, str]


class BasePage:
    """Ortak sayfa davranislari."""

    #: Alt siniflar bu iki alani doldurur; `verify_loaded()` bunlari kullanir.
    URL_FRAGMENT: str = ""
    UNIQUE_LOCATOR: Locator | None = None
    PAGE_NAME: str = "BasePage"

    def __init__(self, driver: WebDriver, settings: Settings) -> None:
        self.driver = driver
        self.settings = settings
        self.timeout = settings.timeouts.explicit_wait
        self.log = get_logger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Bekleme yardimcilari
    # ------------------------------------------------------------------ #
    def _wait(self, timeout: float | None = None) -> WebDriverWait:
        return WebDriverWait(
            self.driver,
            timeout or self.timeout,
            poll_frequency=self.settings.timeouts.poll_frequency,
            ignored_exceptions=(StaleElementReferenceException, NoSuchElementException),
        )

    def wait_for(
        self,
        condition: Callable,
        timeout: float | None = None,
        state: str = "kosul",
        locator: Locator | None = None,
    ):
        """Bir Expected Condition'i uygular, zaman asiminda anlamli hata verir."""
        try:
            return self._wait(timeout).until(condition)
        except TimeoutException as exc:
            raise ElementNotReadyError(
                locator or condition, state, timeout or self.timeout, self.PAGE_NAME
            ) from exc

    def wait_visible(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self.wait_for(
            EC.visibility_of_element_located(locator), timeout, "gorunur", locator
        )

    def wait_present(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self.wait_for(
            EC.presence_of_element_located(locator), timeout, "DOM'da mevcut", locator
        )

    def wait_clickable(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self.wait_for(
            waits.element_to_be_clickable_and_stable(locator),
            timeout,
            "tiklanabilir ve sabit",
            locator,
        )

    def wait_invisible(self, locator: Locator, timeout: float | None = None) -> bool:
        return self.wait_for(
            EC.invisibility_of_element_located(locator), timeout, "gorunmez", locator
        )

    def wait_url_contains(self, fragment: str, timeout: float | None = None) -> bool:
        return self.wait_for(EC.url_contains(fragment), timeout, f"URL '{fragment}' icerir")

    def wait_document_ready(self, timeout: float | None = None) -> bool:
        return self.wait_for(waits.document_ready(), timeout, "document.readyState=complete")

    # ------------------------------------------------------------------ #
    # Etkilesimler - hepsi StaleElement'e karsi korumali
    # ------------------------------------------------------------------ #
    def _with_stale_retry(self, action: Callable, description: str):
        """DOM yeniden ciziminde bozulan referanslari yeniden dener.

        Bu, Selenium ile calisirken en sik karsilasilan hata sinifidir ve
        Playwright'ta locator'lar "lazy" oldugu icin hic yasanmaz.
        """
        attempts = self.settings.stale_element_attempts
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return action()
            except (StaleElementReferenceException, ElementClickInterceptedException) as exc:
                last_error = exc
                self.log.warning(
                    "%s -> %s (deneme %s/%s)",
                    description,
                    type(exc).__name__,
                    attempt,
                    attempts,
                )
                time.sleep(self.settings.stale_element_backoff * attempt)
        raise last_error  # type: ignore[misc]

    def click(self, locator: Locator, timeout: float | None = None) -> None:
        self.log.info("Tikla: %s", locator)

        def _do() -> None:
            self.wait_clickable(locator, timeout).click()

        self._with_stale_retry(_do, f"click{locator}")

    def js_click(self, locator: Locator) -> None:
        """Ustunde overlay olan elemanlar icin son care."""
        self.log.info("JS ile tikla: %s", locator)
        element = self.wait_present(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def type_text(self, locator: Locator, text: str, clear: bool = True) -> None:
        masked = "*" * len(text) if "pass" in str(locator).lower() else text
        self.log.info("Yaz: %s -> '%s'", locator, masked)

        def _do() -> None:
            element = self.wait_visible(locator)
            if clear:
                element.clear()
            element.send_keys(text)

        self._with_stale_retry(_do, f"type{locator}")

    def get_text(self, locator: Locator, timeout: float | None = None) -> str:
        def _do() -> str:
            return self.wait_visible(locator, timeout).text.strip()

        return self._with_stale_retry(_do, f"text{locator}")

    def get_texts(self, locator: Locator, timeout: float | None = None) -> list[str]:
        """Liste elemanlarinin metinlerini doner (ilk eleman gorunur olana kadar bekler)."""
        self.wait_for(
            waits.element_count_at_least(locator, 1), timeout, "en az 1 eleman", locator
        )

        def _do() -> list[str]:
            return [e.text.strip() for e in self.driver.find_elements(*locator)]

        return self._with_stale_retry(_do, f"texts{locator}")

    def get_attribute(self, locator: Locator, attribute: str) -> str:
        def _do() -> str:
            return self.wait_present(locator).get_attribute(attribute) or ""

        return self._with_stale_retry(_do, f"attr{locator}.{attribute}")

    def select_by_value(self, locator: Locator, value: str) -> None:
        self.log.info("Dropdown sec: %s -> %s", locator, value)

        def _do() -> None:
            Select(self.wait_visible(locator)).select_by_value(value)

        self._with_stale_retry(_do, f"select{locator}")

    def hover(self, locator: Locator) -> None:
        element = self.wait_visible(locator)
        ActionChains(self.driver).move_to_element(element).perform()

    def scroll_into_view(self, locator: Locator) -> None:
        element = self.wait_present(locator)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
        )

    # ------------------------------------------------------------------ #
    # Sorgular
    # ------------------------------------------------------------------ #
    def is_visible(self, locator: Locator, timeout: float = 3) -> bool:
        """Gorunurlugu kisa bir zaman asimiyla sorar; hata firlatmaz."""
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def count(self, locator: Locator) -> int:
        return len(self.driver.find_elements(*locator))

    def exists(self, locator: Locator) -> bool:
        return self.count(locator) > 0

    # ------------------------------------------------------------------ #
    # Sayfa dogrulama ve navigasyon
    # ------------------------------------------------------------------ #
    def open(self, url: str) -> "BasePage":
        self.log.info("Adrese git: %s", url)
        self.driver.get(url)
        self.wait_document_ready()
        return self

    def verify_loaded(self, timeout: float | None = None) -> "BasePage":
        """Sayfanin dogru sayfa oldugunu URL + isaretci eleman ile dogrular."""
        effective = timeout or self.timeout
        if self.URL_FRAGMENT:
            try:
                self._wait(effective).until(EC.url_contains(self.URL_FRAGMENT))
            except TimeoutException as exc:
                raise PageNotLoadedError(
                    self.PAGE_NAME, self.URL_FRAGMENT, self.driver.current_url
                ) from exc
        if self.UNIQUE_LOCATOR:
            try:
                self._wait(effective).until(
                    EC.visibility_of_element_located(self.UNIQUE_LOCATOR)
                )
            except TimeoutException as exc:
                raise PageNotLoadedError(
                    self.PAGE_NAME, str(self.UNIQUE_LOCATOR), "isaretci eleman gorunmedi"
                ) from exc
        self.log.info("Sayfa dogrulandi: %s", self.PAGE_NAME)
        return self

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    @property
    def title(self) -> str:
        return self.driver.title

    # ------------------------------------------------------------------ #
    # Teshis
    # ------------------------------------------------------------------ #
    def take_screenshot(self, path: str) -> None:
        self.driver.save_screenshot(path)

    def browser_console_errors(self) -> list[str]:
        """Tarayici konsolundaki SEVERE kayitlari doner (yalnizca Chrome/Edge).

        KARSILASTIRMA NOTU: Playwright'ta konsol dinlemek olay tabanlidir
        (`page.on("console", ...)`) ve tum tarayicilarda calisir. Selenium'da
        yalnizca Chromium tabanli tarayicilarda ve yalnizca "cekerek" mumkundur.
        """
        try:
            logs = self.driver.get_log("browser")
        except Exception:  # Firefox bu API'yi desteklemez
            return []
        return [entry["message"] for entry in logs if entry.get("level") == "SEVERE"]

    @staticmethod
    def by_test_id(value: str) -> Locator:
        return (By.CSS_SELECTOR, f"[data-test='{value}']")

    @staticmethod
    def unique(values: Iterable[str]) -> Sequence[str]:
        return list(dict.fromkeys(values))
