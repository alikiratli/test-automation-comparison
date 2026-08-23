*** Settings ***
Documentation       Checkout formu ve tutar hesaplama testleri.

Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource
Resource            ../resources/pages/inventory_page.resource
Resource            ../resources/pages/cart_page.resource
Resource            ../resources/pages/checkout_page.resource

Test Setup          Iki Urunlu Sepetle Basla
Test Teardown       End Web Test

Force Tags          checkout


*** Variables ***
@{TWO_PRODUCTS}     Sauce Labs Backpack    Sauce Labs Bike Light


*** Test Cases ***
Gecerli bilgilerle checkout formu gecilebilmeli
    [Tags]    smoke
    Proceed To Checkout
    Continue To Checkout Overview
    Checkout Overview Page Should Be Open

Zorunlu alan validasyonu
    [Documentation]    Alanlar SIRAYLA dogrulanmali: once ad, sonra soyad,
    ...    sonra posta kodu. Bu, validasyon SIRASININ da test edildigi anlamina
    ...    gelir - hepsi bos oldugunda ilk hata "First Name" olmalidir.
    [Tags]    negative
    [Template]    Hatali Checkout Formu Denemesi

    ${EMPTY}    Kiratli     34710       Error: First Name is required
    Ali         ${EMPTY}    34710       Error: Last Name is required
    Ali         Kiratli     ${EMPTY}    Error: Postal Code is required
    ${EMPTY}    ${EMPTY}    ${EMPTY}    Error: First Name is required

Ozet sayfasindaki tutarlar matematiksel olarak dogru olmali
    [Documentation]    IS KURALI TESTI - otomasyonun asil degeri.
    ...    KDV = ara toplam x 0.08 ve genel toplam = ara toplam + KDV olmali.
    [Tags]    smoke
    ${expected_subtotal} =    Sum Product Prices    ${PRODUCTS}    ${TWO_PRODUCTS}
    Proceed To Checkout
    Continue To Checkout Overview
    Checkout Totals Should Be Correct    expected_subtotal=${expected_subtotal}

Ozet sayfasi tam olarak sepetteki urunleri listelemeli
    [Tags]    regression
    Proceed To Checkout
    Continue To Checkout Overview
    Checkout Overview Should Contain Exactly    @{TWO_PRODUCTS}

Odeme ve kargo bilgileri gorunmeli
    [Tags]    regression
    Proceed To Checkout
    Continue To Checkout Overview
    Payment And Shipping Info Should Be Present

Bilgi adimindan iptal sepete donmeli
    [Tags]    regression
    Proceed To Checkout
    Cancel Checkout Information
    Cart Page Should Be Open
    Cart Should Contain Exactly    @{TWO_PRODUCTS}

Ozet adimindan iptal envantere donmeli
    [Tags]    regression
    Proceed To Checkout
    Continue To Checkout Overview
    Cancel Checkout Overview
    Inventory Page Should Be Open
    Cart Badge Should Show    2

Farkli sepet buyukluklerinde KDV dogru hesaplanmali
    [Documentation]    Ayni is kurali, 3 farkli veri kumesiyle.
    ...    Her senaryo sonrasi uygulama durumu sifirlanir.
    [Tags]    regression
    [Setup]    Envanter Sayfasinda Basla
    [Template]    Sepet Senaryosunda Tutarlar Dogrulanmali

    Sauce Labs Onesie
    Sauce Labs Backpack        Sauce Labs Fleece Jacket
    Sauce Labs Bike Light      Sauce Labs Bolt T-Shirt     Sauce Labs Onesie


*** Keywords ***
Envanter Sayfasinda Basla
    Begin Web Test
    Login As Standard User
    Inventory Page Should Be Open

Iki Urunlu Sepetle Basla
    [Documentation]    Checkout testlerinin ortak on kosulu.
    ...    pytest'teki `cart_with_two_items` fixture'inin karsiligi.
    Envanter Sayfasinda Basla
    Add Products To Cart    @{TWO_PRODUCTS}
    Open Cart
    Cart Should Contain Exactly    @{TWO_PRODUCTS}

Hatali Checkout Formu Denemesi
    [Arguments]    ${first}    ${last}    ${postal}    ${expected_error}
    Proceed To Checkout
    Checkout Information Should Fail With Error    ${first}    ${last}    ${postal}
    ...    ${expected_error}
    # Bir sonraki sablon satiri icin sepete geri don
    Cancel Checkout Information

Sepet Senaryosunda Tutarlar Dogrulanmali
    [Documentation]    Vararg adi `@{product_names}`; `@{products}` yazilsaydi
    ...    global `${PRODUCTS}` fiyat sozlugunu golgelerdi (bkz. checkout_page).
    [Arguments]    @{product_names}
    Add Products To Cart    @{product_names}
    ${expected_subtotal} =    Sum Product Prices    ${PRODUCTS}    ${product_names}
    Open Cart
    Proceed To Checkout
    Continue To Checkout Overview
    Checkout Totals Should Be Correct    expected_subtotal=${expected_subtotal}
    Cancel Checkout Overview
    Reset Application State
