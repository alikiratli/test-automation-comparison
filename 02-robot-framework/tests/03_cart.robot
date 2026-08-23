*** Settings ***
Documentation       Sepet islemleri testleri.

Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource
Resource            ../resources/pages/inventory_page.resource
Resource            ../resources/pages/cart_page.resource

Test Setup          Envanter Sayfasinda Basla
Test Teardown       End Web Test

Force Tags          cart


*** Variables ***
@{TWO_PRODUCTS}     Sauce Labs Backpack    Sauce Labs Bike Light


*** Test Cases ***
Yeni oturumda sepet bos olmali
    [Tags]    smoke
    ${count} =    Get Cart Badge Count
    Should Be Equal As Integers    ${count}    0
    Open Cart
    Cart Should Be Empty

Tek urun eklendiginde rozet guncellenmeli
    [Tags]    smoke
    Add Product To Cart    Sauce Labs Backpack
    Cart Badge Should Show    1
    Product Should Be In Cart    Sauce Labs Backpack

Tum urunler sepete eklenebilmeli
    [Documentation]    Her eklemeden sonra rozetin DOGRU SAYIDA artmasi kontrol edilir.
    [Tags]    regression
    FOR    ${index}    ${name}    IN ENUMERATE    @{PRODUCT_NAMES}    start=1
        Add Product To Cart    ${name}
        Cart Badge Should Show    ${index}
    END
    Open Cart
    ${count} =    Get Cart Item Count
    Should Be Equal As Integers    ${count}    ${EXPECTED_PRODUCT_COUNT}
    Cart Should Contain Exactly    @{PRODUCT_NAMES}

Urun envanter sayfasindan cikarilabilmeli
    [Tags]    regression
    Add Products To Cart    Sauce Labs Backpack    Sauce Labs Onesie
    Cart Badge Should Show    2
    Remove Product From Inventory    Sauce Labs Onesie
    Cart Badge Should Show    1
    Product Should Not Be In Cart    Sauce Labs Onesie
    Product Should Be In Cart    Sauce Labs Backpack

Urun sepet sayfasindan cikarilabilmeli
    [Tags]    regression
    Add Products To Cart    @{TWO_PRODUCTS}
    Open Cart
    Remove Item From Cart    Sauce Labs Backpack
    Cart Should Not Contain    Sauce Labs Backpack
    Cart Should Contain    Sauce Labs Bike Light
    Cart Badge Should Show    1

Sepetteki fiyat ve adetler dogru olmali
    [Tags]    regression
    Add Products To Cart    @{TWO_PRODUCTS}
    Open Cart
    All Cart Quantities Should Be One
    Cart Prices Should Match Reference Data

    ${subtotal} =    Get Cart Subtotal
    ${expected} =    Sum Product Prices    ${PRODUCTS}    ${TWO_PRODUCTS}
    Should Be Equal As Numbers    ${subtotal}    ${expected}
    ...    msg=Sepet ara toplami referans veriyle uyusmuyor

Sepet sayfa gecislerinde korunmali
    [Documentation]    localStorage davranisi: gezinme ve yenileme sepeti bozmamali.
    [Tags]    regression
    Add Products To Cart    @{TWO_PRODUCTS}
    Open Cart
    Continue Shopping
    Cart Badge Should Show    2

    Reload Page
    Wait For Page To Be Ready
    Cart Badge Should Show    2

    Open Cart
    Cart Should Contain Exactly    @{TWO_PRODUCTS}

Sepet cikis ve yeniden giris sonrasi korunmali
    [Documentation]    Uygulamanin MEVCUT davranisini kayit altina alir
    ...    (characterization test). Davranis degisirse test kirmizi yanar.
    [Tags]    regression
    Add Product To Cart    Sauce Labs Backpack
    Logout From Application
    Login As Standard User
    Cart Badge Should Show    1

Reset App State sepeti temizlemeli
    [Tags]    regression
    Add Products To Cart    @{TWO_PRODUCTS}
    Cart Badge Should Show    2
    Reset Application State
    ${count} =    Get Cart Badge Count
    Should Be Equal As Integers    ${count}    0

Continue Shopping envantere donmeli
    [Tags]    regression
    Add Product To Cart    Sauce Labs Onesie
    Open Cart
    Continue Shopping
    Inventory Page Should Be Open
    Cart Badge Should Show    1


*** Keywords ***
Envanter Sayfasinda Basla
    Begin Web Test
    Login As Standard User
    Inventory Page Should Be Open
