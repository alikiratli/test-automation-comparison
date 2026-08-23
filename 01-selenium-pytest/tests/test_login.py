"""Kimlik dogrulama testleri.

Veri odakli (data-driven) yaklasim: senaryolar ../shared/users.json dosyasindan
gelir. Yeni bir kullanici eklendiginde TEST KODU DEGISMEZ, yalnizca veri
degisir. Ayni veri dosyasini Robot ve Playwright projeleri de okur.
"""
from __future__ import annotations

import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.data_loader import invalid_users, load_users, user, valid_users

pytestmark = [pytest.mark.login]


@pytest.mark.smoke
def test_login_page_elements_are_present(login_page: LoginPage) -> None:
    """Giris ekraninin temel bilesenleri gorunur olmali."""
    assert login_page.is_visible(login_page.LOGIN_LOGO), "Logo gorunmuyor"
    assert login_page.is_visible(login_page.USERNAME_INPUT), "Kullanici adi alani yok"
    assert login_page.is_visible(login_page.PASSWORD_INPUT), "Sifre alani yok"
    assert login_page.is_visible(login_page.LOGIN_BUTTON), "Giris butonu yok"
    assert login_page.get_attribute(login_page.PASSWORD_INPUT, "type") == "password", (
        "Sifre alani maskelenmemis - guvenlik acigi"
    )


@pytest.mark.smoke
def test_standard_user_can_login(login_page: LoginPage) -> None:
    """Referans kullanici giris yapabilmeli ve envantere yonlenmeli."""
    standard = user("standard")
    inventory = login_page.login(standard.username, standard.password)

    assert isinstance(inventory, InventoryPage), "Envanter sayfasina gecilemedi"
    assert "inventory.html" in inventory.current_url
    assert inventory.page_title() == "Products"
    assert inventory.product_count() == 6, "Giristen sonra 6 urun listelenmeli"


@pytest.mark.regression
@pytest.mark.parametrize("credential", valid_users(), ids=str)
def test_all_valid_users_can_login(login_page: LoginPage, credential) -> None:
    """Giris yapabilmesi beklenen TUM kullanicilar icin ayni dogrulama.

    performance_glitch_user kasitli olarak yavastir; explicit wait'lerin
    yeterli olup olmadigini bu test kanitlar.
    """
    if credential.id == "performance_glitch":
        # Yavas kullanici icin bekleme suresini gecici olarak uzat.
        login_page.timeout = login_page.settings.timeouts.slow_user_wait

    page = login_page.login(credential.username, credential.password)

    assert isinstance(page, InventoryPage), (
        f"'{credential.username}' giris yapamadi ({credential.description})"
    )
    assert "inventory.html" in page.current_url


@pytest.mark.negative
@pytest.mark.parametrize("credential", invalid_users(), ids=str)
def test_invalid_logins_show_expected_error(login_page: LoginPage, credential) -> None:
    """Her hatali senaryo KENDI ozel hata mesajini gostermeli.

    'Sadece hata cikti mi' demek yetmez; yanlis mesaj da bir hatadir.
    """
    page = login_page.login(credential.username, credential.password)

    assert isinstance(page, LoginPage), (
        f"'{credential.username}' giris yapmamaliydi ({credential.description})"
    )
    assert page.has_error(), "Hata mesaji gorunmedi"
    assert page.get_error_message() == credential.expected_error, (
        f"Hata mesaji beklenenden farkli. Senaryo: {credential.description}"
    )


@pytest.mark.negative
def test_locked_out_user_message(login_page: LoginPage) -> None:
    """Kilitli kullanici icin ozel is kurali dogrulamasi."""
    locked = user("locked_out")
    page = login_page.login(locked.username, locked.password)

    assert "locked out" in page.get_error_message().lower()
    assert "inventory.html" not in page.current_url, "Kilitli kullanici iceri girdi!"


@pytest.mark.negative
def test_error_message_can_be_dismissed(login_page: LoginPage) -> None:
    """Hata mesaji (X) ile kapatilabilmeli."""
    login_page.login("ghost_user", "wrong")
    assert login_page.has_error()

    login_page.dismiss_error()
    assert not login_page.is_visible(login_page.ERROR_MESSAGE, timeout=3), (
        "Hata mesaji kapatilamadi"
    )


@pytest.mark.negative
def test_empty_form_marks_fields_invalid(login_page: LoginPage) -> None:
    """Bos formda gonderim, alanlari gorsel olarak isaretlemeli."""
    login_page.submit()

    assert login_page.has_error()
    assert login_page.is_field_marked_invalid(login_page.USERNAME_INPUT), (
        "Kullanici adi alani hatali olarak isaretlenmedi"
    )
    assert login_page.is_field_marked_invalid(login_page.PASSWORD_INPUT), (
        "Sifre alani hatali olarak isaretlenmedi"
    )


@pytest.mark.regression
def test_direct_url_access_without_session_is_blocked(login_page: LoginPage) -> None:
    """Guvenlik: oturum acmadan envantere dogrudan gidilememeli.

    Bu, otomasyonun UI'dan cok is kurali test ettigi tipik bir ornektir.
    """
    login_page.open(login_page.settings.inventory_url)

    assert "inventory.html" not in login_page.current_url or login_page.has_error(), (
        "Oturumsuz kullanici envanter sayfasini gorebiliyor - yetkilendirme acigi"
    )


@pytest.mark.regression
def test_logout_clears_session(inventory_page: InventoryPage) -> None:
    """Cikis sonrasi geri tusu ile oturuma donulememeli."""
    login = inventory_page.header.logout()
    assert login.is_visible(login.LOGIN_BUTTON)

    login.driver.back()
    login.wait_document_ready()

    assert "inventory.html" not in login.current_url or login.has_error(), (
        "Cikis sonrasi geri tusu ile korumali sayfaya donulebiliyor"
    )


@pytest.mark.regression
def test_shared_data_file_is_consistent() -> None:
    """Ortak veri dosyasinin butunlugu (uc proje de ayni dosyaya bagimli)."""
    users = load_users()
    assert len(users) >= 6, "Ortak veri dosyasinda beklenenden az senaryo var"
    assert all(u.expected_error for u in users if not u.should_login), (
        "Basarisiz olmasi beklenen her senaryonun expected_error alani dolu olmali"
    )
