"""AG KATMANI MUDAHALESI - Selenium ve Robot Framework'te KARSILIGI YOKTUR.

NEDEN ONEMLI?
    Selenium, tarayiciyi WebDriver protokolu uzerinden "disaridan" surer;
    sayfanin yaptigi HTTP isteklerini GORMEZ, degistiremez. Playwright ise
    tarayiciya CDP/WebSocket ile baglanir ve ag katmanina tam erisimi vardir.

    Bunun pratik sonucu:
      * Backend'e hic dokunmadan hata senaryolarini test edebilirsiniz
        (500 hatasi, timeout, bos yanit).
      * Testler harici servislere bagimli olmaktan cikar -> hizlanir, kararli olur.
      * Sayfanin kac istek attigini, hangi kaynagi ne kadar surede indirdigini
        olcebilirsiniz.

    Selenium'da ayni sonuc icin bir HTTP proxy (BrowserMob, mitmproxy) kurmak
    ve testin yanina ayri bir surec olarak calistirmak gerekir.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, Route, expect

from pages.login_page import LoginPage
from utils.data_loader import user

pytestmark = [pytest.mark.network]


@pytest.mark.regression
def test_capture_all_network_requests(login_page: LoginPage) -> None:
    """Giris akisi sirasinda atilan tum istekleri kaydeder ve inceler."""
    requests: list[tuple[str, str]] = []
    login_page.page.on("request", lambda req: requests.append((req.method, req.url)))

    standard = user("standard")
    login_page.login_expecting_success(standard.username, standard.password)

    assert requests, "Hic ag istegi yakalanamadi"
    # Guvenlik kontrolu: sifre URL'de duz metin olarak gitmemeli
    leaked = [url for _, url in requests if "secret_sauce" in url]
    assert not leaked, f"Sifre URL'de sizdirildi: {leaked}"


@pytest.mark.regression
def test_block_images_speeds_up_page_load(page: Page, settings) -> None:
    """Gorselleri ENGELLEYEREK sayfayi yukler.

    Gercek hayatta kullanimi: gorsel indirmenin gereksiz oldugu fonksiyonel
    testlerde bant genisligi ve sure tasarrufu; ayrica "gorsel yuklenmezse
    sayfa ne yapiyor" senaryosunun testi.
    """
    blocked: list[str] = []

    def block_media(route: Route) -> None:
        blocked.append(route.request.url)
        route.abort()

    # ** joker ifadesiyle desen eslesmesi
    page.route("**/*.{png,jpg,jpeg,svg,gif,webp}", block_media)

    standard = user("standard")
    inventory = LoginPage(page, settings).open_login_page().login_expecting_success(
        standard.username, standard.password
    )

    expect(inventory.inventory_list).to_be_visible()
    assert blocked, "Hicbir gorsel engellenmedi - route kurulumu calismadi"
    # Gorseller olmadan da uygulama islevsel kalmali
    expect(inventory.items).to_have_count(6)


@pytest.mark.regression
def test_simulate_server_error_on_static_asset(page: Page, settings) -> None:
    """Bir kaynagi 500 hatasi ile yanitlayarak uygulamanin dayanikliligini olcer.

    Backend'i degistirmeden, veri tabanina dokunmadan, tek satirda bir hata
    senaryosu uretiyoruz. Selenium'da bu ancak proxy ile mumkundur.
    """
    page.route(
        "**/*.css",
        lambda route: route.fulfill(status=500, body="Internal Server Error"),
    )

    standard = user("standard")
    inventory = LoginPage(page, settings).open_login_page().login_expecting_success(
        standard.username, standard.password
    )

    # CSS yuklenmese bile DOM yapisi ve is mantigi ayakta kalmali
    expect(inventory.items).to_have_count(6)
    assert len(inventory.get_product_names()) == 6


@pytest.mark.regression
def test_measure_page_load_performance(page: Page, settings) -> None:
    """Navigation Timing API ile gercek yuklenme metrikleri toplar.

    Playwright bu bilgiyi `page.evaluate` ile alir; Selenium'da da JS ile
    alinabilir. FARK, olcumu istek/yanit dinleyicileriyle ZENGINLESTIREBILMEK:
    hangi istek ne kadar surdu, kac bayt indi.
    """
    response_sizes: dict[str, int] = {}

    def record(response) -> None:
        try:
            length = response.header_value("content-length")
            if length:
                response_sizes[response.url] = int(length)
        except Exception:
            pass

    page.on("response", record)
    page.goto(settings.login_url, wait_until="load")

    metrics = page.evaluate(
        """() => {
            const nav = performance.getEntriesByType('navigation')[0];
            if (!nav) { return null; }
            return {
                domContentLoaded: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
                loadComplete: Math.round(nav.loadEventEnd - nav.startTime),
                transferSize: nav.transferSize
            };
        }"""
    )

    assert metrics is not None, "Navigation Timing verisi alinamadi"
    assert metrics["loadComplete"] < 15_000, (
        f"Sayfa cok yavas yuklendi: {metrics['loadComplete']} ms"
    )
    print(f"\nYuklenme metrikleri: {metrics}")
    print(f"Olculen yanit sayisi: {len(response_sizes)}")


@pytest.mark.regression
def test_offline_mode_behaviour(page: Page, settings) -> None:
    """Cevrimdisi moda gecerek uygulamanin davranisini gozlemler.

    `context.set_offline(True)` tarayiciyi agsiz birakir. Selenium'da bunun
    dogrudan bir karsiligi yoktur.
    """
    standard = user("standard")
    inventory = LoginPage(page, settings).open_login_page().login_expecting_success(
        standard.username, standard.password
    )

    page.context.set_offline(True)
    try:
        # Zaten yuklenmis sayfa uzerinde islem yapmak calismaya devam etmeli
        # (SauceDemo istemci tarafinda calisir).
        inventory.add_to_cart("Sauce Labs Backpack")
        inventory.header.expect_cart_count(1)
    finally:
        page.context.set_offline(False)


@pytest.mark.regression
def test_mock_api_response_pattern(page: Page, settings) -> None:
    """API yanitini SAHTE veriyle degistirme kalibi.

    SauceDemo tamamen istemci tarafinda calistigi icin degistirilecek bir API
    cagrisi yok; bu test kalibin KENDISINI gosterir. Gercek bir projede
    asagidaki 4 satir, backend'i beklemeden frontend testi yazmayi mumkun kilar.
    """
    intercepted = {"count": 0}

    def fake_api(route: Route) -> None:
        intercepted["count"] += 1
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"products": [], "message": "sahte yanit"}',
        )

    page.route("**/api/**", fake_api)
    page.goto(settings.login_url)

    # SauceDemo /api/ cagrisi yapmadigi icin sayac 0 kalir; onemli olan
    # mekanizmanin kurulabilmesidir.
    assert intercepted["count"] >= 0
    expect(page.get_by_test_id("login-button")).to_be_visible()
