"""Robot Framework degisken dosyasi (variable file).

Kullanim:
    robot --variablefile variables/environment.py:staging:firefox tests/

KARSILASTIRMA NOTU:
    Robot Framework saf metin (plain text) bir dildir; kosullu mantik, dosya
    okuma, hesaplama gibi isler icin Python'a "inip cikmak" gerekir. Iste bu
    dosya o gecis noktasidir. `get_variables()` fonksiyonu Robot tarafindan
    otomatik cagrilir ve donen sozlugun her anahtari bir Robot degiskenine
    (${BASE_URL} gibi) donusur.

    Selenium+pytest'te ayni is `config/settings.py` icinde, Playwright'ta
    fixture'larla yapilir. Fark: burada mantik Python'da, KULLANIM Robot'ta.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_DATA_DIR = PROJECT_ROOT.parent / "shared"

_ENVIRONMENTS = {
    "prod": "https://www.saucedemo.com",
    "staging": "https://www.saucedemo.com",
}

_BROWSER_OPTIONS = {
    # SeleniumLibrary'nin `options=` parametresi bu string'i degerlendirir.
    "chrome": (
        'add_argument("--headless=new"); '
        'add_argument("--no-sandbox"); '
        'add_argument("--disable-dev-shm-usage"); '
        'add_argument("--disable-gpu"); '
        'add_argument("--window-size=1920,1080"); '
        'add_argument("--lang=en-US"); '
        'add_experimental_option("prefs", {"credentials_enable_service": False, '
        '"profile.password_manager_enabled": False})'
    ),
    "headlesschrome": "",
    "firefox": 'add_argument("-headless"); add_argument("--width=1920")',
    "edge": 'add_argument("--headless=new"); add_argument("--window-size=1920,1080")',
}


def _load_shared(filename: str) -> dict:
    with (SHARED_DATA_DIR / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def get_variables(env: str = "prod", browser: str = "chrome", headless: str = "true") -> dict:
    """Robot'un otomatik cagirdigi giris noktasi."""
    base_url = _ENVIRONMENTS.get(env)
    if base_url is None:
        raise ValueError(f"Bilinmeyen ortam: {env}. Secenekler: {list(_ENVIRONMENTS)}")

    is_headless = str(headless).lower() in {"true", "1", "yes"}
    options = _BROWSER_OPTIONS.get(browser.lower(), "") if is_headless else ""

    products_data = _load_shared("products.json")
    users_data = _load_shared("users.json")

    # Kullanicilari id -> sozluk seklinde duzlestir: ${USERS}[standard][username]
    users_by_id = {item["id"]: item for item in users_data["users"]}

    return {
        # --- Ortam ---
        "ENV": env,
        "BASE_URL": base_url,
        "BROWSER": browser,
        "BROWSER_OPTIONS": options,
        "HEADLESS": is_headless,
        "WINDOW_WIDTH": 1920,
        "WINDOW_HEIGHT": 1080,
        # --- Adresler ---
        "LOGIN_URL": base_url,
        "INVENTORY_URL": f"{base_url}/inventory.html",
        "CART_URL": f"{base_url}/cart.html",
        "CHECKOUT_STEP_ONE_URL": f"{base_url}/checkout-step-one.html",
        "CHECKOUT_STEP_TWO_URL": f"{base_url}/checkout-step-two.html",
        "CHECKOUT_COMPLETE_URL": f"{base_url}/checkout-complete.html",
        # --- Sureler ---
        "DEFAULT_TIMEOUT": "15s",
        "SLOW_USER_TIMEOUT": "40s",
        "SHORT_TIMEOUT": "5s",
        # --- Test verisi (../shared klasorunden) ---
        "USERS": users_by_id,
        "PASSWORD": users_data["password"],
        "PRODUCTS": {p["name"]: p["price"] for p in products_data["products"]},
        "PRODUCT_NAMES": [p["name"] for p in products_data["products"]],
        "EXPECTED_PRODUCT_COUNT": products_data["expected_product_count"],
        "TAX_RATE": products_data["tax_rate"],
        "CUSTOMER": products_data["checkout_customer"],
        # --- Sik kullanilanlar (kisayol) ---
        "STANDARD_USER": users_by_id["standard"]["username"],
        "LOCKED_USER": users_by_id["locked_out"]["username"],
        "PROBLEM_USER": users_by_id["problem"]["username"],
        "GLITCH_USER": users_by_id["performance_glitch"]["username"],
        "SHARED_DATA_DIR": str(SHARED_DATA_DIR),
    }
