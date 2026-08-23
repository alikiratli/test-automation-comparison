"""pytest fixture'lari ve hook'lari - Selenium projesinin omurgasi.

KARSILASTIRMA NOTU:
    Robot Framework'te Suite Setup / Test Teardown, `*** Settings ***` icinde
    iki satirdir. Playwright-pytest'te `page` fixture'i eklentiden HAZIR gelir.
    Selenium'da su dosyanin tamami elle yazilir: tarayici acma/kapama, hata
    aninda ekran goruntusu, HTML rapor zenginlestirme, CLI parametreleri.
    Bu dosya, "Selenium daha cok bogaz kod ister" iddiasinin kanitidir.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Proje kokunu import yoluna ekle (paket kurulumu gerektirmemek icin)
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import Settings, load_settings  # noqa: E402
from core.driver_factory import DriverFactory  # noqa: E402
from core.logger import configure_logging, get_logger  # noqa: E402
from pages.login_page import LoginPage  # noqa: E402
from utils.data_loader import checkout_customer, user  # noqa: E402


# --------------------------------------------------------------------------- #
# CLI parametreleri
# --------------------------------------------------------------------------- #
def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("saucedemo")
    group.addoption("--browser", action="store", default=None,
                    help="chrome | firefox | edge")
    group.addoption("--env", action="store", default=None,
                    help="config.yaml icindeki ortam adi (prod, staging)")
    group.addoption("--headed", action="store_true", default=False,
                    help="Tarayiciyi gorunur modda calistir")
    group.addoption("--keep-browser-open", action="store_true", default=False,
                    help="Hata aninda tarayiciyi kapatma (yerel hata ayiklama)")


# --------------------------------------------------------------------------- #
# Oturum kapsamli fixture'lar
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def settings(request: pytest.FixtureRequest) -> Settings:
    cfg = load_settings(
        env=request.config.getoption("--env"),
        browser=request.config.getoption("--browser"),
        headless=not request.config.getoption("--headed"),
    )
    log_file = configure_logging(cfg.artifacts.log_dir)
    log = get_logger("session")
    log.info("=" * 78)
    log.info("Kosum basladi | ortam=%s | tarayici=%s | headless=%s",
             cfg.env, cfg.browser.name, cfg.browser.headless)
    log.info("Hedef adres: %s", cfg.base_url)
    log.info("Log dosyasi: %s", log_file)
    log.info("=" * 78)
    return cfg


@pytest.fixture(scope="session")
def customer() -> dict[str, str]:
    """Checkout formunda kullanilan varsayilan musteri."""
    return checkout_customer()


# --------------------------------------------------------------------------- #
# Test kapsamli fixture'lar
# --------------------------------------------------------------------------- #
@pytest.fixture
def driver(settings: Settings, request: pytest.FixtureRequest):
    """Her test icin TEMIZ bir tarayici oturumu.

    Neden her test icin yeni tarayici?
      + Tam izolasyon: cerez/localStorage sizintisi olmaz, testler birbirini
        etkilemez, paralel kosumda (-n auto) guvenlidir.
      - Maliyet: tarayici acilisi test basina ~1-2 sn ekler.

    Playwright'ta bu ikilem `browser` (oturum kapsamli) + `context` (test
    kapsamli) ayrimiyla cozulur: tarayici bir kez acilir, her test izole bir
    context alir. Selenium'da context kavrami yoktur; ya tarayiciyi yeniden
    acarsiniz ya da izolasyonu elle temizlersiniz.
    """
    web_driver = DriverFactory.create(settings)
    request.node.stash_driver = web_driver  # hook'lar erisebilsin diye
    yield web_driver

    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed and request.config.getoption("--keep-browser-open"):
        get_logger("driver").warning("Hata sonrasi tarayici acik birakildi.")
        return
    web_driver.quit()


@pytest.fixture
def login_page(driver, settings: Settings) -> LoginPage:
    return LoginPage(driver, settings).open_login_page()


@pytest.fixture
def inventory_page(login_page: LoginPage):
    """Standart kullaniciyla giris yapilmis envanter sayfasi.

    Cogu test giris ekranini test etmez, giris SONRASINI test eder. Bu
    fixture o on kosulu tek satira indirir.
    """
    standard = user("standard")
    return login_page.login_expecting_success(standard.username, standard.password)


@pytest.fixture
def cart_with_two_items(inventory_page):
    """Icinde 2 urun olan sepet - checkout testlerinin ortak baslangici."""
    products = ["Sauce Labs Backpack", "Sauce Labs Bike Light"]
    inventory_page.add_many_to_cart(products)
    cart = inventory_page.header.open_cart()
    return cart, products


# --------------------------------------------------------------------------- #
# Hook'lar: hata aninda teshis toplama
# --------------------------------------------------------------------------- #
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Test sonucunu fixture'lardan erisilebilir hale getirir.

    pytest'te bir fixture, testin gecip gecmedigini dogrudan bilemez. Bu
    standart hook sonucu `item.rep_setup/rep_call/rep_teardown` olarak saklar.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    web_driver = getattr(item, "stash_driver", None)
    if web_driver is None:
        return

    cfg = load_settings()
    log = get_logger("artifacts")
    stamp = f"{item.name}_{datetime.now():%H%M%S}".replace("/", "_").replace("[", "_").replace("]", "")

    if cfg.artifacts.screenshot_on_failure:
        shot = Path(cfg.artifacts.screenshot_dir) / f"{stamp}.png"
        try:
            web_driver.save_screenshot(str(shot))
            log.error("Hata ekran goruntusu: %s", shot)
            # pytest-html raporuna gomulu olarak ekle
            extras = getattr(report, "extras", [])
            try:
                import pytest_html

                extras.append(pytest_html.extras.image(str(shot)))
                extras.append(pytest_html.extras.url(web_driver.current_url, name="Hata URL'si"))
                report.extras = extras
            except ImportError:
                pass
        except Exception as exc:  # tarayici cokmus olabilir
            log.warning("Ekran goruntusu alinamadi: %s", exc)

    if cfg.artifacts.page_source_on_failure:
        source = Path(cfg.artifacts.page_source_dir) / f"{stamp}.html"
        try:
            source.write_text(web_driver.page_source, encoding="utf-8")
            log.error("Hata anindaki HTML: %s", source)
        except Exception as exc:
            log.warning("Sayfa kaynagi kaydedilemedi: %s", exc)

    # Tarayici konsolundaki JS hatalari cogu zaman kok nedeni gosterir
    try:
        severe = [e["message"] for e in web_driver.get_log("browser") if e["level"] == "SEVERE"]
        if severe:
            log.error("Tarayici konsol hatalari:\n%s", "\n".join(severe[:10]))
    except Exception:
        pass


def pytest_configure(config: pytest.Config) -> None:
    Path(PROJECT_ROOT / "reports").mkdir(parents=True, exist_ok=True)


def pytest_html_report_title(report) -> None:
    report.title = "SauceDemo - Selenium + pytest Test Raporu"


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    terminalreporter.write_sep("=", "SELENIUM KOSUM OZETI")
    terminalreporter.write_line(f"  Gecen   : {passed}")
    terminalreporter.write_line(f"  Kalan   : {failed}")
    terminalreporter.write_line(f"  Atlanan : {skipped}")
    terminalreporter.write_line(f"  Rapor   : {PROJECT_ROOT / 'reports' / 'report.html'}")
