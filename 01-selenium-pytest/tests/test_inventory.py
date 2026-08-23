"""Urun listesi ve siralama testleri."""
from __future__ import annotations

import pytest

from core.soft_assert import SoftAssert
from pages.inventory_page import InventoryPage, SortOption
from utils.data_loader import load_products, product_names
from utils.parsers import is_sorted_ascending, is_sorted_descending

pytestmark = [pytest.mark.inventory]


@pytest.mark.smoke
def test_all_products_are_listed(inventory_page: InventoryPage) -> None:
    """Beklenen sayida ve isimde urun listelenmeli."""
    expected = load_products()["expected_product_count"]
    assert inventory_page.product_count() == expected

    listed = set(inventory_page.product_names())
    assert listed == set(product_names()), (
        f"Urun listesi referanstan farkli. Fazla: {listed - set(product_names())}, "
        f"Eksik: {set(product_names()) - listed}"
    )


@pytest.mark.regression
def test_product_prices_match_reference_data(inventory_page: InventoryPage) -> None:
    """Her urunun fiyati referans veriyle birebir esit olmali.

    SoftAssert kullaniyoruz: ilk hatali fiyatta durmak yerine, hatali TUM
    fiyatlari tek kosumda raporluyoruz.
    """
    reference = {p["name"]: p["price"] for p in load_products()["products"]}

    with SoftAssert("Urun fiyatlari") as soft:
        for product in inventory_page.products():
            soft.equal(product.price, reference[product.name], f"{product.name} fiyati")


@pytest.mark.regression
def test_every_product_has_name_description_and_price(inventory_page: InventoryPage) -> None:
    """Hicbir urun kartinda bos alan olmamali."""
    with SoftAssert("Urun kart butunlugu") as soft:
        for product in inventory_page.products():
            soft.check(bool(product.name), f"Isim dolu: {product}")
            soft.check(len(product.description) > 10, f"Aciklama yeterli uzunlukta: {product}")
            soft.check(product.price > 0, f"Fiyat pozitif: {product}")


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
def test_sort_dropdown_updates_active_label(
    inventory_page: InventoryPage, sort_option: str, expected_label: str
) -> None:
    inventory_page.sort_by(sort_option)
    assert inventory_page.active_sort_label() == expected_label


@pytest.mark.regression
def test_sort_by_name_ascending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.NAME_A_TO_Z)
    names = inventory_page.product_names()
    assert names == sorted(names), f"Isimler A-Z sirali degil: {names}"


@pytest.mark.regression
def test_sort_by_name_descending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.NAME_Z_TO_A)
    names = inventory_page.product_names()
    assert names == sorted(names, reverse=True), f"Isimler Z-A sirali degil: {names}"


@pytest.mark.regression
def test_sort_by_price_ascending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.PRICE_LOW_TO_HIGH)
    prices = inventory_page.product_prices()
    assert is_sorted_ascending(prices), f"Fiyatlar artan sirali degil: {prices}"
    assert prices[0] == min(prices)


@pytest.mark.regression
def test_sort_by_price_descending(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by(SortOption.PRICE_HIGH_TO_LOW)
    prices = inventory_page.product_prices()
    assert is_sorted_descending(prices), f"Fiyatlar azalan sirali degil: {prices}"
    assert prices[0] == max(prices)


@pytest.mark.regression
def test_sorting_does_not_change_product_set(inventory_page: InventoryPage) -> None:
    """Siralama urunleri yeniden dizmeli, EKLEMEMELI veya SILMEMELI.

    Klasik bir regresyon hatasi: siralama sonrasi listeden urun dusmesi.
    """
    original = set(inventory_page.product_names())

    for option in (
        SortOption.NAME_Z_TO_A,
        SortOption.PRICE_LOW_TO_HIGH,
        SortOption.PRICE_HIGH_TO_LOW,
        SortOption.NAME_A_TO_Z,
    ):
        inventory_page.sort_by(option)
        assert set(inventory_page.product_names()) == original, (
            f"'{option}' siralamasindan sonra urun kumesi degisti"
        )


@pytest.mark.regression
def test_product_detail_matches_list_data(inventory_page: InventoryPage) -> None:
    """Listedeki bilgi ile detay sayfasindaki bilgi tutarli olmali."""
    first = inventory_page.products()[0]

    detail = inventory_page.open_product_detail(first.name)
    assert detail.name() == first.name
    assert detail.price() == first.price
    assert detail.description() == first.description

    back = detail.back_to_products()
    assert back.product_count() == 6


@pytest.mark.slow
@pytest.mark.regression
def test_problem_user_has_broken_images(login_page) -> None:
    """problem_user'in bilinen gorsel hatasini DOGRULAR.

    Bu test "hata bulmak" icin degil, bilinen hatanin hala var oldugunu
    izlemek icindir (characterization test). Selenium'da gorsel dogrulamanin
    ancak JavaScript ile yapilabildigini de gosterir - Playwright'ta
    `expect(page).to_have_screenshot()` ile piksel karsilastirmasi hazirdir.
    """
    from utils.data_loader import user

    problem = user("problem")
    inventory = login_page.login_expecting_success(problem.username, problem.password)

    distinct = inventory.distinct_image_sources()
    assert distinct < 6, (
        "problem_user icin tum gorseller ayni olmaliydi (bilinen hata kayboldu mu?)"
    )
