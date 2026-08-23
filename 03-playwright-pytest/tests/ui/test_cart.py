"""Sepet islemleri testleri - Playwright surumu."""
from __future__ import annotations

import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage
from utils.data_loader import product_names, product_price, user

pytestmark = [pytest.mark.cart]


@pytest.mark.smoke
def test_cart_is_empty_at_start(inventory_page: InventoryPage) -> None:
    inventory_page.header.expect_cart_count(0)
    cart = inventory_page.header.open_cart()
    cart.expect_empty()


@pytest.mark.smoke
def test_add_single_product_updates_badge(inventory_page: InventoryPage) -> None:
    inventory_page.add_to_cart("Sauce Labs Backpack")
    inventory_page.header.expect_cart_count(1)
    inventory_page.expect_in_cart("Sauce Labs Backpack")


@pytest.mark.regression
def test_add_all_products(inventory_page: InventoryPage) -> None:
    names = product_names()
    for index, name in enumerate(names, start=1):
        inventory_page.add_to_cart(name)
        inventory_page.header.expect_cart_count(index)

    cart = inventory_page.header.open_cart()
    cart.expect_item_count(len(names))
    assert set(cart.get_item_names()) == set(names)


@pytest.mark.regression
def test_remove_from_inventory_page(inventory_page: InventoryPage) -> None:
    inventory_page.add_many_to_cart(["Sauce Labs Backpack", "Sauce Labs Onesie"])
    inventory_page.remove_from_cart("Sauce Labs Onesie")

    inventory_page.header.expect_cart_count(1)
    inventory_page.expect_not_in_cart("Sauce Labs Onesie")
    inventory_page.expect_in_cart("Sauce Labs Backpack")


@pytest.mark.regression
def test_remove_from_cart_page(cart_with_two_items) -> None:
    cart, products = cart_with_two_items
    cart.remove(products[0])

    cart.expect_item_count(1)
    assert not cart.contains(products[0])
    cart.expect_contains(products[1])
    cart.header.expect_cart_count(1)


@pytest.mark.regression
def test_cart_prices_and_quantities(cart_with_two_items) -> None:
    cart, products = cart_with_two_items

    for line in cart.lines():
        assert line.quantity == 1
        assert line.price == product_price(line.name)

    assert cart.subtotal() == round(sum(product_price(p) for p in products), 2)


@pytest.mark.regression
def test_cart_persists_after_navigation(cart_with_two_items) -> None:
    cart, products = cart_with_two_items

    inventory = cart.continue_shopping()
    inventory.header.expect_cart_count(2)

    inventory.page.reload()
    inventory.header.expect_cart_count(2)

    back = inventory.header.open_cart()
    assert set(back.get_item_names()) == set(products)


@pytest.mark.regression
def test_cart_survives_logout_login(inventory_page: InventoryPage) -> None:
    """Characterization test: uygulamanin MEVCUT davranisini kayit altina alir."""
    inventory_page.add_to_cart("Sauce Labs Backpack")
    login = inventory_page.header.logout()

    standard = user("standard")
    again = login.login_expecting_success(standard.username, standard.password)
    again.header.expect_cart_count(1)


@pytest.mark.regression
def test_reset_app_state_clears_cart(inventory_page: InventoryPage) -> None:
    inventory_page.add_many_to_cart(["Sauce Labs Backpack", "Sauce Labs Bike Light"])
    inventory_page.header.expect_cart_count(2)

    inventory_page.header.reset_app_state()
    inventory_page.header.expect_cart_count(0)


@pytest.mark.regression
def test_cart_state_is_isolated_between_contexts(browser, settings) -> None:
    """IKI AYRI OTURUM AYNI ANDA - SELENIUM'DA MALIYETLI, BURADA UCUZ.

    Iki farkli BrowserContext, iki farkli kullanici gibi davranir: cerezleri
    ve localStorage'lari tamamen ayridir. Ayni tarayici surecinde calisirlar.

    Selenium'da ayni senaryo IKI AYRI TARAYICI SURECI acmayi gerektirir
    (~2-4 sn ek maliyet ve iki kat RAM). Playwright'ta iki context ~50 ms.
    """
    from pages.login_page import LoginPage

    standard = user("standard")

    context_a = browser.new_context(base_url=settings.base_url)
    context_b = browser.new_context(base_url=settings.base_url)
    try:
        page_a, page_b = context_a.new_page(), context_b.new_page()

        inventory_a = LoginPage(page_a, settings).open_login_page().login_expecting_success(
            standard.username, standard.password
        )
        inventory_b = LoginPage(page_b, settings).open_login_page().login_expecting_success(
            standard.username, standard.password
        )

        inventory_a.add_many_to_cart(["Sauce Labs Backpack", "Sauce Labs Onesie"])

        inventory_a.header.expect_cart_count(2)
        inventory_b.header.expect_cart_count(0)  # B oturumu etkilenmedi
    finally:
        context_a.close()
        context_b.close()


@pytest.mark.negative
def test_checkout_with_empty_cart(inventory_page: InventoryPage, customer) -> None:
    """Bos sepetle checkout - uygulamanin gercek davranisini belgeler."""
    cart = inventory_page.header.open_cart()
    cart.expect_empty()

    overview = cart.proceed_to_checkout().submit(**customer)
    totals = overview.totals()

    assert totals.subtotal == 0.0
    assert totals.total == round(totals.subtotal + totals.tax, 2)
