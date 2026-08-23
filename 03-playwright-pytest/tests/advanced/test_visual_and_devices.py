"""GORSEL REGRESYON, CIHAZ EMULASYONU ve COKLU SEKME.

Bu dosyadaki yeteneklerin Selenium/Robot Framework'te ya karsiligi yoktur ya
da ek kutuphane + ek altyapi gerektirir.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, Playwright, expect

from pages.login_page import LoginPage
from utils.data_loader import user

BASELINE_DIR = Path(__file__).resolve().parents[2] / "reports" / "visual_baseline"


@pytest.mark.visual
def test_login_page_visual_snapshot(page: Page, settings) -> None:
    """Login sayfasinin gorsel anlik goruntusunu alir ve referansla karsilastirir.

    KARSILASTIRMA NOTU:
        Playwright'in TypeScript surumunde bu tek satirdir:
            await expect(page).toHaveScreenshot('login.png');
        Python surumunde hazir bir gorsel karsilastirici YOKTUR; asagida
        temel bir uygulama gosteriyoruz (dosya boyutu/bayt karsilastirmasi).
        Gercek projelerde `pytest-playwright-visual` veya Applitools gibi bir
        cozum tercih edilir.

        Selenium'da ise ekran goruntusu almak mumkundur ama:
          - tam sayfa goruntusu icin kaydirma + birlestirme gerekir,
          - animasyon/font farklari icin maskeleme destegi yoktur.
        Playwright'ta `full_page=True`, `mask=[...]` ve `animations="disabled"`
        parametreleri hazirdir.
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    page.goto(settings.login_url)

    current = page.screenshot(
        full_page=True,
        animations="disabled",  # animasyonlari dondur -> kararli goruntu
        caret="hide",           # imleci gizle -> piksel gurultusu azalir
    )

    baseline_file = BASELINE_DIR / "login_page.png"
    if not baseline_file.exists():
        baseline_file.write_bytes(current)
        pytest.skip("Referans goruntu olusturuldu; sonraki kosumda karsilastirilacak")

    baseline = baseline_file.read_bytes()
    # Basit bir tolerans: boyut farki %5'ten fazlaysa gorsel degismis kabul et
    difference_ratio = abs(len(current) - len(baseline)) / max(len(baseline), 1)
    assert difference_ratio < 0.05, (
        f"Login sayfasi gorsel olarak degismis olabilir "
        f"(boyut farki %{difference_ratio * 100:.1f})"
    )


@pytest.mark.visual
def test_element_level_screenshot(inventory_page) -> None:
    """Tek bir bilesenin goruntusunu alir.

    Locator seviyesinde ekran goruntusu, gorsel regresyonu tum sayfa yerine
    RISKLI BILESENE odaklamayi saglar - cok daha az kirilgandir.
    """
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    first_card = inventory_page.items.first

    image = first_card.screenshot(path=str(BASELINE_DIR / "first_product_card.png"))
    assert len(image) > 1000, "Bilesen goruntusu bos gorunuyor"


@pytest.mark.visual
def test_mobile_device_emulation(playwright: Playwright, browser: Browser, settings) -> None:
    """iPhone 13 emulasyonu ile responsive davranis testi.

    Playwright ~130 hazir cihaz profili tasir: viewport, user agent, cihaz
    piksel orani, dokunmatik destegi ve mobil bayragi birlikte gelir.

        Selenium'da: yalnizca pencere boyutunu degistirebilirsiniz. Gercek
        mobil test icin Appium ayri bir altyapi olarak kurulur.
        Robot Framework'te: SeleniumLibrary uzerinden ayni sinirlar gecerli.
    """
    iphone = playwright.devices["iPhone 13"]
    context = browser.new_context(**iphone, base_url=settings.base_url)
    try:
        page = context.new_page()
        standard = user("standard")

        inventory = LoginPage(page, settings).open_login_page().login_expecting_success(
            standard.username, standard.password
        )

        expect(inventory.inventory_list).to_be_visible()
        expect(inventory.items).to_have_count(6)

        viewport = page.viewport_size
        assert viewport["width"] < 500, f"Mobil viewport bekleniyordu: {viewport}"
        assert page.evaluate("() => navigator.maxTouchPoints") > 0, (
            "Dokunmatik destegi emule edilmemis"
        )
    finally:
        context.close()


