"""WebDriver fabrikasi.

KARSILASTIRMA NOTU:
    Playwright'ta tarayici baslatmak `sync_playwright().chromium.launch()` ile
    tek satirdir ve tarayici binary'leri Playwright tarafindan surum-kilitli
    olarak indirilir. Selenium'da tarayici SISTEMDEKI tarayicidir; her tarayici
    icin ayri Options sinifi, ayri argumanlar ve ayri sorunlar vardir. Asagidaki
    dosyanin varlik sebebi budur.

    Selenium 4.6+ ile gelen Selenium Manager sayesinde artik surucu (.exe)
    indirmeye gerek kalmadi; yine de tarayici-surucu surum uyumu isletim
    sisteminin sorumlulugundadir.
"""
from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings
from core.logger import get_logger

log = get_logger("driver_factory")

# Konteyner/CI ortamlarinda kararliligi artiran ortak argumanlar
_COMMON_CHROMIUM_ARGS = (
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-infobars",
    "--ignore-certificate-errors",
    "--lang=en-US",
)


class DriverFactory:
    """Ayarlara gore yapilandirilmis bir WebDriver ornegi uretir."""

    @staticmethod
    def create(settings: Settings) -> WebDriver:
        name = settings.browser.name
        log.info(
            "Tarayici baslatiliyor: %s (headless=%s, %sx%s)",
            name,
            settings.browser.headless,
            settings.browser.window_width,
            settings.browser.window_height,
        )

        builders = {
            "chrome": DriverFactory._chrome,
            "firefox": DriverFactory._firefox,
            "edge": DriverFactory._edge,
        }
        if name not in builders:
            raise ValueError(f"Desteklenmeyen tarayici: '{name}'. Secenekler: {list(builders)}")

        driver = builders[name](settings)
        DriverFactory._apply_common(driver, settings)
        log.info("Tarayici hazir. Oturum: %s", driver.session_id)
        return driver

    # ------------------------------------------------------------------ #
    @staticmethod
    def _chrome(settings: Settings) -> WebDriver:
        options = ChromeOptions()
        for arg in _COMMON_CHROMIUM_ARGS:
            options.add_argument(arg)
        if settings.browser.headless:
            # "new" headless modu, eski headless'tan farkli olarak gercek
            # render motorunu kullanir; gorsel testlerde fark yaratir.
            options.add_argument("--headless=new")
        options.add_argument(
            f"--window-size={settings.browser.window_width},{settings.browser.window_height}"
        )
        # SauceDemo'nun sifre kaydetme balonunu bastir
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            },
        )
        # DIKKAT - GERCEK HAYATTAN BIR TUZAK:
        #   Bircok Selenium ornegi burada
        #       options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #   satirini onerir. Chrome 151 ile bu secenek tarayicinin acilir
        #   acilmaz kapanmasina ("Chrome instance exited") yol acmaktadir.
        #   Bilerek KULLANMIYORUZ. Selenium'un tarayici surumlerine bagimliligi
        #   tam olarak boyle gorunur: kod degismez, tarayici guncellenir, suite
        #   toptan kirmizi olur. Playwright'ta tarayici surumu pakete kilitli
        #   oldugu icin bu sinif hatalar yasanmaz.
        options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
        return webdriver.Chrome(options=options)

    @staticmethod
    def _firefox(settings: Settings) -> WebDriver:
        options = FirefoxOptions()
        if settings.browser.headless:
            options.add_argument("-headless")
        options.add_argument(f"--width={settings.browser.window_width}")
        options.add_argument(f"--height={settings.browser.window_height}")
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("signon.rememberSignons", False)
        options.set_preference("intl.accept_languages", "en-US, en")
        return webdriver.Firefox(options=options)

    @staticmethod
    def _edge(settings: Settings) -> WebDriver:
        options = EdgeOptions()
        for arg in _COMMON_CHROMIUM_ARGS:
            options.add_argument(arg)
        if settings.browser.headless:
            options.add_argument("--headless=new")
        options.add_argument(
            f"--window-size={settings.browser.window_width},{settings.browser.window_height}"
        )
        return webdriver.Edge(options=options)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_common(driver: WebDriver, settings: Settings) -> None:
        driver.set_page_load_timeout(settings.timeouts.page_load)
        driver.set_script_timeout(settings.timeouts.script)

        # DIKKAT: implicit_wait 0 birakiliyor. implicit + explicit karisimi,
        # WebDriver spesifikasyonunda tanimsiz davranisa yol acar ve bekleme
        # sureleri toplanarak testleri yavaslatir.
        driver.implicitly_wait(settings.browser.implicit_wait)

        if not settings.browser.headless:
            driver.set_window_size(
                settings.browser.window_width, settings.browser.window_height
            )
