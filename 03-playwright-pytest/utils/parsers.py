"""Metin -> veri donusumleri (Selenium projesindekiyle ayni mantik)."""
from __future__ import annotations

import re

_PRICE_PATTERN = re.compile(r"-?\d+(?:[.,]\d+)?")


def parse_price(text: str) -> float:
    match = _PRICE_PATTERN.search(str(text).replace(",", "."))
    if not match:
        raise ValueError(f"Metinden fiyat cikarilamadi: '{text}'")
    return round(float(match.group()), 2)


def slugify_product(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def is_sorted_ascending(values: list) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def is_sorted_descending(values: list) -> bool:
    return all(values[i] >= values[i + 1] for i in range(len(values) - 1))
