"""Uctan uca satin alma senaryolari.

Bu dosya, POM katmaninin ne kadar okunakli bir test dili urettigini gosterir:
asagidaki testlerde tek bir CSS selector veya bekleme kodu YOKTUR.
"""
from __future__ import annotations

import time

import pytest

from pages.login_page import LoginPage
from utils.data_loader import product_price, tax_rate, user

pytestmark = [pytest.mark.e2e]


@pytest.mark.smoke
def test_complete_purchase_happy_path(login_page: LoginPage, customer) -> None:
    """Giris -> urun sec -> sepet -> checkout -> siparis tamamla."""
    standard = user("standard")
    selected = ["Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Onesie"]

    inventory = login_page.login_expecting_success(standard.username, standard.password)
    inventory.add_many_to_cart(selected)
    assert inventory.header.cart_count() == 3

    cart = inventory.header.open_cart()
    assert set(cart.item_names()) == set(selected)

    overview = cart.proceed_to_checkout().submit(**customer)

    totals = overview.totals()
    assert totals.subtotal == round(sum(product_price(p) for p in selected), 2)
    totals.validate(tax_rate=tax_rate())

    complete = overview.finish()

    assert complete.confirmation_header().lower().startswith("thank you")
    assert "dispatched" in complete.confirmation_text().lower()
    assert complete.is_success_image_visible()
    assert complete.header.cart_count() == 0, "Siparis sonrasi sepet temizlenmedi"


@pytest.mark.regression
def test_purchase_then_start_new_order(login_page: LoginPage, customer) -> None:
    """Siparis sonrasi kullanici yeni bir siparise baslayabilmeli."""
    standard = user("standard")
    inventory = login_page.login_expecting_success(standard.username, standard.password)

    complete = (
        inventory.add_to_cart("Sauce Labs Fleece Jacket")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
    )

    inventory_again = complete.back_to_products()

    assert inventory_again.product_count() == 6
    assert inventory_again.header.cart_count() == 0
    assert not inventory_again.is_in_cart("Sauce Labs Fleece Jacket"), (
        "Onceki siparisin urunu hala sepette gorunuyor"
    )


@pytest.mark.slow
@pytest.mark.regression
def test_e2e_with_performance_glitch_user(login_page: LoginPage, customer) -> None:
    """Yavas kullaniciyla ayni akis - bekleme stratejisinin dayaniklilik testi.

    KARSILASTIRMA NOTU:
        Bu test Selenium'da ANCAK explicit wait'ler dogru kuruldugu icin gecer.
        `time.sleep()` ile yazilmis bir suite burada ya kirilir ya da gereksiz
        yere yavaslar. Playwright'ta ayni test ek bir onlem gerektirmez, cunku
        auto-wait varsayilan davranistir.
    """
    slow = user("performance_glitch")
    login_page.timeout = login_page.settings.timeouts.slow_user_wait

    started = time.perf_counter()
    inventory = login_page.login_expecting_success(slow.username, slow.password)
    login_duration = time.perf_counter() - started

    # Yavas kullanicinin gercekten yavas oldugunu da belgeleyelim
    assert login_duration > 1.0, (
        "performance_glitch_user beklenenden hizli - uygulama davranisi degismis olabilir"
    )

    complete = (
        inventory.add_to_cart("Sauce Labs Backpack")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
    )

    assert complete.confirmation_header().lower().startswith("thank you")


@pytest.mark.regression
def test_no_severe_console_errors_during_purchase(login_page: LoginPage, customer) -> None:
    """Satin alma akisi boyunca tarayici konsoluna SEVERE hata dusmemeli.

    KARSILASTIRMA NOTU:
        Selenium'da konsol loglari yalnizca Chromium tabanli tarayicilarda ve
        ancak SONRADAN cekilerek okunur (`get_log('browser')`). Playwright'ta
        `page.on("console")` ile ANLIK ve TUM tarayicilarda dinlenir.
    """
    if login_page.settings.browser.name not in {"chrome", "edge"}:
        pytest.skip("Konsol logu yalnizca Chromium tabanli tarayicilarda okunabilir")

    standard = user("standard")
    inventory = login_page.login_expecting_success(standard.username, standard.password)
    (
        inventory.add_to_cart("Sauce Labs Onesie")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
    )

    errors = inventory.browser_console_errors()

    # BILINEN GURULTUYU AYIKLA:
    #   SauceDemo, backtrace.io telemetri servisine placeholder token ile
    #   istek atar ve her kosumda 401 alir. Bu, TEST EDILEN UYGULAMANIN
    #   bilinen bir davranisidir; bizim akisimizla ilgisi yoktur.
    #   Gercek projelerde bu liste kisa tutulmali ve her maddesi
    #   gerekcelendirilmelidir - aksi halde test hicbir seyi yakalamaz.
    KNOWN_NOISE = ("favicon", "backtrace.io", "events.backtrace")
    blocking = [e for e in errors if not any(n in e.lower() for n in KNOWN_NOISE)]

    assert not blocking, "Akis sirasinda konsol hatalari olustu:\n" + "\n".join(blocking)
