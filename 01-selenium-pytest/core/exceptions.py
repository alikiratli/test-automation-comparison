"""Projeye ozel hata tipleri.

Selenium'un firlattigi ham `TimeoutException` mesaji genelde sadece stack trace
icerir ve "hangi sayfada, hangi elemani, ne kadar bekledik" bilgisini vermez.
Asagidaki sarmalayicilar hata mesajini teshis edilebilir hale getirir.
"""
from __future__ import annotations


class FrameworkError(Exception):
    """Tum proje hatalarinin atasi."""


class ElementNotReadyError(FrameworkError):
    """Eleman beklenen sure icinde beklenen duruma gelmedi."""

    def __init__(self, locator, state: str, timeout: float, page: str = "") -> None:
        page_info = f" [sayfa: {page}]" if page else ""
        super().__init__(
            f"Eleman {timeout}sn icinde '{state}' durumuna gelmedi -> {locator}{page_info}"
        )
        self.locator = locator
        self.state = state
        self.timeout = timeout


class PageNotLoadedError(FrameworkError):
    """Sayfa dogrulamasi (URL veya isaretci eleman) basarisiz oldu."""

    def __init__(self, page_name: str, expected: str, actual: str) -> None:
        super().__init__(
            f"'{page_name}' sayfasi yuklenmedi. Beklenen: '{expected}' | Gercek: '{actual}'"
        )


class BusinessRuleError(FrameworkError):
    """Uygulama is kuralinin ihlali (ornegin toplam tutar tutmuyor)."""