@pytest.mark.regression
def test_multiple_tabs_in_same_context(inventory_page) -> None:
    """Ayni oturumda ikinci sekme acar.

    Playwright'ta bir context birden fazla sayfa (sekme) tutabilir ve
    aralarinda gecis anlik olur. Selenium'da sekme yonetimi
    `driver.switch_to.window(handle)` ile yapilir; handle'lari elle takip
    etmek gerekir ve yanlis sekmede kalmak sik yasanan bir hatadir.
    """
    inventory_page.add_to_cart("Sauce Labs Backpack")

    context = inventory_page.page.context
    second_tab = context.new_page()
    try:
        second_tab.goto(inventory_page.settings.cart_url)

        from pages.cart_page import CartPage

        cart = CartPage(second_tab, inventory_page.settings)
        # Ayni context = ayni oturum: sepet ikinci sekmede de gorunur
        cart.expect_item_count(1)
        cart.expect_contains("Sauce Labs Backpack")
    finally:
        second_tab.close()


@pytest.mark.accessibility
def test_basic_accessibility_checks(inventory_page) -> None:
    """Temel erisilebilirlik kontrolleri.

    Playwright'in `get_by_role` locator'lari, ERISILEBILIRLIK AGACI uzerinden
    calisir. Yani bir elemani "role=button, name=Add to cart" diye bulmak,
    hem testi kirilmaz yapar hem de o elemanin ekran okuyucular tarafindan
    dogru algilanabildigini KANITLAR.

    Selenium'da erisilebilirlik agacina erisim yoktur; ancak axe-core gibi bir
    JS kutuphanesini sayfaya enjekte ederek benzer sonuc alinabilir.
    """
    page = inventory_page.page

    # 1. Tum "Add to cart" butonlari erisilebilir isimle bulunabilmeli
    add_buttons = page.get_by_role("button", name="Add to cart")
    expect(add_buttons).to_have_count(6)

    # 2. Tum gorsellerin alt metni olmali
    images_without_alt = page.evaluate(
        """() => Array.from(document.querySelectorAll('img'))
               .filter(img => !img.alt || img.alt.trim() === '').length"""
    )
    assert images_without_alt == 0, (
        f"{images_without_alt} gorselde alt metni eksik - ekran okuyucular icin sorun"
    )

    # 3. Form alanlari klavye ile gezilebilmeli
    page.keyboard.press("Tab")
    focused = page.evaluate("() => document.activeElement.tagName")
    assert focused not in (None, "BODY"), "Tab tusuyla odaklanilabilir eleman yok"


@pytest.mark.accessibility
@pytest.mark.xfail(
    reason=(
        "GERCEK BIR KUSUR: SauceDemo envanter sayfasinda hicbir heading (h1-h6) "
        "yoktur; sayfa basligi 'Products' bir <span data-test='title'> olarak "
        "islenmistir. Ekran okuyucu kullanicilari sayfa yapisinda gezinemez "
        "(WCAG 2.1 - 1.3.1 Info and Relationships). Bu testi ilk kosumda "
        "erisilebilirlik kontrolu KENDILIGINDEN buldu. Kusur duzeltildiginde "
        "test 'xpass' verecek ve isaret kaldirilmalidir."
    ),
    strict=False,
)
def test_page_has_heading_structure(inventory_page) -> None:
    """Sayfada anlamli bir baslik hiyerarsisi olmali.

    `get_by_role("heading")` ERISILEBILIRLIK AGACINI sorgular; CSS'e degil,
    sayfanin ekran okuyucuya nasil gorundugune bakar. Selenium'da bu bilgiye
    erisimin dogrudan bir yolu yoktur.
    """
    headings = inventory_page.page.get_by_role("heading")
    assert headings.count() >= 1, (
        "Sayfada hicbir heading yok - ekran okuyucu kullanicilari icin engel"
    )
