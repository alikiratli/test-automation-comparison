"""Playwright fixture'lari.

SELENIUM PROJESININ conftest.py DOSYASIYLA KARSILASTIRIN:

    Selenium conftest.py : ~180 satir
       - CLI parametreleri (--browser, --headed, ...)   -> elle
       - tarayici acma/kapama                            -> elle
       - hata aninda ekran goruntusu                     -> elle (hook)
       - hata aninda HTML kaynagi                        -> elle
       - konsol loglari                                  -> elle
       - HTML rapora gomme                               -> elle

    Playwright conftest.py: asagidaki dosya
       - CLI parametreleri      -> pytest-playwright HAZIR verir
       - tarayici yasam dongusu -> pytest-playwright HAZIR verir
       - ekran goruntusu/video/trace -> --screenshot/--video/--tracing bayraklari
       - konsol loglari         -> 5 satirlik olay dinleyicisi

    Geriye kalan: yalnizca UYGULAMAYA OZEL fixture'lar.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import AUTH_STATE_FILE, Settings, load_settings  # noqa: E402
from pages.inventory_page import InventoryPage  # noqa: E402
from pages.login_page import LoginPage  # noqa: E402
from utils.data_loader import checkout_customer, user  # noqa: E402

log = logging.getLogger("suite")


# --------------------------------------------------------------------------- #
# CLI parametreleri
# --------------------------------------------------------------------------- #
def pytest_addoption(parser: pytest.Parser) -> None:
    """Yalnizca UYGULAMAYA OZEL parametre.

    --browser, --headed, --slowmo, --tracing, --video, --screenshot,
    --device, --browser-channel parametrelerini pytest-playwright zaten
    tanimlar; burada tekrar tanimlanamaz (cakisir).
    """
    parser.getgroup("saucedemo").addoption(
        "--env", action="store", default=None, help="prod | staging"
    )


# --------------------------------------------------------------------------- #
# Oturum kapsamli
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def settings(request: pytest.FixtureRequest) -> Settings:
    cfg = load_settings(env=request.config.getoption("--env"))
    log.info("Ortam=%s | Adres=%s", cfg.env, cfg.base_url)
    return cfg


@pytest.fixture(scope="session", autouse=True)
def configure_test_id_attribute(playwright: Playwright) -> None:
    """`get_by_test_id()` hangi attribute'a baksin?

    Varsayilan `data-testid`; SauceDemo `data-test` kullaniyor. Tek satirlik
    bu ayar sayesinde tum sayfa nesnelerinde
        page.get_by_test_id("username")
    yazabiliyoruz. Selenium'da bunun karsiligi, her locator icin
    `(By.CSS_SELECTOR, "[data-test='username']")` yazmaktir.
    """
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def customer() -> dict[str, str]:
    return checkout_customer()


# --------------------------------------------------------------------------- #
# Tarayici context ayarlari
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict, settings: Settings) -> dict:
    """pytest-playwright'in context fabrikasini ozellestirir.

    BURASI PLAYWRIGHT'IN MIMARI USTUNLUGUNUN KALBI:
    `BrowserContext`, izole bir tarayici profilidir (cerez, localStorage,
    izinler, kimlik bilgisi hepsi ayri). Tarayici SUREC olarak bir kez acilir;
    her test kendi context'ini alir.

        Selenium: her test icin YENI TARAYICI SURECI  (~1-2 sn)
        Playwright: her test icin YENI CONTEXT        (~20-50 ms)

    Izolasyon ayni, maliyet 20-50 kat daha dusuk.
    """
    return {
        **browser_context_args,
        "viewport": {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        },
        "base_url": settings.base_url,
        "locale": "en-US",
        "timezone_id": "Europe/Istanbul",
        "ignore_https_errors": True,
    }


@pytest.fixture(autouse=True)
def configure_page(page: Page, settings: Settings) -> Page:
    """Her sayfa icin timeout'lari ayarlar ve konsol hatalarini toplar.

    KARSILASTIRMA NOTU:
        Konsol dinleme Selenium'da yalnizca Chromium'da, `get_log('browser')`
        ile SONRADAN cekilerek yapilabiliyordu. Burada olay tabanlidir ve
        chromium/firefox/webkit hepsinde calisir.
    """
    page.set_default_timeout(settings.default_timeout)
    page.set_default_navigation_timeout(settings.navigation_timeout)

    errors: list[str] = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page._console_errors = errors  # BasePage.collect_console_errors() okur
    return page


# --------------------------------------------------------------------------- #
# Uygulama fixture'lari
# --------------------------------------------------------------------------- #
@pytest.fixture
def login_page(page: Page, settings: Settings) -> LoginPage:
    return LoginPage(page, settings).open_login_page()


@pytest.fixture
def inventory_page(login_page: LoginPage) -> InventoryPage:
    standard = user("standard")
    return login_page.login_expecting_success(standard.username, standard.password)


@pytest.fixture
def cart_with_two_items(inventory_page: InventoryPage):
    products = ["Sauce Labs Backpack", "Sauce Labs Bike Light"]
    inventory_page.add_many_to_cart(products)
    return inventory_page.header.open_cart(), products


# --------------------------------------------------------------------------- #
# Oturum yeniden kullanimi (storage state)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def authenticated_state(browser: Browser, settings: Settings) -> str:
    """Bir kez giris yapar, oturum durumunu diske yazar.

    SELENIUM'DA KARSILIGI YOKTUR (kolay bir karsiligi yoktur).
        Playwright, cerezleri ve localStorage'i JSON olarak disa aktarabilir
        (`context.storage_state()`) ve yeni bir context'e dogrudan yukleyebilir.
        Sonuc: 50 test icin 50 kez UI'dan giris yapmak yerine 1 kez giris
        yapip 50 context'e ayni oturumu enjekte edersiniz.

        Buyuk suite'lerde bu tek ozellik, toplam sureyi %30-50 kisaltabilir.
        Selenium'da benzeri, cerezleri elle `driver.add_cookie()` ile
        yerlestirerek taklit edilebilir ama localStorage icin JS gerekir.
    """
    context = browser.new_context(base_url=settings.base_url)
    page = context.new_page()

    standard = user("standard")
    LoginPage(page, settings).open_login_page().login_expecting_success(
        standard.username, standard.password
    )

    AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(AUTH_STATE_FILE))
    context.close()
    log.info("Oturum durumu kaydedildi: %s", AUTH_STATE_FILE)
    return str(AUTH_STATE_FILE)


@pytest.fixture
def fast_authenticated_page(
    browser: Browser, settings: Settings, authenticated_state: str
) -> Page:
    """Giris ekranina UGRAMADAN dogrudan oturumlu sayfa doner."""
    context: BrowserContext = browser.new_context(
        storage_state=authenticated_state,
        base_url=settings.base_url,
        viewport={"width": settings.viewport_width, "height": settings.viewport_height},
    )
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout)
    yield page
    context.close()


# --------------------------------------------------------------------------- #
# Raporlama
# --------------------------------------------------------------------------- #
def pytest_html_report_title(report) -> None:
    report.title = "SauceDemo - Playwright + pytest Test Raporu"


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    terminalreporter.write_sep("=", "PLAYWRIGHT KOSUM OZETI")
    terminalreporter.write_line(f"  Gecen   : {passed}")
    terminalreporter.write_line(f"  Kalan   : {failed}")
    terminalreporter.write_line(f"  Atlanan : {skipped}")
    terminalreporter.write_line(f"  Rapor   : {PROJECT_ROOT / 'reports' / 'report.html'}")
    if failed:
        terminalreporter.write_line(
            "  Trace   : playwright show-trace reports/artifacts/<test>/trace.zip"
        )
