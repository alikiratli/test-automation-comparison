"""Soft assertion (yumusak dogrulama) destegi.

Normal `assert` ilk hatada testi durdurur. Bir sayfada 10 alan dogrulanacaksa
ilk hatadan sonrakiler gorunmez olur. SoftAssert tum hatalari toplar ve sonunda
hepsini birden raporlar.

KARSILASTIRMA NOTU:
    Robot Framework'te `Run Keyword And Continue On Failure` ayni isi hazir
    yapar. Playwright (Python) tarafinda `expect` retry'lidir ama soft assert
    yine elle kurulur; TypeScript surumunde `expect.soft()` yerlesiktir.
"""
from __future__ import annotations

from typing import Any

from core.logger import get_logger


class SoftAssert:
    def __init__(self, context: str = "") -> None:
        self.context = context
        self.failures: list[str] = []
        self.log = get_logger("SoftAssert")

    def check(self, condition: bool, message: str) -> bool:
        if condition:
            self.log.info("OK  - %s", message)
        else:
            self.log.error("HATA - %s", message)
            self.failures.append(message)
        return condition

    def equal(self, actual: Any, expected: Any, message: str) -> bool:
        return self.check(
            actual == expected, f"{message} | beklenen='{expected}' gercek='{actual}'"
        )

    def contains(self, haystack: str, needle: str, message: str) -> bool:
        return self.check(
            needle in haystack, f"{message} | '{needle}' su metinde aranidi: '{haystack}'"
        )

    def assert_all(self) -> None:
        if not self.failures:
            return
        header = f"{len(self.failures)} yumusak dogrulama basarisiz"
        if self.context:
            header += f" ({self.context})"
        details = "\n".join(f"  {i}. {msg}" for i, msg in enumerate(self.failures, 1))
        raise AssertionError(f"{header}:\n{details}")

    def __enter__(self) -> "SoftAssert":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self.assert_all()
        return False
