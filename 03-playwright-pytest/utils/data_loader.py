"""../shared klasorundeki ortak test verisini yukler."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from config.settings import SHARED_DATA_DIR


@dataclass(frozen=True)
class UserCredential:
    id: str
    username: str
    password: str
    should_login: bool
    expected_error: str | None
    description: str

    def __str__(self) -> str:
        return self.id


def _read_json(filename: str) -> dict[str, Any]:
    with (SHARED_DATA_DIR / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_users() -> list[UserCredential]:
    payload = _read_json("users.json")
    return [UserCredential(**{k: v for k, v in item.items()}) for item in payload["users"]]


def user(user_id: str) -> UserCredential:
    for candidate in load_users():
        if candidate.id == user_id:
            return candidate
    raise KeyError(f"Tanimsiz kullanici id: '{user_id}'")


def valid_users() -> list[UserCredential]:
    return [u for u in load_users() if u.should_login]


def invalid_users() -> list[UserCredential]:
    return [u for u in load_users() if not u.should_login]


@lru_cache(maxsize=1)
def load_products() -> dict[str, Any]:
    return _read_json("products.json")


def product_names() -> list[str]:
    return [p["name"] for p in load_products()["products"]]


def product_price(name: str) -> float:
    for product in load_products()["products"]:
        if product["name"] == name:
            return float(product["price"])
    raise KeyError(f"Tanimsiz urun: '{name}'")


def tax_rate() -> float:
    return float(load_products()["tax_rate"])


def checkout_customer() -> dict[str, str]:
    return dict(load_products()["checkout_customer"])
