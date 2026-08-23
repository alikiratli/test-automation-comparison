"""Metin -> veri donusumleri.

Bu fonksiyonlar UI'dan bagimsizdir; birim testle dogrulanabilirler.
Ayni mantik Robot Framework tarafinda `libraries/SauceDemoLibrary.py` icinde,
Playwright tarafinda `utils/parsers.py` icinde tekrar eder - bilinctli olarak,
cunku her proje kendi basina calisabilir olmalidir.
"""
from __future__ import annotations

import re

_PRICE_PATTERN = re.compile(r"-?\d+(?:[.,]\d+)?")


def parse_price(text: str) -> float:
    """'Item total: $129.94' -> 129.94

    Etiket metnini, para birimi sembolunu ve bosluklari temizler.
    """
    if text is None:
        raise ValueError("parse_price(None) cagrilamaz")
    match = _PRICE_PATTERN.search(str(text).replace(",", "."))
    if not match:
        raise ValueError(f"Metinden fiyat cikarilamadi: '{text}'")
    return round(float(match.group()), 2)


def slugify_product(name: str) -> str:
    """'Sauce Labs Backpack' -> 'sauce-labs-backpack'

    SauceDemo data-test degerlerini uretir. Ozel urun adi
    'Test.allTheThings() T-Shirt (Red)' -> 'test.allthethings()-t-shirt-(red)'
    seklinde noktalama isaretlerini KORUR; bu yuzden sadece kucult ve
    bosluklari tire yap.
    """
    return name.strip().lower().replace(" ", "-")


def is_sorted_ascending(values: list) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def is_sorted_descending(values: list) -> bool:
    return all(values[i] >= values[i + 1] for i in range(len(values) - 1))


def calculate_expected_tax(subtotal: float, rate: float = 0.08) -> float:
    return round(subtotal * rate, 2)
