*** Settings ***
Documentation       Uctan uca satin alma senaryolari.
...
...                 Bu dosya Robot Framework'un vitrinidir: asagidaki testler
...                 neredeyse duz Ingilizce/Turkce cumlelerden olusur. Teknik
...                 olmayan bir ekip uyesi bu dosyayi okuyup "sistem ne yapiyor"
...                 sorusunu yanitlayabilir. Selenium ve Playwright projelerinde
...                 ayni okunakliliga ulasmak icin Python bilmek gerekir.

Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource
Resource            ../resources/pages/inventory_page.resource
Resource            ../resources/pages/cart_page.resource
Resource            ../resources/pages/checkout_page.resource

Test Setup          Begin Web Test
Test Teardown       End Web Test

Force Tags          e2e


*** Test Cases ***
Uctan uca satin alma akisi tamamlanmali
    [Documentation]    Giris -> urun sec -> sepet -> checkout -> siparis.
    ...    Tek keyword ile ifade edilen bir is akisi.
    [Tags]    smoke
    Complete Purchase For    ${STANDARD_USER}
    ...    Sauce Labs Backpack
    ...    Sauce Labs Bike Light
    ...    Sauce Labs Onesie

Tek urunle satin alma tamamlanmali
    [Tags]    smoke
    Complete Purchase For    ${STANDARD_USER}    Sauce Labs Fleece Jacket

Tum urunlerle satin alma tamamlanmali
    [Documentation]    En buyuk sepet senaryosu - 6 urun.
    [Tags]    regression
    Complete Purchase For    ${STANDARD_USER}    @{PRODUCT_NAMES}

Siparis sonrasi yeni siparise baslanabilmeli
    [Documentation]    Siparis tamamlandiktan sonra sepet sifirlanmali ve
    ...    kullanici temiz bir envanter sayfasina donebilmeli.
    [Tags]    regression
    Complete Purchase For    ${STANDARD_USER}    Sauce Labs Fleece Jacket
    Return To Products After Order
    Inventory Page Should Be Open
    ${count} =    Get Cart Badge Count
    Should Be Equal As Integers    ${count}    0
    Product Should Not Be In Cart    Sauce Labs Fleece Jacket

Yavas kullaniciyla uctan uca akis tamamlanmali
    [Documentation]    performance_glitch_user ile ayni akis.
    ...
    ...    Bu test, bekleme stratejisinin dayanikliligini olcer.
    ...    `Wait Until ...` keyword'leri yerine `Sleep` kullanan bir suite
    ...    burada ya kirilir ya da gereksiz yere yavaslar.
    [Tags]    regression    slow
    # Iki ayar birlikte gerekiyor:
    #   1. Set Selenium Timeout -> kutuphanenin VARSAYILAN suresi
    #   2. Set Test Variable ${DEFAULT_TIMEOUT} -> keyword'lerimize ACIKCA
    #      gecirilen sure (Wait Until ... ${DEFAULT_TIMEOUT})
    # Sadece birincisi ayarlandiginda, sureyi acikca veren keyword'ler yine
    # 15 saniyede pes eder. Bu, "timeout'u tek yerden yonetmek" konusunda
    # ogretici bir tuzaktir.
    Set Selenium Timeout    ${SLOW_USER_TIMEOUT}
    Set Test Variable    ${DEFAULT_TIMEOUT}    ${SLOW_USER_TIMEOUT}
    Complete Purchase For    ${GLITCH_USER}    Sauce Labs Backpack

Problem kullanici bilinen hatalari
    [Documentation]    problem_user, SauceDemo'nun kasitli olarak bozdugu
    ...    kullanicidir. Bu testin AMACI hatalari "yakalamak" degil, hala
    ...    VAR OLDUKLARINI izlemektir (characterization test). Hatalardan biri
    ...    duzeltilirse test uyari verir ve ekip bunu farkeder.
    ...
    ...    Izlenen iki bilinen hata:
    ...      1. 'Add to cart' butonu urunu sepete eklemiyor.
    ...      2. Checkout formunda soyad alani duzgun doldurulamiyor.
    [Tags]    regression    known-issue
    Login As    ${PROBLEM_USER}

    # --- BILINEN HATA 1 ---
    # Basarisiz olmasi BEKLENDIGI icin kisa bir sure yeterli; 15 sn beklemek
    # testi gereksiz yere uzatir.
    Set Selenium Timeout    5s
    ${added} =    Run Keyword And Return Status
    ...    Add Product To Cart    Sauce Labs Backpack
    Set Selenium Timeout    ${DEFAULT_TIMEOUT}
    IF    not ${added}
        Log    BILINEN HATA 1 dogrulandi: problem_user urunu sepete ekleyemiyor.
        ...    level=WARN
    ELSE
        Log    BILINEN HATA 1 ARTIK YOK - uygulama duzeltilmis olabilir.    level=WARN
    END

    # --- BILINEN HATA 2 ---
    # SauceDemo bos sepetle de checkout'a izin verdigi icin forma ulasabiliyoruz.
    Go To Cart Page
    Proceed To Checkout
    Fill Checkout Information    Ali    Kiratli    34710
    ${last_name} =    Get Value    ${LAST_NAME_INPUT}
    IF    '${last_name}' == 'Kiratli'
        Log    BILINEN HATA 2 ARTIK YOK - soyad alani duzgun dolduruldu.    level=WARN
    ELSE
        Log    BILINEN HATA 2 dogrulandi: yazilan 'Kiratli', okunan '${last_name}'
        ...    level=WARN
    END

Menu ogeleri beklenen sirada olmali
    [Tags]    regression    navigation
    Login As Standard User
    ${items} =    Get Side Menu Items
    ${expected} =    Create List    All Items    About    Logout    Reset App State
    Lists Should Be Equal    ${items}    ${expected}
    ...    msg=Yan menu ogeleri degismis

Sayfa basliklari tutarli olmali
    [Tags]    regression    navigation
    Login As Standard User
    Title Should Be    Swag Labs
    Element Text Should Be    ${APP_LOGO}    Swag Labs
    Open Cart
    Title Should Be    Swag Labs
