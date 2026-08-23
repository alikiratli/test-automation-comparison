"""Uctan uca satin alma senaryolari - Playwright surumu."""
from __future__ import annotations

import time

import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage
from utils.data_loader import product_names, product_price, tax_rate, user

pytestmark = [pytest.mark.e2e]


@pytest.mark.smoke
def test_complete_purchase_happy_path(login_page: LoginPage, customer) -> None:
    standard = user("standard")
    selected = ["Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Onesie"]

    inventory = login_page.login_expecting_success(standard.username, standard.password)
    inventory.add_many_to_cart(selected)
    inventory.header.expect_cart_count(3)

    cart = inventory.header.open_cart()
    assert set(cart.get_item_names()) == set(selected)

    overview = cart.proceed_to_checkout().submit(**customer)
    totals = overview.totals()
    assert totals.subtotal == round(sum(product_price(p) for p in selected), 2)
    totals.validate(tax_rate=tax_rate())

    overview.finish().expect_order_confirmed()


@pytest.mark.regression
def test_purchase_all_products(login_page: LoginPage, customer) -> None:
    """En buyuk sepet senaryosu - 6 urun."""
    standard = user("standard")
    all_products = product_names()

    inventory = login_page.login_expecting_success(standard.username, standard.password)
    inventory.add_many_to_cart(all_products)

    overview = inventory.header.open_cart().proceed_to_checkout().submit(**customer)
    assert set(overview.get_item_names()) == set(all_products)
    overview.totals().validate(tax_rate=tax_rate())

    overview.finish().expect_order_confirmed()


@pytest.mark.regression
def test_purchase_then_start_new_order(login_page: LoginPage, customer) -> None:
    standard = user("standard")
    inventory = login_page.login_expecting_success(standard.username, standard.password)

    complete = (
        inventory.add_to_cart("Sauce Labs Fleece Jacket")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
    )

    again = complete.back_to_products()
    expect(again.items).to_have_count(6)
    again.header.expect_cart_count(0)
    again.expect_not_in_cart("Sauce Labs Fleece Jacket")


@pytest.mark.slow
@pytest.mark.regression
def test_e2e_with_performance_glitch_user(login_page: LoginPage, customer) -> None:
    """Yavas kullaniciyla ayni akis.

    KARSILASTIRMA NOTU:
        Selenium surumunde bu test, explicit wait'ler dogru kuruldugu icin
        geciyordu. Burada ek bir onlem YOK: auto-wait varsayilan davranis.
        Tek yaptigimiz ust siniri yukseltmek.
    """
    slow = user("performance_glitch")
    login_page.page.set_default_timeout(login_page.settings.slow_user_timeout)

    started = time.perf_counter()
    inventory = login_page.login_expecting_success(slow.username, slow.password)
    duration = time.perf_counter() - started

    assert duration > 1.0, "performance_glitch_user beklenenden hizli"

    (
        inventory.add_to_cart("Sauce Labs Backpack")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
        .expect_order_confirmed()
    )


@pytest.mark.regression
def test_no_console_errors_during_purchase(login_page: LoginPage, customer) -> None:
    """Akis boyunca konsola hata dusmemeli.

    KARSILASTIRMA NOTU:
        Selenium surumunde bu test yalnizca Chromium'da kosabiliyor ve
        `get_log('browser')` ile SONRADAN cekiliyordu. Burada konsol olayi
        conftest.py'de ANLIK dinleniyor, chromium/firefox/webkit hepsinde
        calisiyor.
    """
    standard = user("standard")
    inventory = login_page.login_expecting_success(standard.username, standard.password)

    (
        inventory.add_to_cart("Sauce Labs Onesie")
        .header.open_cart()
        .proceed_to_checkout()
        .submit(**customer)
        .finish()
    )

    # SauceDemo'nun bilinen telemetri gurultusu (backtrace.io 401) ayiklanir.
    KNOWN_NOISE = ("favicon", "backtrace.io", "events.backtrace")
    errors = [
        e
        for e in inventory.collect_console_errors()
        if not any(noise in e.lower() for noise in KNOWN_NOISE)
    ]
    assert not errors, "Konsol hatalari:\n" + "\n".join(errors)


@pytest.mark.regression
def test_menu_items_and_page_titles(inventory_page) -> None:
    items = inventory_page.header.get_menu_items()
    assert items == ["All Items", "About", "Logout", "Reset App State"]

    assert inventory_page.title == "Swag Labs"
    expect(inventory_page.header.app_logo).to_have_text("Swag Labs")
