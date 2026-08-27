*** Settings ***
Documentation       Checkout akisinin 3 adimi tek resource dosyasinda.
...
...                 Selenium projesinde bu 3 adim 3 AYRI SINIFTIR
...                 (CheckoutInformationPage / OverviewPage / CompletePage).
...                 Robot'ta sinif olmadigi icin ayrim, keyword ISIMLERININ
...                 on ekiyle saglanir: "Checkout Information ...",
...                 "Checkout Overview ...", "Checkout Complete ...".

Resource            ../common.resource


*** Variables ***
# --- Adim 1: musteri bilgileri ---
${FIRST_NAME_INPUT}         css:[data-test='firstName']
${LAST_NAME_INPUT}          css:[data-test='lastName']
${POSTAL_CODE_INPUT}        css:[data-test='postalCode']
${CONTINUE_BUTTON}          css:[data-test='continue']
${CANCEL_BUTTON}            css:[data-test='cancel']

# --- Adim 2: ozet ---
${SUBTOTAL_LABEL}           css:[data-test='subtotal-label']
${TAX_LABEL}                css:[data-test='tax-label']
${TOTAL_LABEL}              css:[data-test='total-label']
${PAYMENT_INFO}             css:[data-test='payment-info-value']
${SHIPPING_INFO}            css:[data-test='shipping-info-value']
${FINISH_BUTTON}            css:[data-test='finish']
${OVERVIEW_ITEM_NAME}       css:[data-test='inventory-item-name']

# --- Adim 3: tamamlandi ---
${COMPLETE_HEADER}          css:[data-test='complete-header']
${COMPLETE_TEXT}            css:[data-test='complete-text']
${PONY_IMAGE}               css:[data-test='pony-express']
${BACK_HOME_BUTTON}         css:[data-test='back-to-products']


*** Keywords ***
# =========================================================================== #
# ADIM 1 - Musteri bilgileri
# =========================================================================== #
Checkout Information Page Should Be Open
    Wait Until Location Contains    checkout-step-one.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${FIRST_NAME_INPUT}    ${DEFAULT_TIMEOUT}

Fill Checkout Information
    [Documentation]    Formu doldurur. Bos deger verilen alan yalnizca temizlenir.
    [Arguments]    ${first_name}    ${last_name}    ${postal_code}

    IF    '${first_name}' != '${EMPTY}'
        Type Text With Verify    ${FIRST_NAME_INPUT}    ${first_name}
    ELSE
        Clear Input Field    ${FIRST_NAME_INPUT}
    END
    IF    '${last_name}' != '${EMPTY}'
        Type Text With Verify    ${LAST_NAME_INPUT}    ${last_name}
    ELSE
        Clear Input Field    ${LAST_NAME_INPUT}
    END
    IF    '${postal_code}' != '${EMPTY}'
        Type Text With Verify    ${POSTAL_CODE_INPUT}    ${postal_code}
    ELSE
        Clear Input Field    ${POSTAL_CODE_INPUT}
    END

Submit Checkout Information
    [Documentation]    'Continue' tiklamasi iki sonuctan birini uretmeli:
    ...    ya 2. adima gecilir ya da hata mesaji gorunur. Tiklama etkisiz
    ...    kalirsa tekrar denenir.
    Click Element Until    ${CONTINUE_BUTTON}
    ...    Wait Until Keyword Succeeds    3s    250ms    Checkout Form Result Should Appear

Checkout Form Result Should Appear
    ${url} =    Get Location
    ${moved} =    Run Keyword And Return Status
    ...    Should Contain    ${url}    checkout-step-two.html
    IF    not ${moved}
        Element Should Be Visible    ${ERROR_MESSAGE}
    END

Continue To Checkout Overview
    [Documentation]    Formu doldurup 2. adima gecer ve gecisi dogrular.
    [Arguments]    ${first_name}=${CUSTOMER}[first_name]
    ...    ${last_name}=${CUSTOMER}[last_name]
    ...    ${postal_code}=${CUSTOMER}[postal_code]
    Fill Checkout Information    ${first_name}    ${last_name}    ${postal_code}
    Submit Checkout Information
    Checkout Overview Page Should Be Open

Checkout Information Should Fail With Error
    [Arguments]    ${first_name}    ${last_name}    ${postal_code}    ${expected_error}
    Fill Checkout Information    ${first_name}    ${last_name}    ${postal_code}
    Submit Checkout Information
    Error Message Should Be    ${expected_error}
    Location Should Not Contain    checkout-step-two.html

Cancel Checkout Information
    Click And Wait For Location    ${CANCEL_BUTTON}    cart.html

# =========================================================================== #
# ADIM 2 - Siparis ozeti
# =========================================================================== #
Checkout Overview Page Should Be Open
    Wait Until Location Contains    checkout-step-two.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${FINISH_BUTTON}    ${DEFAULT_TIMEOUT}

Get Checkout Totals
    [Documentation]    Ara toplam / KDV / genel toplam METINLERINI doner.
    ...    Sayiya cevirme ve dogrulama isi Python kutuphanesindedir.
    ${subtotal} =    Get Text    ${SUBTOTAL_LABEL}
    ${tax} =    Get Text    ${TAX_LABEL}
    ${total} =    Get Text    ${TOTAL_LABEL}
    ${totals} =    Create Dictionary    subtotal=${subtotal}    tax=${tax}    total=${total}
    RETURN    ${totals}

