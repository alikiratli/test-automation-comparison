"""Navigasyon, yan menu ve tarayici gecmisi testleri."""
from __future__ import annotations

import pytest

from pages.inventory_page import InventoryPage

pytestmark = [pytest.mark.regression]


def test_burger_menu_contains_expected_items(inventory_page: InventoryPage) -> None:
    items = inventory_page.header.menu_items()

    expected = ["All Items", "About", "Logout", "Reset App State"]
    assert items == expected, f"Menu ogeleri degismis: {items}"


def test_menu_opens_and_closes(inventory_page: InventoryPage) -> None:
    """Animasyonlu menunun ac/kapa dongusu.

    Animasyonlu bilesenler Selenium'da en kirilgan alandir: `.click()`
    animasyon sirasinda calisirsa 'element not interactable' alirsiniz.
    HeaderComponent bunu aria-hidden bekleyerek cozuyor.
    """
    header = inventory_page.header

    header.open_menu()
    assert header.is_visible(header.LOGOUT_LINK)

    header.close_menu()
    assert not header.is_visible(header.LOGOUT_LINK, timeout=3)


def test_all_items_link_returns_to_inventory(inventory_page: InventoryPage) -> None:
    cart = inventory_page.header.open_cart()
    assert "cart.html" in cart.current_url

    cart.header.open_menu()
    cart.click(cart.header.ALL_ITEMS_LINK)

    inventory = InventoryPage(cart.driver, cart.settings).verify_loaded()
    assert inventory.product_count() == 6


def test_browser_back_from_cart(inventory_page: InventoryPage) -> None:
    inventory_page.add_to_cart("Sauce Labs Backpack")
    cart = inventory_page.header.open_cart()

    cart.driver.back()
    cart.wait_document_ready()

    inventory = InventoryPage(cart.driver, cart.settings).verify_loaded()
    assert inventory.header.cart_count() == 1, "Geri donusta sepet durumu kayboldu"


def test_deep_link_to_cart_with_active_session(inventory_page: InventoryPage) -> None:
    """Oturum acikken dogrudan sepet URL'sine gidilebilmeli."""
    inventory_page.add_to_cart("Sauce Labs Bike Light")

    from pages.cart_page import CartPage

    cart = CartPage(inventory_page.driver, inventory_page.settings).open_cart_page()

    assert cart.item_count() == 1
    assert cart.contains("Sauce Labs Bike Light")


def test_page_titles_are_correct(inventory_page: InventoryPage) -> None:
    """Tarayici sekmesi basligi tum sayfalarda tutarli olmali (SEO/UX)."""
    assert inventory_page.title == "Swag Labs"

    cart = inventory_page.header.open_cart()
    assert cart.title == "Swag Labs"
    assert cart.get_text(cart.header.APP_LOGO) == "Swag Labs"
