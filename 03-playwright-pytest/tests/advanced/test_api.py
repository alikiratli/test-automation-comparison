"""API TESTLERI - Playwright'in ayni framework icinde sundugu HTTP istemcisi.

NEDEN BU DOSYA VAR?
    Selenium bir TARAYICI OTOMASYON aracidir; API testi icin `requests` gibi
    ayri bir kutuphane, ayri bir test yapisi ve ayri bir raporlama kurmaniz
    gerekir. Robot Framework'te RequestsLibrary eklenir - bu en azindan ayni
    rapor icinde toplanir.

    Playwright'ta `APIRequestContext` framework'un parcasidir:
      * ayni trace icinde gorunur,
      * tarayici context'i ile COOKIE PAYLASABILIR,
      * yani "API ile veri hazirla, UI ile dogrula" akisi dogal olarak kurulur.

NOT: SauceDemo'nun public bir API'si olmadigi icin burada bir sandbox API
kullaniliyor. Amac, YETENEGI gostermektir.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import APIRequestContext, Playwright, expect

from config.settings import API_SANDBOX_URL

pytestmark = [pytest.mark.api]


@pytest.fixture(scope="module")
def api_context(playwright: Playwright) -> APIRequestContext:
    """Tarayici ACMADAN calisan bir HTTP istemcisi.

    DIKKAT: Bu fixture tarayici baslatmaz. API testleri tarayicisiz kostugu
    icin milisaniyeler surer - UI testlerinden 50-100 kat hizli.
    """
    context = playwright.request.new_context(
        base_url=API_SANDBOX_URL,
        extra_http_headers={"Accept": "application/json"},
        timeout=15_000,
    )
    yield context
    context.dispose()


@pytest.mark.smoke
def test_api_get_returns_expected_schema(api_context: APIRequestContext) -> None:
    """GET istegi ve yanit sematik dogrulamasi."""
    response = api_context.get("/posts/1")

    assert response.ok, f"Beklenmeyen durum kodu: {response.status}"
    assert response.status == 200

    payload = response.json()
    for field in ("id", "userId", "title", "body"):
        assert field in payload, f"Yanitta '{field}' alani yok"
    assert payload["id"] == 1


@pytest.mark.regression
def test_api_post_creates_resource(api_context: APIRequestContext) -> None:
    """POST istegi ve olusturma dogrulamasi."""
    response = api_context.post(
        "/posts",
        data={"title": "Otomasyon karsilastirmasi", "body": "Playwright API testi", "userId": 1},
    )

    assert response.status == 201, f"201 bekleniyordu, {response.status} geldi"
    created = response.json()
    assert created["title"] == "Otomasyon karsilastirmasi"


@pytest.mark.regression
def test_api_handles_not_found(api_context: APIRequestContext) -> None:
    """Negatif senaryo: olmayan kaynak 404 donmeli."""
    response = api_context.get("/posts/999999")
    assert response.status == 404


@pytest.mark.regression
def test_api_response_time_is_acceptable(api_context: APIRequestContext) -> None:
    """Basit performans esigi kontrolu."""
    import time

    started = time.perf_counter()
    response = api_context.get("/users")
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert response.ok
    assert elapsed_ms < 5_000, f"API yaniti cok yavas: {elapsed_ms:.0f} ms"
    assert len(response.json()) > 0


@pytest.mark.regression
def test_api_and_ui_share_the_same_context(page, settings) -> None:
    """API ve UI AYNI OTURUMU paylasabilir.

    `page.request` ile yapilan istekler, sayfanin cerezlerini tasir. Gercek
    projelerdeki en degerli kullanimi:

        1. Test verisini API ile HIZLICA olustur (UI'dan form doldurmadan)
        2. Dogrulamayi UI'da yap
        3. Temizligi yine API ile yap

    Bu kalip, UI test sureleri konusunda en buyuk kazanci saglayan tekniktir.
    Selenium'da API cagrisi `requests` ile yapilir ama oturumu paylasmak icin
    cerezleri elle tasimak gerekir.
    """
    page.goto(settings.login_url)

    # page.request: sayfanin oturumunu kullanan HTTP istemcisi
    response = page.request.get(settings.base_url)

    assert response.ok, f"Ana sayfa istegi basarisiz: {response.status}"
    assert "swag labs" in response.text().lower() or "saucedemo" in response.url.lower()
    expect(page.get_by_test_id("login-button")).to_be_visible()
