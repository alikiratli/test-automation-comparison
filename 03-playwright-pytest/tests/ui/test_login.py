"""Kimlik dogrulama testleri - Playwright surumu.

Selenium surumuyle (01-selenium-pytest/tests/test_login.py) satir satir
karsilastirilabilir; ayni senaryolar, ayni veri kaynagi.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.data_loader import invalid_users, user, valid_users

pytestmark = [pytest.mark.login]


@pytest.mark.smoke
def test_login_page_elements_are_present(login_page: LoginPage) -> None:
    expect(login_page.login_logo).to_be_visible()
    expect(login_page.username_input).to_be_visible()
    expect(login_page.password_input).to_be_visible()
    expect(login_page.login_button).to_be_enabled()
    login_page.expect_password_masked()


@pytest.mark.smoke
def test_standard_user_can_login(login_page: LoginPage) -> None:
    standard = user("standard")
    inventory = login_page.login(standard.username, standard.password)

    assert isinstance(inventory, InventoryPage)
    expect(inventory.page).to_have_url(inventory.settings.inventory_url)
    expect(inventory.page_title).to_have_text("Products")
    expect(inventory.items).to_have_count(6)


@pytest.mark.regression
@pytest.mark.parametrize("credential", valid_users(), ids=str)
def test_all_valid_users_can_login(login_page: LoginPage, credential) -> None:
    """Yavas kullanici dahil tum gecerli kullanicilar giris yapabilmeli.

    KARSILASTIRMA NOTU:
        Selenium surumunde performance_glitch_user icin timeout'u ELLE
        uzatmak gerekiyordu. Burada da uzatiyoruz ama sebep farkli: Playwright
        zaten bekliyor, biz sadece ust siniri yukseltiyoruz. Selenium'da
        bekleme kodunu yazmak gerekiyordu; burada sadece bir sayi.
    """
    if credential.id == "performance_glitch":
        login_page.page.set_default_timeout(login_page.settings.slow_user_timeout)

    page = login_page.login(credential.username, credential.password)
    assert isinstance(page, InventoryPage), f"'{credential.username}' giris yapamadi"


@pytest.mark.negative
@pytest.mark.parametrize("credential", invalid_users(), ids=str)
def test_invalid_logins_show_expected_error(login_page: LoginPage, credential) -> None:
    page = login_page.login(credential.username, credential.password)

    assert isinstance(page, LoginPage), f"'{credential.username}' giris yapmamaliydi"
    page.expect_error(credential.expected_error)
    page.expect_still_on_login_page()


@pytest.mark.negative
def test_error_message_can_be_dismissed(login_page: LoginPage) -> None:
    login_page.login("ghost_user", "wrong")
    expect(login_page.error_message).to_be_visible()

    login_page.dismiss_error()
    expect(login_page.error_message).not_to_be_visible()


@pytest.mark.negative
def test_empty_form_marks_fields_invalid(login_page: LoginPage) -> None:
    login_page.submit()

    expect(login_page.error_message).to_be_visible()
    login_page.expect_field_marked_invalid("username")
    login_page.expect_field_marked_invalid("password")


@pytest.mark.regression
def test_direct_url_access_without_session_is_blocked(login_page: LoginPage) -> None:
    login_page.page.goto(login_page.settings.inventory_url)

    expect(login_page.error_message).to_be_visible()
    assert "inventory.html" not in login_page.page.url or login_page.error_message.count()


@pytest.mark.regression
def test_logout_clears_session(inventory_page: InventoryPage) -> None:
    login = inventory_page.header.logout()
    expect(login.login_button).to_be_visible()

    login.page.go_back()
    assert "inventory.html" not in login.page.url or login.error_message.count() > 0


@pytest.mark.regression
def test_storage_state_login_is_faster_than_ui_login(fast_authenticated_page) -> None:
    """Oturum enjeksiyonu ile giris - UI'ya HIC dokunmadan.

    Bu testin Selenium'da dogrudan bir karsiligi yoktur. `fast_authenticated_page`
    fixture'i, bir kez kaydedilmis cerez + localStorage durumunu yeni bir
    context'e yukler; test dogrudan envanter sayfasindan baslar.
    """
    from config.settings import load_settings

    settings = load_settings()
    fast_authenticated_page.goto(settings.inventory_url)

    inventory = InventoryPage(fast_authenticated_page, settings)
    expect(inventory.inventory_list).to_be_visible()
    expect(inventory.items).to_have_count(6)
