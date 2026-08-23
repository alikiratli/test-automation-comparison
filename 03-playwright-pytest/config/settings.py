"""Playwright projesi ayarlari.

KARSILASTIRMA NOTU:
    Selenium projesinde `config/settings.py` YAML okur, tarayici argumanlarini
    kurar, timeout'lari yonetirdi (~150 satir). Burada cok daha kisadir cunku
    tarayici yapilandirmasinin buyuk kismi pytest-playwright eklentisine ve
    `browser_context_args` fixture'ina devredilmistir.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
SHARED_DATA_DIR = REPO_ROOT / "shared"
REPORTS_DIR = PROJECT_ROOT / "reports"
AUTH_STATE_FILE = PROJECT_ROOT / ".auth" / "standard_user.json"

ENVIRONMENTS = {
    "prod": "https://www.saucedemo.com",
    "staging": "https://www.saucedemo.com",
}

# Playwright'in API testi ozelligini gostermek icin kullanilan public sandbox.
# SauceDemo'nun bir API'si olmadigi icin farkli bir hedef seciliyor.
API_SANDBOX_URL = "https://jsonplaceholder.typicode.com"


@dataclass(frozen=True)
class Settings:
    env: str
    base_url: str
    # Playwright'ta timeout'lar MILISANIYE cinsindendir (Selenium'da saniye).
    default_timeout: int = 15_000
    navigation_timeout: int = 30_000
    slow_user_timeout: int = 45_000
    expect_timeout: int = 10_000
    viewport_width: int = 1920
    viewport_height: int = 1080

    @property
    def login_url(self) -> str:
        return self.base_url

    @property
    def inventory_url(self) -> str:
        return f"{self.base_url}/inventory.html"

    @property
    def cart_url(self) -> str:
        return f"{self.base_url}/cart.html"

    @property
    def checkout_step_one_url(self) -> str:
        return f"{self.base_url}/checkout-step-one.html"

    @property
    def checkout_step_two_url(self) -> str:
        return f"{self.base_url}/checkout-step-two.html"

    @property
    def checkout_complete_url(self) -> str:
        return f"{self.base_url}/checkout-complete.html"


def load_settings(env: str | None = None) -> Settings:
    env_name = env or os.getenv("TEST_ENV") or "prod"
    if env_name not in ENVIRONMENTS:
        raise ValueError(f"Bilinmeyen ortam: {env_name}. Secenekler: {list(ENVIRONMENTS)}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    return Settings(env=env_name, base_url=ENVIRONMENTS[env_name])
