*** Settings ***
Documentation       Kimlik dogrulama testleri.
...
...                 Bu dosya Robot Framework'un iki farkli veri odakli
...                 yaklasimini gosterir:
...                   1) [Template] + inline veri satirlari  -> 07 numarali test
...                   2) DataDriver + CSV dosyasi            -> 01b_login_datadriven.robot
...
...                 Selenium projesindeki karsiligi: tests/test_login.py

Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource
Resource            ../resources/pages/inventory_page.resource

Test Setup          Begin Web Test
Test Teardown       End Web Test

Force Tags          login


*** Test Cases ***
Giris ekraninin temel bilesenleri gorunur olmali
    [Documentation]    Login sayfasinin yapisal butunlugu.
    [Tags]    smoke
    Login Page Should Be Open
    Element Should Be Visible    ${LOGIN_LOGO}
    Password Field Should Be Masked

Standart kullanici giris yapabilmeli
    [Documentation]    Referans kullanici ile mutlu yol.
    [Tags]    smoke
    Login As    ${STANDARD_USER}
    Inventory Page Should Be Open
    ${count} =    Get Product Count
    Should Be Equal As Integers    ${count}    ${EXPECTED_PRODUCT_COUNT}

Problem kullanici giris yapabilmeli
    [Documentation]    problem_user giris YAPABILIR; sorunlari giristen sonradir.
    [Tags]    regression
    Login As    ${PROBLEM_USER}
    Inventory Page Should Be Open

Yavas kullanici giris yapabilmeli
    [Documentation]    performance_glitch_user kasitli olarak yavastir.
    ...
    ...    Bu test, bekleme suresinin TEST BAZINDA uzatilabildigini gosterir.
    ...    `Set Selenium Timeout` sadece bu testi etkiler, digerlerini degil.
    [Tags]    regression    slow
    Set Selenium Timeout    ${SLOW_USER_TIMEOUT}
    Login As    ${GLITCH_USER}
    Inventory Page Should Be Open

Kilitli kullanici giris yapamamali
    [Documentation]    Is kurali: kilitli hesap engellenmeli.
    [Tags]    negative
    Login Should Fail With Error
    ...    ${LOCKED_USER}
    ...    ${PASSWORD}
    ...    Epic sadface: Sorry, this user has been locked out.

Hata mesaji kapatilabilmeli
    [Tags]    negative
    Login With Credentials    ghost_user    wrong_password
    Login Error Should Be Visible
    Dismiss Login Error
    Element Should Not Be Visible    ${ERROR_MESSAGE}

Bos form gonderiminde alanlar hatali isaretlenmeli
    [Tags]    negative
    Submit Login Form
    Login Error Should Be Visible
    Login Field Should Be Marked Invalid    ${LOGIN_USERNAME_INPUT}
    Login Field Should Be Marked Invalid    ${LOGIN_PASSWORD_INPUT}

Gecersiz giris senaryolari
    [Documentation]    [Template] ile VERI ODAKLI TEST.
    ...
    ...    Robot'un en zarif ozelliklerinden biri: asagidaki her satir AYRI
    ...    BIR TEST olarak kosar ve raporda ayri satir olarak gorunur.
    ...    pytest'teki `@pytest.mark.parametrize` karsiligidir, ama tabloyu
    ...    okumak icin Python bilmek gerekmez.
    [Tags]    negative    regression
    [Template]    Login Should Fail With Error

    locked_out_user    secret_sauce      Epic sadface: Sorry, this user has been locked out.
    standard_user      wrong_password    Epic sadface: Username and password do not match any user in this service
    ghost_user         secret_sauce      Epic sadface: Username and password do not match any user in this service
    ${EMPTY}           secret_sauce      Epic sadface: Username is required
    standard_user      ${EMPTY}          Epic sadface: Password is required

Oturumsuz kullanici korumali sayfaya erisememeli
    [Documentation]    Guvenlik: giris yapmadan /inventory.html acilmamali.
    [Tags]    regression    security
    Go To    ${INVENTORY_URL}
    Wait For Page To Be Ready
    Location Should Not Contain    inventory.html
    ...    message=Yetkilendirme acigi: oturumsuz erisim mumkun

Cikis sonrasi geri tusu oturumu geri getirmemeli
    [Tags]    regression    security
    Login As Standard User
    Logout From Application
    Go Back
    Wait For Page To Be Ready
    Location Should Not Contain    inventory.html
    ...    message=Cikis sonrasi geri tusu ile korumali sayfaya donulebiliyor
