*** Settings ***
Documentation       Urun listesi (envanter) sayfasi keyword'leri.

Resource            ../common.resource


*** Variables ***
${INVENTORY_LIST}           css:[data-test='inventory-list']
${INVENTORY_ITEM}           css:.inventory_item
${ITEM_NAME}                css:[data-test='inventory-item-name']
${ITEM_DESC}                css:[data-test='inventory-item-desc']
${ITEM_PRICE}               css:[data-test='inventory-item-price']
${ITEM_IMAGE}               css:.inventory_item_img img
${SORT_DROPDOWN}            css:[data-test='product-sort-container']
${ACTIVE_SORT_LABEL}        css:.active_option
${PAGE_TITLE}               css:[data-test='title']

# Siralama secenekleri - testlerde deger yerine ISIM kullanilsin diye
${SORT_NAME_ASC}            az
${SORT_NAME_DESC}           za
${SORT_PRICE_ASC}           lohi
${SORT_PRICE_DESC}          hilo


*** Keywords ***
Inventory Page Should Be Open
    Wait Until Location Contains    inventory.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${INVENTORY_LIST}    ${DEFAULT_TIMEOUT}
    Element Text Should Be    ${PAGE_TITLE}    Products

Get Product Count
    ${elements} =    Get WebElements    ${INVENTORY_ITEM}
    ${count} =    Get Length    ${elements}
    RETURN    ${count}

Get Product Names
    ${names} =    Get Texts From Elements    ${ITEM_NAME}
    RETURN    ${names}

Get Product Prices
    [Documentation]    Fiyat metinlerini SAYIYA cevrilmis olarak doner.
    ...    Metin -> sayi donusumu Python kutuphanesinde yapilir; Robot'un
    ...    kendi sozdiziminde bu islem okunaksiz olurdu.
    ${texts} =    Get Texts From Elements    ${ITEM_PRICE}
    ${prices} =    Parse Prices    ${texts}
    RETURN    ${prices}

Get Product Descriptions
    ${descriptions} =    Get Texts From Elements    ${ITEM_DESC}
    RETURN    ${descriptions}

Get Active Sort Label
    ${label} =    Get Text    ${ACTIVE_SORT_LABEL}
    RETURN    ${label}

Sort Products By
    [Documentation]    Siralamayi degistirir ve LISTENIN YENIDEN CIZILMESINI bekler.
    ...    Etiketin guncellenmesini beklemeden fiyat okumak, eski siralamayi
    ...    okuma riski tasir - klasik bir flaky test kaynagi.
    [Arguments]    ${sort_value}    ${expected_label}
    Select From List By Value    ${SORT_DROPDOWN}    ${sort_value}
    Wait Until Element Contains    ${ACTIVE_SORT_LABEL}    ${expected_label}
    ...    timeout=${DEFAULT_TIMEOUT}

Add Product To Cart
    [Documentation]    Urunu sepete ekler ve iki kaniti birden dogrular:
    ...    (1) butonun 'Remove'a donmesi, (2) rozet sayisinin artmasi.
    [Arguments]    ${product_name}
    ${before} =    Get Cart Badge Count
    ${add_locator} =    Add To Cart Locator    ${product_name}
    ${remove_locator} =    Remove From Cart Locator    ${product_name}

    # Etki-dogrulamali tiklama: Chrome 151 + headless ortaminda React
    # butonlarina yapilan gercek tiklamalar zaman zaman sessizce yutuluyor.
    # Butonun 'Remove' haline donmesi, islemin gerceklestiginin kanitidir.
    Click And Wait For Element    ${add_locator}    ${remove_locator}

    ${expected} =    Evaluate    ${before} + 1
    Cart Badge Should Show    ${expected}
    Log    Sepete eklendi: ${product_name} (rozet: ${expected})

Remove Product From Inventory
    [Arguments]    ${product_name}
    ${before} =    Get Cart Badge Count
    ${remove_locator} =    Remove From Cart Locator    ${product_name}
    ${add_locator} =    Add To Cart Locator    ${product_name}

    Click And Wait For Element    ${remove_locator}    ${add_locator}

    ${expected} =    Evaluate    max(${before} - 1, 0)
    Cart Badge Should Show    ${expected}

Add Products To Cart
    [Documentation]    Birden fazla urunu sirayla ekler.
    ...    FOR dongusu, Robot'un veri isleme yetenegini gosterir.
    [Arguments]    @{product_names}
    FOR    ${name}    IN    @{product_names}
        Add Product To Cart    ${name}
    END

Product Should Be In Cart
    [Arguments]    ${product_name}
    ${remove_locator} =    Remove From Cart Locator    ${product_name}
    Element Should Be Visible    ${remove_locator}
    ...    message=Urun sepette gorunmuyor: ${product_name}

Product Should Not Be In Cart
    [Arguments]    ${product_name}
    ${add_locator} =    Add To Cart Locator    ${product_name}
    Element Should Be Visible    ${add_locator}
    ...    message=Urun hala sepette: ${product_name}

Open Product Detail
    [Arguments]    ${product_name}
    Click And Wait For Location    xpath://div[text()='${product_name}']    inventory-item.html
    ...    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${ITEM_NAME}    ${DEFAULT_TIMEOUT}

Go Back To Products
    Click And Wait For Location    css:[data-test='back-to-products']    inventory.html
    ...    ${DEFAULT_TIMEOUT}
    Inventory Page Should Be Open

Get Distinct Image Source Count
    [Documentation]    Farkli gorsel adresi sayisini doner.
    ...    problem_user'da tum gorseller ayni oldugu icin bu deger 1'e duser.
    ${images} =    Get WebElements    ${ITEM_IMAGE}
    ${sources} =    Create List
    FOR    ${image}    IN    @{images}
        ${src} =    Get Element Attribute    ${image}    src
        Append To List    ${sources}    ${src}
    END
    ${unique} =    Remove Duplicates    ${sources}
    ${count} =    Get Length    ${unique}
    RETURN    ${count}

Product Set Should Match Reference Data
    [Documentation]    Ekrandaki urun kumesi ../shared/products.json ile ayni mi?
    ${names} =    Get Product Names
    Verify Sets Are Equal    ${names}    ${PRODUCT_NAMES}    label=Urun listesi

All Product Prices Should Match Reference Data
    [Documentation]    Her urunun fiyatini referans tabloyla karsilastirir.
    ...    `Run Keyword And Continue On Failure` = soft assertion:
    ...    ilk hatada durmaz, TUM hatali fiyatlari tek kosumda raporlar.
    ${names} =    Get Product Names
    ${prices} =    Get Product Prices
    FOR    ${index}    ${name}    IN ENUMERATE    @{names}
        ${actual} =    Get From List    ${prices}    ${index}
        ${expected} =    Get From Dictionary    ${PRODUCTS}    ${name}
        Run Keyword And Continue On Failure
        ...    Should Be Equal As Numbers    ${actual}    ${expected}
        ...    msg=${name} fiyati hatali
    END
