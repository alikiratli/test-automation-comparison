*** Settings ***
Documentation       Urun listesi ve siralama testleri.

Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource
Resource            ../resources/pages/inventory_page.resource

Test Setup          Envanter Sayfasinda Basla
Test Teardown       End Web Test

Force Tags          inventory


*** Test Cases ***
Tum urunler listelenmeli
    [Documentation]    Urun sayisi ve isimleri referans veriyle ayni olmali.
    [Tags]    smoke
    ${count} =    Get Product Count
    Should Be Equal As Integers    ${count}    ${EXPECTED_PRODUCT_COUNT}
    Product Set Should Match Reference Data

Urun fiyatlari referans veriyle eslesmeli
    [Documentation]    Soft assertion: ILK hatada durmaz, tum hatali fiyatlari
    ...    tek kosumda raporlar (`Run Keyword And Continue On Failure`).
    [Tags]    regression
    All Product Prices Should Match Reference Data

Her urun kartinda isim aciklama ve fiyat bulunmali
    [Tags]    regression
    ${names} =    Get Product Names
    ${descriptions} =    Get Product Descriptions
    ${prices} =    Get Product Prices

    FOR    ${index}    ${name}    IN ENUMERATE    @{names}
        ${description} =    Get From List    ${descriptions}    ${index}
        ${price} =    Get From List    ${prices}    ${index}
        Run Keyword And Continue On Failure    Should Not Be Empty    ${name}
        Run Keyword And Continue On Failure    Should Be True    len('''${description}''') > 10
        ...    msg=Aciklama cok kisa: ${name}
        Run Keyword And Continue On Failure    Should Be True    ${price} > 0
        ...    msg=Fiyat pozitif degil: ${name}
    END

Siralama secenegi aktif etiketi guncellemeli
    [Documentation]    [Template] ile 4 siralama secenegi tek testte.
    [Tags]    smoke
    [Template]    Siralama Etiketi Dogrulanmali

    ${SORT_NAME_ASC}      Name (A to Z)
    ${SORT_NAME_DESC}     Name (Z to A)
    ${SORT_PRICE_ASC}     Price (low to high)
    ${SORT_PRICE_DESC}    Price (high to low)

Isme gore artan siralama dogru olmali
    [Tags]    regression
    Sort Products By    ${SORT_NAME_ASC}    Name (A to Z)
    ${names} =    Get Product Names
    Verify List Is Sorted Ascending    ${names}    label=Urun isimleri

Isme gore azalan siralama dogru olmali
    [Tags]    regression
    Sort Products By    ${SORT_NAME_DESC}    Name (Z to A)
    ${names} =    Get Product Names
    Verify List Is Sorted Descending    ${names}    label=Urun isimleri

Fiyata gore artan siralama dogru olmali
    [Tags]    regression
    Sort Products By    ${SORT_PRICE_ASC}    Price (low to high)
    ${prices} =    Get Product Prices
    Verify List Is Sorted Ascending    ${prices}    label=Urun fiyatlari

Fiyata gore azalan siralama dogru olmali
    [Tags]    regression
    Sort Products By    ${SORT_PRICE_DESC}    Price (high to low)
    ${prices} =    Get Product Prices
    Verify List Is Sorted Descending    ${prices}    label=Urun fiyatlari

Siralama urun kumesini degistirmemeli
    [Documentation]    Regresyon: siralama sonrasi listeden urun DUSMEMELI.
    [Tags]    regression
    ${original} =    Get Product Names

    Sort Products By    ${SORT_NAME_DESC}    Name (Z to A)
    ${after_name_desc} =    Get Product Names
    Verify Sets Are Equal    ${after_name_desc}    ${original}    label=Z-A sonrasi

    Sort Products By    ${SORT_PRICE_ASC}    Price (low to high)
    ${after_price_asc} =    Get Product Names
    Verify Sets Are Equal    ${after_price_asc}    ${original}    label=Fiyat artan sonrasi

    Sort Products By    ${SORT_PRICE_DESC}    Price (high to low)
    ${after_price_desc} =    Get Product Names
    Verify Sets Are Equal    ${after_price_desc}    ${original}    label=Fiyat azalan sonrasi

Urun detay sayfasi liste verisiyle tutarli olmali
    [Tags]    regression
    ${names} =    Get Product Names
    ${prices} =    Get Product Prices
    ${first_name} =    Get From List    ${names}    0
    ${first_price} =    Get From List    ${prices}    0

    Open Product Detail    ${first_name}
    Element Text Should Be    ${ITEM_NAME}    ${first_name}
    ${detail_price_text} =    Get Text    ${ITEM_PRICE}
    ${detail_price} =    Parse Price    ${detail_price_text}
    Should Be Equal As Numbers    ${detail_price}    ${first_price}

    Go Back To Products
    ${count} =    Get Product Count
    Should Be Equal As Integers    ${count}    ${EXPECTED_PRODUCT_COUNT}


*** Keywords ***
Envanter Sayfasinda Basla
    [Documentation]    Ortak on kosul: giris yapilmis envanter sayfasi.
    ...    pytest'teki `inventory_page` fixture'inin karsiligi.
    Begin Web Test
    Login As Standard User
    Inventory Page Should Be Open

Siralama Etiketi Dogrulanmali
    [Arguments]    ${sort_value}    ${expected_label}
    Sort Products By    ${sort_value}    ${expected_label}
    ${label} =    Get Active Sort Label
    Should Be Equal    ${label}    ${expected_label}
