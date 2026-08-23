"""Checkout formu ve tutar hesaplamalari."""
from __future__ import annotations

import pytest

from core.exceptions import BusinessRuleError
from utils.data_loader import product_price, tax_rate

pytestmark = [pytest.mark.checkout]


@pytest.mark.smoke
def test_checkout_form_accepts_valid_data(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    info = cart.proceed_to_checkout()

    overview = info.submit(**customer)

    assert "checkout-step-two.html" in overview.current_url
    assert overview.is_visible(overview.FINISH_BUTTON)


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
    """Zorunlu alan validasyonu - alanlar SIRAYLA dogrulanmali.

    Hepsi bos oldugunda uygulama ilk hatayi (First Name) gostermelidir; bu,
    validasyon sirasinin da test edildigi anlamina gelir.
    """
    cart, _ = cart_with_two_items
    info = cart.proceed_to_checkout()

    result = info.submit(first, last, postal)

    assert result is info, "Hatali form ile bir sonraki adima gecildi"
    assert result.error_message() == expected_error


@pytest.mark.smoke
def test_overview_totals_are_mathematically_correct(cart_with_two_items, customer) -> None:
    """UI DEGIL, IS KURALI testi: KDV ve genel toplam dogru hesaplanmali."""
    cart, products = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    totals = overview.totals()
    expected_subtotal = round(sum(product_price(p) for p in products), 2)

    assert totals.subtotal == expected_subtotal, "Ara toplam sepetle uyusmuyor"
    # validate() hatali durumda BusinessRuleError firlatir
    totals.validate(tax_rate=tax_rate())


@pytest.mark.regression
def test_overview_lists_exactly_the_cart_items(cart_with_two_items, customer) -> None:
    cart, products = cart_with_two_items
    cart_names = cart.item_names()

    overview = cart.proceed_to_checkout().submit(**customer)

    assert set(overview.item_names()) == set(cart_names) == set(products)
    assert len(overview.item_names()) == 2, "Ozet sayfasinda satir sayisi hatali"


@pytest.mark.regression
def test_overview_shows_payment_and_shipping_info(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    assert overview.payment_information().strip(), "Odeme bilgisi bos"
    assert overview.shipping_information().strip(), "Kargo bilgisi bos"


@pytest.mark.regression
def test_cancel_from_information_returns_to_cart(cart_with_two_items) -> None:
    cart, products = cart_with_two_items
    info = cart.proceed_to_checkout()

    back = info.cancel()

    assert back.item_count() == 2, "Iptal sonrasi sepet bozuldu"
    assert set(back.item_names()) == set(products)


@pytest.mark.regression
def test_cancel_from_overview_returns_to_inventory(cart_with_two_items, customer) -> None:
    cart, _ = cart_with_two_items
    overview = cart.proceed_to_checkout().submit(**customer)

    inventory = overview.cancel()

    assert "inventory.html" in inventory.current_url
    assert inventory.header.cart_count() == 2, "Iptal sepeti bosaltmamali"


@pytest.mark.regression
def test_tax_calculation_across_different_cart_sizes(inventory_page, customer) -> None:
    """Farkli sepet buyukluklerinde KDV matematigi dogrulanir.

    Tek testte 3 farkli senaryo kosarak tarayici acilis maliyetinden kaciniyoruz.
    Bu, Selenium'da paralellik pahali oldugu icin bilincli bir tercihtir.
    """
    scenarios = [
        ["Sauce Labs Onesie"],
        ["Sauce Labs Backpack", "Sauce Labs Fleece Jacket"],
        ["Sauce Labs Bike Light", "Sauce Labs Bolt T-Shirt", "Sauce Labs Onesie"],
    ]

    for products in scenarios:
        inventory_page.add_many_to_cart(products)
        overview = (
            inventory_page.header.open_cart().proceed_to_checkout().submit(**customer)
        )

        totals = overview.totals()
        expected = round(sum(product_price(p) for p in products), 2)
        assert totals.subtotal == expected, f"{products} icin ara toplam hatali"

        try:
            totals.validate(tax_rate=tax_rate())
        except BusinessRuleError as exc:
            pytest.fail(f"{products} icin tutar hatasi: {exc}")

        # Bir sonraki senaryo icin temiz baslangic
        inventory = overview.cancel()
        inventory.header.reset_app_state()
