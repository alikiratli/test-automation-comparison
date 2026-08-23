"""Sepet islemleri testleri."""
from __future__ import annotations

import pytest

from pages.inventory_page import InventoryPage
from utils.data_loader import product_names, product_price

pytestmark = [pytest.mark.cart]


@pytest.mark.smoke
def test_cart_is_empty_at_start(inventory_page: InventoryPage) -> None:
    assert inventory_page.header.cart_count() == 0, "Yeni oturumda sepet dolu"
    cart = inventory_page.header.open_cart()
    assert cart.is_empty()


@pytest.mark.smoke
def test_add_single_product_updates_badge(inventory_page: InventoryPage) -> None:
    inventory_page.add_to_cart("Sauce Labs Backpack")

    assert inventory_page.header.cart_count() == 1
    assert inventory_page.is_in_cart("Sauce Labs Backpack"), (
        "Buton 'Remove' durumuna gecmedi"
    )


@pytest.mark.regression
def test_add_all_products(inventory_page: InventoryPage) -> None:
    """Tum urunler tek tek eklenirken rozet dogru artmali."""
    names = product_names()
    for index, name in enumerate(names, start=1):
        inventory_page.add_to_cart(name)
        assert inventory_page.header.cart_count() == index, (
            f"{index}. urun sonrasi rozet yanlis"
        )

    cart = inventory_page.header.open_cart()
    assert cart.item_count() == len(names)
    assert set(cart.item_names()) == set(names)


@pytest.mark.regression
def test_remove_from_inventory_page(inventory_page: InventoryPage) -> None:
    inventory_page.add_many_to_cart(["Sauce Labs Backpack", "Sauce Labs Onesie"])
    assert inventory_page.header.cart_count() == 2

    inventory_page.remove_from_cart("Sauce Labs Onesie")

    assert inventory_page.header.cart_count() == 1
    assert not inventory_page.is_in_cart("Sauce Labs Onesie")
    assert inventory_page.is_in_cart("Sauce Labs Backpack")


@pytest.mark.regression
def test_remove_from_cart_page(cart_with_two_items) -> None:
    cart, products = cart_with_two_items
    cart.remove(products[0])

    assert cart.item_count() == 1
    assert not cart.contains(products[0])
    assert cart.contains(products[1])
    assert cart.header.cart_count() == 1


@pytest.mark.regression
def test_cart_prices_and_quantities(cart_with_two_items) -> None:
    """Sepetteki fiyat ve adet degerleri referans veriyle uyusmali."""
    cart, products = cart_with_two_items

    for line in cart.lines():
        assert line.quantity == 1, f"{line.name} adedi 1 olmaliydi"
        assert line.price == product_price(line.name), f"{line.name} fiyati hatali"

    expected_subtotal = round(sum(product_price(p) for p in products), 2)
    assert cart.subtotal() == expected_subtotal


@pytest.mark.regression
def test_cart_persists_after_navigation(cart_with_two_items) -> None:
    """Sepet, sayfalar arasi gezinmede korunmali (localStorage davranisi)."""
    cart, products = cart_with_two_items

    inventory = cart.continue_shopping()
    assert inventory.header.cart_count() == 2

    inventory.driver.refresh()
    inventory.wait_document_ready()
    assert inventory.header.cart_count() == 2, "Sayfa yenilendiginde sepet bosaldi"

    back_to_cart = inventory.header.open_cart()
    assert set(back_to_cart.item_names()) == set(products)


@pytest.mark.regression
def test_cart_survives_logout_login(inventory_page: InventoryPage) -> None:
    """SauceDemo'nun bilinen davranisi: sepet cikis sonrasi da korunur.

    Bu bir 'characterization test'tir - dogru mu tartisilir ama MEVCUT
    davranisi kayit altina alir. Davranis degisirse test kirmizi yanar ve
    ekip bunun bilincli bir degisiklik olup olmadigini sorgular.
    """
    from utils.data_loader import user

    inventory_page.add_to_cart("Sauce Labs Backpack")
    login = inventory_page.header.logout()

    standard = user("standard")
    again = login.login_expecting_success(standard.username, standard.password)

    assert again.header.cart_count() == 1, (
        "Sepet cikis/giris sonrasi korunmadi - uygulama davranisi degismis olabilir"
    )


@pytest.mark.regression
def test_reset_app_state_clears_cart(inventory_page: InventoryPage) -> None:
    inventory_page.add_many_to_cart(["Sauce Labs Backpack", "Sauce Labs Bike Light"])
    assert inventory_page.header.cart_count() == 2

    inventory_page.header.reset_app_state()

    assert inventory_page.header.cart_count() == 0, "Reset App State sepeti temizlemedi"


@pytest.mark.negative
def test_checkout_with_empty_cart_is_allowed_but_totals_zero(inventory_page: InventoryPage):
    """Bos sepetle checkout - uygulamanin gercek davranisini belgeler.

    SauceDemo bos sepetle devam etmeye IZIN VERIR. Gercek bir projede bu bir
    hata kaydi olurdu; burada davranisi acikca kayit altina aliyoruz.
    """
    cart = inventory_page.header.open_cart()
    assert cart.is_empty()

    info = cart.proceed_to_checkout()
    overview = info.submit("Ali", "Kiratli", "34710")

    totals = overview.totals()
    assert totals.subtotal == 0.0, "Bos sepette ara toplam 0 olmaliydi"
    assert totals.total == round(totals.subtotal + totals.tax, 2)
