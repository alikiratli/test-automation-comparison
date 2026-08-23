"""Ozel bekleme kosullari (custom Expected Conditions).

KARSILASTIRMA NOTU - BU DOSYA PLAYWRIGHT'TA HIC YOKTUR:
    Playwright'ta `locator.click()` cagrildiginda framework elemanin DOM'a
    girmesini, gorunur olmasini, stabil (animasyonu bitmis) olmasini, ustunde
    baska eleman olmamasini ve etkinlestirilmis olmasini KENDILIGINDEN bekler.
    Selenium'da bu "auto-waiting" yoktur; asagidaki kosullari kendiniz yazar,
    her cagrida WebDriverWait ile kendiniz uygularsiniz. Bu dosya, iki
    framework arasindaki en buyuk mimari farkin somut karsiligidir.
"""
from __future__ import annotations

from typing import Callable, Sequence

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC


def element_has_stable_text(locator, samples: int = 2) -> Callable[[WebDriver], str | bool]:
    """Metin ust uste `samples` kez ayni kalirsa hazir kabul eder.

    Ajax ile guncellenen sayaclarda (sepet rozeti gibi) "yakalandi ama eski
    deger okundu" hatasini engeller.
    """
    history: list[str] = []

    def _predicate(driver: WebDriver):
        try:
            current = driver.find_element(*locator).text.strip()
        except StaleElementReferenceException:
            history.clear()
            return False
        history.append(current)
        if len(history) > samples:
            history.pop(0)
        if len(history) == samples and len(set(history)) == 1 and current != "":
            return current
        return False

    return _predicate


def text_to_be_one_of(locator, candidates: Sequence[str]) -> Callable[[WebDriver], bool]:
    """Elemanin metni verilen adaylardan biri olana kadar bekler."""

    def _predicate(driver: WebDriver) -> bool:
        try:
            return driver.find_element(*locator).text.strip() in candidates
        except StaleElementReferenceException:
            return False

    return _predicate


def element_count_to_be(locator, expected: int) -> Callable[[WebDriver], bool]:
    """Liste uzunlugu beklenen sayiya ulasana kadar bekler."""

    def _predicate(driver: WebDriver) -> bool:
        return len(driver.find_elements(*locator)) == expected

    return _predicate


def element_count_at_least(locator, minimum: int) -> Callable[[WebDriver], bool]:
    def _predicate(driver: WebDriver) -> bool:
        return len(driver.find_elements(*locator)) >= minimum

    return _predicate


def attribute_contains(locator, attribute: str, value: str) -> Callable[[WebDriver], bool]:
    def _predicate(driver: WebDriver) -> bool:
        try:
            actual = driver.find_element(*locator).get_attribute(attribute) or ""
        except StaleElementReferenceException:
            return False
        return value in actual

    return _predicate


def element_to_be_clickable_and_stable(locator) -> Callable[[WebDriver], WebElement | bool]:
    """Tiklanabilir + iki ardisik olcumde ayni konumda (animasyon bitmis)."""
    previous_position: dict[str, tuple[int, int]] = {}

    def _predicate(driver: WebDriver):
        element = EC.element_to_be_clickable(locator)(driver)
        if not element:
            return False
        try:
            location = (element.location["x"], element.location["y"])
        except StaleElementReferenceException:
            return False
        if previous_position.get("last") == location:
            return element
        previous_position["last"] = location
        return False

    return _predicate


def document_ready() -> Callable[[WebDriver], bool]:
    """document.readyState == 'complete' olana kadar bekler."""

    def _predicate(driver: WebDriver) -> bool:
        return driver.execute_script("return document.readyState") == "complete"

    return _predicate


def no_pending_animations(selector: str = "*") -> Callable[[WebDriver], bool]:
    """Sayfada devam eden CSS animasyonu kalmayana kadar bekler."""
    script = """
        const nodes = document.querySelectorAll(arguments[0]);
        for (const node of nodes) {
            if (typeof node.getAnimations !== 'function') { continue; }
            if (node.getAnimations().some(a => a.playState === 'running')) { return false; }
        }
        return true;
    """

    def _predicate(driver: WebDriver) -> bool:
        return bool(driver.execute_script(script, selector))

    return _predicate
