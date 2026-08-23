"""Urun listesi ve siralama testleri - Playwright surumu."""
from __future__ import annotations

import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage, SortOption
from utils.data_loader import load_products, product_names
from utils.parsers import is_sorted_ascending, is_sorted_descending

pytestmark = [pytest.mark.inventory]


@pytest.mark.smoke
def test_all_products_are_listed(inventory_page: InventoryPage) -> None:
    expected = load_products()["expected_product_count"]
    expect(inventory_page.items).to_have_count(expected)
    assert set(inventory_page.get_product_names()) == set(product_names())


@pytest.mark.regression
def test_product_prices_match_reference_data(inventory_page: InventoryPage) -> None:
    """Fiyatlari referans veriyle karsilastirir.

    KARSILASTIRMA NOTU - SOFT ASSERT:
        Selenium projesinde bunun icin ozel bir `SoftAssert` sinifi yazilmisti.
        Playwright Python'da (TypeScript'teki `expect.soft` henuz yok) benzer
        bir davranisi hatalari toplayarak elde ediyoruz. Bu, Python surumunun
        TypeScript surumune gore geride kaldigi noktalardan biridir.
    """
    reference = {p["name"]: p["price"] for p in load_products()["products"]}
    failures = []

    for product in inventory_page.get_products():
        if product.price != reference[product.name]:
            failures.append(
                f"{product.name}: beklenen {reference[product.name]}, gercek {product.price}"
            )

    assert not failures, "Hatali fiyatlar:\n  - " + "\n  - ".join(failures)


@pytest.mark.regression
def test_every_product_card_is_complete(inventory_page: InventoryPage) -> None:
    failures = []
    for product in inventory_page.get_products():
        if not product.name:
            failures.append("Isimsiz urun bulundu")
        if len(product.description) <= 10:
            failures.append(f"{product.name}: aciklama cok kisa")
        if product.price <= 0:
            failures.append(f"{product.name}: fiyat pozitif degil")

    assert not failures, "Eksik urun kartlari:\n  - " + "\n  - ".join(failures)


@pytest.mark.smoke
@pytest.mark.parametrize(
    "sort_option,expected_label",
    [
        (SortOption.NAME_A_TO_Z, "Name (A to Z)"),
        (SortOption.NAME_Z_TO_A, "Name (Z to A)"),
        (SortOption.PRICE_LOW_TO_HIGH, "Price (low to high)"),
        (SortOption.PRICE_HIGH_TO_LOW, "Price (high to low)"),
    ],
)
def test_sort_dropdown_updates_label(
    inventory_page: InventoryPage, sort_option: str, expected_label: str
) -> None:
    inventory_page.sort_by(sort_option)
    expect(inventory_page.active_sort_label).to_have_text(expected_label)


@pytest.mark.regression
def test_sort_by_name_ascending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.NAME_A_TO_Z)
    names = inventory_page.get_product_names()
    assert names == sorted(names), f"A-Z sirali degil: {names}"


@pytest.mark.regression
def test_sort_by_name_descending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.NAME_Z_TO_A)
    names = inventory_page.get_product_names()
    assert names == sorted(names, reverse=True), f"Z-A sirali degil: {names}"


@pytest.mark.regression
def test_sort_by_price_ascending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.PRICE_LOW_TO_HIGH)
    prices = inventory_page.get_product_prices()
    assert is_sorted_ascending(prices), f"Artan sirali degil: {prices}"


@pytest.mark.regression
def test_sort_by_price_descending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.PRICE_HIGH_TO_LOW)
    prices = inventory_page.get_product_prices()
    assert is_sorted_descending(prices), f"Azalan sirali degil: {prices}"


@pytest.mark.regression
def test_sorting_does_not_change_product_set(inventory_page: InventoryPage) -> None:
    original = set(inventory_page.get_product_names())

    for option in (
        SortOption.NAME_Z_TO_A,
        SortOption.PRICE_LOW_TO_HIGH,
        SortOption.PRICE_HIGH_TO_LOW,
        SortOption.NAME_A_TO_Z,
    ):
        inventory_page.sort_by(option)
        assert set(inventory_page.get_product_names()) == original


@pytest.mark.regression
def test_product_detail_matches_list_data(inventory_page: InventoryPage) -> None:
    first = inventory_page.get_products()[0]

    detail = inventory_page.open_product_detail(first.name)
    expect(detail.name_label).to_have_text(first.name)
    assert detail.price() == first.price
    assert detail.description() == first.description

    back = detail.back_to_products()
    expect(back.items).to_have_count(6)


@pytest.mark.regression
def test_add_to_cart_from_detail_page(inventory_page: InventoryPage) -> None:
    detail = inventory_page.open_product_detail("Sauce Labs Onesie")
    detail.add_to_cart()

    back = detail.back_to_products()
    back.expect_in_cart("Sauce Labs Onesie")
    back.header.expect_cart_count(1)
