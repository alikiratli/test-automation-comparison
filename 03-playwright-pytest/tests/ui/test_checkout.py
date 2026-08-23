"""Checkout formu ve tutar hesaplamalari - Playwright surumu."""
from __future__ import annotations

import pytest
from playwright.sync_api import expect

from utils.data_loader import product_price, tax_rate

pytestmark = [pytest.mark.checkout]


@pytest.mark.smoke
def test_checkout_form_accepts_valid_data(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)
    expect(overview.finish_button).to_be_visible()


@pytest.mark.negative
@pytest.mark.parametrize(
    "first,last,postal,expected_error",
    [
        ("", "Kiratli", "34710", "Error: First Name is required"),
        ("Ali", "", "34710", "Error: Last Name is required"),
        ("Ali", "Kiratli", "", "Error: Postal Code is required"),
        ("", "", "", "Error: First Name is required"),
    ],
    ids=["ad_bos", "soyad_bos", "posta_kodu_bos", "hepsi_bos"],
)
def test_checkout_form_validation(
    cart_with_two_items, first: str, last: str, postal: str, expected_error: str
) -> None:
    cart, _ = cart_with_two_items
    info = cart.proceed_to_checkout()

    result = info.submit(first, last, postal)

    assert result is info, "Hatali form ile bir sonraki adima gecildi"
    result.expect_error(expected_error)


@pytest.mark.smoke
def test_overview_totals_are_mathematically_correct(cart_with_two_items, customer) -> None:
    """IS KURALI TESTI: KDV ve genel toplam matematigi."""
    cart, products = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    totals = overview.totals()
    assert totals.subtotal == round(sum(product_price(p) for p in products), 2)
    totals.validate(tax_rate=tax_rate())


@pytest.mark.regression
def test_overview_lists_exactly_the_cart_items(cart_with_two_items, customer) -> None:
    cart, products = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    expect(overview.cart_items).to_have_count(2)
    assert set(overview.get_item_names()) == set(products)


@pytest.mark.regression
def test_overview_shows_payment_and_shipping_info(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    expect(overview.payment_info).not_to_be_empty()
    expect(overview.shipping_info).not_to_be_empty()


@pytest.mark.regression
def test_cancel_from_information_returns_to_cart(cart_with_two_items) -> None:
    cart, products = cart_with_two_items
    back = cart.proceed_to_checkout().cancel()

    back.expect_item_count(2)
    assert set(back.get_item_names()) == set(products)


@pytest.mark.regression
def test_cancel_from_overview_returns_to_inventory(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    inventory = cart.proceed_to_checkout().submit(**customer).cancel()

    expect(inventory.inventory_list).to_be_visible()
    inventory.header.expect_cart_count(2)


@pytest.mark.regression
@pytest.mark.parametrize(
    "products",
    [
        ["Sauce Labs Onesie"],
        ["Sauce Labs Backpack", "Sauce Labs Fleece Jacket"],
        ["Sauce Labs Bike Light", "Sauce Labs Bolt T-Shirt", "Sauce Labs Onesie"],
    ],
    ids=["tek_urun", "iki_urun", "uc_urun"],
)
def test_tax_calculation_across_cart_sizes(inventory_page, customer, products) -> None:
    """Farkli sepet buyukluklerinde KDV matematigi.

    KARSILASTIRMA NOTU:
        Selenium surumunde bu 3 senaryo TEK TESTTE, dongü icinde kosuyordu -
        cunku her parametre yeni bir tarayici acmak demekti (~2 sn x 3).
        Playwright'ta her parametre yeni bir CONTEXT acar (~50 ms x 3), bu
        yuzden senaryolari ayirmak bedava. Ayirmanin faydasi: bir senaryo
        kalirsa digerleri yine kosar ve raporda ayri satir olarak gorunur.
    """
    inventory_page.add_many_to_cart(products)
    overview = inventory_page.header.open_cart().proceed_to_checkout().submit(**customer)

    totals = overview.totals()
    assert totals.subtotal == round(sum(product_price(p) for p in products), 2)
    totals.validate(tax_rate=tax_rate())