Checkout Totals Should Be Correct
    [Documentation]    IS KURALI DOGRULAMASI: KDV ve genel toplam matematigi.
    ...    Otomasyonun asil degeri burasidir - "buton calisti mi" degil,
    ...    "hesap dogru mu".
    [Arguments]    ${expected_subtotal}=${None}
    ${totals} =    Get Checkout Totals
    ${result} =    Verify Checkout Totals
    ...    ${totals}[subtotal]    ${totals}[tax]    ${totals}[total]
    ...    expected_subtotal=${expected_subtotal}    tax_rate=${TAX_RATE}
    Log Test Data Table    Checkout Tutarlari    ${result}
    RETURN    ${result}

Get Checkout Overview Item Names
    ${names} =    Get Texts From Elements    ${OVERVIEW_ITEM_NAME}
    RETURN    ${names}

Checkout Overview Should Contain Exactly
    [Arguments]    @{expected_products}
    ${names} =    Get Checkout Overview Item Names
    Verify Sets Are Equal    ${names}    ${expected_products}    label=Siparis ozeti

Payment And Shipping Info Should Be Present
    ${payment} =    Get Text    ${PAYMENT_INFO}
    ${shipping} =    Get Text    ${SHIPPING_INFO}
    Should Not Be Empty    ${payment}    msg=Odeme bilgisi bos
    Should Not Be Empty    ${shipping}    msg=Kargo bilgisi bos

Finish Order
    Click And Wait For Location    ${FINISH_BUTTON}    checkout-complete.html
    Checkout Complete Page Should Be Open

Cancel Checkout Overview
    Click And Wait For Location    ${CANCEL_BUTTON}    inventory.html

# =========================================================================== #
# ADIM 3 - Siparis tamamlandi
# =========================================================================== #
Checkout Complete Page Should Be Open
    Wait Until Location Contains    checkout-complete.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${COMPLETE_HEADER}    ${DEFAULT_TIMEOUT}

Order Confirmation Should Be Displayed
    ${header} =    Get Text    ${COMPLETE_HEADER}
    Should Contain    ${header}    Thank you    ignore_case=${True}
    ...    msg=Onay basligi beklenen metni icermiyor
    ${text} =    Get Text    ${COMPLETE_TEXT}
    Should Contain    ${text}    dispatched    ignore_case=${True}
    # BEKLEYEREK dogrula, ANINDA degil - CI'da olculerek bulundu:
    # `Element Should Be Visible` hicbir bekleme yapmaz. Onay basligi
    # gorundugu anda bu GORSEL henuz yuklenmemis olabilir; yuklenmemis bir
    # <img> sifir boyutludur ve `is_displayed()` False doner. Yavas bir
    # kosucuda (GitHub Actions) bu, akis dogru calistigi halde testi dusurur.
    #
    # KARSILASTIRMA NOTU - UC YIGININ AYRISTIGI NOKTA:
    #   Playwright : expect(pony_image).to_be_visible()  -> KENDILIGINDEN bekler
    #   Selenium   : is_visible(PONY_IMAGE, timeout=5)   -> bekleme ELLE yazilmis
    #   Robot      : Element Should Be Visible           -> bekleme YOK (bu hata)
    # Beklemeyi hatirlamak Selenium ve Robot'ta gelistiricinin isidir;
    # unutuldugunda test yerelde gecer, CI'da duser.
    Wait Until Element Is Visible    ${PONY_IMAGE}    ${DEFAULT_TIMEOUT}

Cart Should Be Cleared After Order
    ${count} =    Get Cart Badge Count
    Should Be Equal As Integers    ${count}    0
    ...    msg=Siparis sonrasi sepet temizlenmedi

Return To Products After Order
    Click And Wait For Location    ${BACK_HOME_BUTTON}    inventory.html

# =========================================================================== #
# UST SEVIYE IS AKISI (business keyword)
# =========================================================================== #
Complete Purchase For
    [Documentation]    Uctan uca satin alma - TEK KEYWORD.
    ...
    ...    Bu keyword, Robot Framework'un en guclu yanini gosterir: karmasik
    ...    bir is akisi, ust seviyede TEK SATIRA iner ve teknik olmayan bir
    ...    kisi tarafindan bile okunabilir:
    ...
    ...    | Complete Purchase For | standard_user | Sauce Labs Backpack |
    ...
    ...    DIKKAT - ROBOT FRAMEWORK TUZAGI:
    ...    Vararg'in adi `@{product_names}`; BILEREK `@{products}` DEGIL.
    ...    Robot'ta degisken adlari buyuk/kucuk harf, bosluk ve alt cizgi
    ...    duyarsizdir: `@{products}` yazilsaydi, global `${PRODUCTS}` fiyat
    ...    sozlugunu GOLGELERDI ve `Sum Product Prices` sozluk yerine liste
    ...    alip "cannot be converted to dictionary" hatasi verirdi.
    ...    Bu suite'in ilk tam kosumunda tam olarak bu hata yasandi.
    [Arguments]    ${username}    @{product_names}
    Login As    ${username}
    Add Products To Cart    @{product_names}
    Open Cart
    Cart Should Contain Exactly    @{product_names}
    ${expected_subtotal} =    Sum Product Prices    ${PRODUCTS}    ${product_names}
    Proceed To Checkout
    Continue To Checkout Overview
    Checkout Totals Should Be Correct    expected_subtotal=${expected_subtotal}
    Finish Order
    Order Confirmation Should Be Displayed
    Cart Should Be Cleared After Order
