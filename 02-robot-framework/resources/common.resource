*** Settings ***
Documentation       Tum suite'lerin kullandigi ortak kurulum ve yardimci keyword'ler.
...
...                 KARSILASTIRMA NOTU:
...                 Bu dosya, Selenium projesindeki conftest.py'nin karsiligidir.
...                 Fark: pytest'te fixture'lari Python ile yazarsiniz; burada
...                 kurulum/temizlik islemleri de KEYWORD'dur, yani testin
...                 kendisiyle ayni dilde yazilir. Bu, teknik olmayan ekip
...                 uyelerinin de altyapiyi okuyabilmesini saglar.

Library             SeleniumLibrary    run_on_failure=Capture Page Screenshot
Library             Collections
Library             String
Library             OperatingSystem
Library             DateTime
Library             ../libraries/SauceDemoLibrary.py


*** Variables ***
${SCREENSHOT_DIR}       ${CURDIR}/../results/screenshots

# Etki-dogrulamali tiklama parametreleri.
# CLICK_RETRY_BUDGET > VERIFY_TIMEOUT olmali; aksi halde dongü tek deneme yapar.
${CLICK_RETRY_BUDGET}   20s
${VERIFY_TIMEOUT}       3s

${CART_BADGE}           css:[data-test='shopping-cart-badge']
${CART_LINK}            css:[data-test='shopping-cart-link']
${BURGER_BUTTON}        id:react-burger-menu-btn
${BURGER_CLOSE}         id:react-burger-cross-btn
${MENU_WRAP}            css:.bm-menu-wrap
${LOGOUT_LINK}          id:logout_sidebar_link
${ALL_ITEMS_LINK}       id:inventory_sidebar_link
${RESET_APP_LINK}       id:reset_sidebar_link
${ABOUT_LINK}           id:about_sidebar_link
${MENU_ITEM}            css:.bm-item.menu-item
${APP_LOGO}             css:.app_logo
${ERROR_MESSAGE}        css:[data-test='error']
${ERROR_CLOSE}          css:.error-button


*** Keywords ***
# =========================================================================== #
# Tarayici yasam dongusu
# =========================================================================== #
Open Test Browser
    [Documentation]    Tarayiciyi acar ve varsayilan sureleri ayarlar.
    ...
    ...    `options=` parametresi headless modu ve CI icin gerekli argumanlari
    ...    tasir; degeri variables/environment.py icinde uretilir.
    [Arguments]    ${url}=${LOGIN_URL}    ${timeout}=${DEFAULT_TIMEOUT}

    Set Selenium Timeout    ${timeout}
    # Set Selenium Speed 0 = her keyword arasinda YAPAY bekleme yok.
    # (Demo videolari icin 0.2s yapilabilir; testlerde asla kullanilmamali.)
    Set Selenium Speed    0
    Set Selenium Implicit Wait    0

    Run Keyword If    '${BROWSER_OPTIONS}' != '${EMPTY}'
    ...    Open Browser    ${url}    ${BROWSER}    options=${BROWSER_OPTIONS}
    ...    ELSE
    ...    Open Browser    ${url}    ${BROWSER}

    # DIKKAT - IKI AYRI TUZAK, IKISI DE OLCEREK BULUNDU:
    #
    # 1) `Maximize Browser Window` headless modda pencereyi tarayicinin
    #    varsayilan sanal ekran boyutuna (800x600) DUSURUR; yani
    #    --window-size=1920,1080 argumanini geri alir. Dar viewport'ta
    #    bilesenler ust uste biner ve tiklamalar isabet etmez.
    #
    # 2) Bunu duzeltmek icin calisma aninda `Set Window Size` cagirmak DAHA
    #    KOTU sonuc verdi: headless Chrome'da pencereyi acildiktan SONRA
    #    yeniden boyutlandirmak, girdi koordinatlarini sayfa duzeninden
    #    kaydiriyor. Olculen belirti: `Click Element ${POSTAL_CODE_INPUT}`
    #    sonrasi `document.activeElement` = lastName (bir ust alan) oluyor,
    #    ardindan `send_keys` hicbir yere yazmiyor. Ham Selenium send_keys de
    #    ayni sekilde bosa gidiyor.
    #
    # DOGRU COZUM: headless'ta pencere boyutuna calisma aninda HIC dokunmamak;
    # boyut zaten --window-size launch argumaniyla ayarlanmis durumda.
    # (Selenium projesi de tam olarak boyle yapiyor: core/driver_factory.py
    #  icinde set_window_size YALNIZCA headless olmayan modda cagriliyor.)
    IF    not ${HEADLESS}
        Run Keyword And Ignore Error    Maximize Browser Window
    END
    Wait For Page To Be Ready
    ${size} =    Get Window Size
    Log    Tarayici acildi: ${BROWSER} -> ${url} | pencere: ${size}    console=${True}

Close Test Browser
    [Documentation]    Oturumu kapatir. Testin gecip gecmedigine bakmaz.
    Run Keyword And Ignore Error    Close All Browsers

Wait For Page To Be Ready
    [Documentation]    document.readyState == 'complete' olana kadar bekler.
    ...    SeleniumLibrary'de bunun hazir bir keyword'u yoktur; JS ile yaparız.
    Wait Until Keyword Succeeds    ${DEFAULT_TIMEOUT}    200ms
    ...    Current Document Should Be Complete

Current Document Should Be Complete
    ${state} =    Execute Javascript    return document.readyState
    Should Be Equal    ${state}    complete    Sayfa hala yukleniyor: ${state}

# =========================================================================== #
# Suite / Test seviyesi kurulum
# =========================================================================== #
Suite Setup Actions
    [Documentation]    Suite basinda bir kez calisir.
    Create Directory    ${SCREENSHOT_DIR}
    Set Screenshot Directory    ${SCREENSHOT_DIR}
    Log To Console    \n[SUITE] Ortam=${ENV} | Tarayici=${BROWSER} | Adres=${BASE_URL}

Suite Teardown Actions
    Close Test Browser
    Log To Console    [SUITE] Tamamlandi.

Begin Web Test
    [Documentation]    Her testin basinda temiz bir tarayici acar.
    ...
    ...    NEDEN HER TEST ICIN YENI TARAYICI?
    ...    Test izolasyonu icin. Sepet ve oturum bilgisi localStorage'da tutulur;
    ...    tarayiciyi paylasan testler birbirini etkiler. Maliyeti kabul ediyoruz.
    [Arguments]    ${timeout}=${DEFAULT_TIMEOUT}
    Open Test Browser    ${LOGIN_URL}    ${timeout}

End Web Test
    [Documentation]    Her testin sonunda calisir.
    ...    Test BASARISIZ ise ek teshis bilgisi toplar.
    Run Keyword If Test Failed    Collect Failure Diagnostics
    Close Test Browser

Collect Failure Diagnostics
    [Documentation]    Hata aninda URL, ekran goruntusu ve konsol loglarini rapora ekler.
    ...
    ...    KARSILASTIRMA NOTU: Selenium+pytest'te bu isi ~40 satirlik bir
    ...    `pytest_runtest_makereport` hook'u yapar. Burada `run_on_failure`
    ...    ayari zaten ekran goruntusunu otomatik alir; asagisi sadece ekstra.
    ${ok}    ${url} =    Run Keyword And Ignore Error    Get Location
    Run Keyword If    '${ok}' == 'PASS'    Log    Hata anindaki adres: ${url}
    Capture Page Screenshot    hata_{index}.png
    ${logs} =    Run Keyword And Ignore Error    Get Browser Console Log Entries
    Log    Tarayici konsolu: ${logs}

Get Browser Console Log Entries
    [Documentation]    Chromium tabanli tarayicilarda konsol hatalarini doner.
    ${driver} =    Get WebDriver Instance
    ${entries} =    Evaluate    [e for e in $driver.get_log('browser') if e['level']=='SEVERE']
    RETURN    ${entries}

Get WebDriver Instance
    [Documentation]    Alttaki ham Selenium driver nesnesine erisim.
    ...
    ...    Robot Framework'un "kacis kapisi": SeleniumLibrary'nin sunmadigi
    ...    bir seye ihtiyaciniz oldugunda ham WebDriver'a inebilirsiniz.
    ${lib} =    Get Library Instance    SeleniumLibrary
    RETURN    ${lib.driver}

# =========================================================================== #
# Ortak UI keyword'leri (her sayfada gecerli)
# =========================================================================== #
Get Cart Badge Count
    [Documentation]    Sepet rozetindeki sayiyi doner; rozet yoksa 0.
    ${visible} =    Run Keyword And Return Status    Page Should Contain Element    ${CART_BADGE}
    IF    not ${visible}
        RETURN    ${0}
    END
    ${text} =    Get Text    ${CART_BADGE}
    ${count} =    Convert To Integer    ${text}
    RETURN    ${count}

Cart Badge Should Show
    [Documentation]    Rozet beklenen degere ULASANA KADAR bekler.
    ...    Dogrudan `Element Text Should Be` kullanmak yaris durumu yaratir;
    ...    React rozeti asenkron gunceller.
    [Arguments]    ${expected}
    IF    ${expected} == 0
        Wait Until Element Is Not Visible    ${CART_BADGE}    ${SHORT_TIMEOUT}
    ELSE
        Wait Until Element Contains    ${CART_BADGE}    ${expected}    ${DEFAULT_TIMEOUT}
    END

Open Cart
    Click And Wait For Location    ${CART_LINK}    cart.html
    Wait Until Element Is Visible    css:[data-test='cart-list']    ${DEFAULT_TIMEOUT}

Clear Input Field
    [Documentation]    React kontrollu bir input alanini GERCEKTEN temizler.
    ...
    ...    `Clear Element Text` (Selenium'un element.clear() metodu) DOM'daki
    ...    value niteligini bosaltir ama React'in ic state'ini GUNCELLEMEZ:
    ...    ekranda alan bos gorunur, forma eski deger gider. Gercek klavye
    ...    olaylari React'in onChange isleyicisini tetikler.
    [Arguments]    ${locator}
    Press Keys    ${locator}    CTRL+a    DELETE

Type Text With Verify
    [Documentation]    Alana yazar ve yazilanin GERCEKTEN girildigini dogrular.
    ...
    ...    NEDEN GEREKLI - OLCEREK BULUNDU:
    ...    Bu ortamda `Input Text` (ve hatta ham Selenium `send_keys`) zaman
    ...    zaman hicbir hata vermeden HICBIR SEY YAZMIYOR; alan bos kaliyor ve
    ...    test onlarca saniye sonra alakasiz bir hatayla dusuyor.
    ...    Tiklamada oldugu gibi burada da guvenilir olcut "yazildi mi" degil,
    ...    "alanda beklenen deger var mi" sorusudur.
    [Arguments]    ${locator}    ${text}    ${secret}=${False}
    Wait Until Element Is Visible    ${locator}    ${DEFAULT_TIMEOUT}
    Wait Until Keyword Succeeds    ${CLICK_RETRY_BUDGET}    500ms
    ...    Type And Verify Field    ${locator}    ${text}    ${secret}

Type And Verify Field
    [Arguments]    ${locator}    ${text}    ${secret}=${False}
    Clear Input Field    ${locator}
    IF    ${secret}
        # Input Password degeri log.html icinde maskeler.
        Input Password    ${locator}    ${text}
    ELSE
        Input Text    ${locator}    ${text}
    END
    ${actual} =    Get Element Attribute    ${locator}    value
    IF    ${secret}
        ${len_actual} =    Get Length    ${actual}
        ${len_expected} =    Get Length    ${text}
        Should Be Equal As Integers    ${len_actual}    ${len_expected}
        ...    Sifre alanina yazilan karakter sayisi tutmuyor
    ELSE
        Should Be Equal    ${actual}    ${text}
        ...    Alana yazilan deger dogrulanamadi (yazma islemi bosa gitti)
    END

Click Element Via JavaScript
    [Documentation]    Elemani JavaScript ile tiklar - SON CARE.
    ...
    ...    `arguments[0].click()`, elemanin DOM uzerindeki click isleyicisini
    ...    dogrudan cagirir. Fare koordinati, gorunurluk, ust uste binme gibi
    ...    kontrolleri ATLAR. Bu yuzden:
    ...      + Cok guvenilirdir.
    ...      - GERCEK KULLANICI DAVRANISINI TEMSIL ETMEZ. Eleman ekranda
    ...        gorunmuyor veya bir overlay ile kapali olsa bile "calisir";
    ...        yani gercek bir kullanilabilirlik hatasini gizleyebilir.
    ...
    ...    Bu yuzden asagida once GERCEK tiklama denenir, yalnizca o etkisiz
    ...    kalirsa bu yonteme dusulur.
    [Arguments]    ${locator}
    ${element} =    Get WebElement    ${locator}
    Execute Javascript    ARGUMENTS    ${element}    JAVASCRIPT    arguments[0].click();

Click Element Until
    [Documentation]    Tiklamayi, BEKLENEN ETKI gerceklesene kadar tekrarlar.
    ...
    ...    BU SUITE'IN KOSUMUNDA ORTAYA CIKAN GERCEK BIR SORUN:
    ...    SauceDemo'nun yan menusu `react-burger-menu` bileseniyle yapilmis
    ...    olup, tiklama alani `opacity: 0` olan bir <button> katmanidir.
    ...    Chrome 151 + headless ortaminda bu katmana yapilan GERCEK tiklamalar
    ...    (WebDriver'in fare olayi) SESSIZCE YUTULUYOR: hata firlatilmiyor,
    ...    ama menu de acilmiyor. Olcum sonucu: gercek tiklama ~%50 basarili,
    ...    JavaScript tiklamasi 6/6 basarili.
    ...
    ...    Bu, "tiklandi mi?" sorusunun guvenilir olmadigini gosterir.
    ...    Guvenilir olan tek olcut ETKININ GERCEKLESIP GERCEKLESMEDIGIDIR.
    ...
    ...    Strateji:
    ...      1. Gercek tiklamayi dene, etkiyi dogrula (6 sn boyunca tekrarla).
    ...      2. Etki olusmazsa JavaScript tiklamasina dus ve tekrar dogrula.
    ...
    ...    Kullanim:
    ...    | Click Element Until | ${BURGER_BUTTON} | Side Menu Should Be Open |
    ...
    ...    KARSILASTIRMA:
    ...      * Selenium projesinde ayni sorun `core/waits.py` icindeki
    ...        `element_to_be_clickable_and_stable` kosuluyla asilmisti.
    ...      * Playwright'ta bu desene HIC ihtiyac duyulmaz: `click()`,
    ...        elemanin gorunur, sabit ve gercekten tiklanabilir oldugunu
    ...        dogruladiktan sonra tiklar ("actionability" kontrolu).
    ...
    ...    ONEMLI TASARIM AYRINTISI - ILK SURUMDE HATALIYDI:
    ...    Ic dogrulamaya UZUN bir sure (15 sn) verilirse, disaridaki
    ...    `Wait Until Keyword Succeeds` butcesi (asagida 15 sn) tek denemede
    ...    tukenir ve "tekrar deneme" fiilen calismaz. Dogrulama suresi KISA
    ...    (2-3 sn) olmali ki dongü gercekten birkac kez deneyebilsin.
    [Arguments]    ${locator}    @{verification}
    Wait Until Element Is Visible    ${locator}    ${DEFAULT_TIMEOUT}
    ${succeeded} =    Run Keyword And Return Status
    ...    Wait Until Keyword Succeeds    ${CLICK_RETRY_BUDGET}    500ms
    ...    Click And Verify Effect    ${locator}    @{verification}
    IF    not ${succeeded}
        Log    Gercek tiklama etki uretmedi -> JavaScript tiklamasina dusuluyor: ${locator}
        ...    level=WARN
        Click Element Via JavaScript    ${locator}
        Run Keyword    @{verification}
    END

Click And Verify Effect
    [Documentation]    Tikla ve etkiyi dogrula.
    ...    Tiklamadan once elemanin ETKIN (enabled) oldugu dogrulanir; React
    ...    uygulamalarda eleman DOM'a girmis ama olay isleyicisi henuz
    ...    baglanmamis olabilir.
    ...
    ...    DIKKAT - OLCULMUS BIR ANTI-PATTERN:
    ...    Burada bir ara "elemanin konumu iki olcumde ayni kalsin" (position
    ...    stability) beklemesi denendi. Olcum sonucu carpiciydi:
    ...
    ...        hemen tikla ................... 5/5 basarili
    ...        EC.element_to_be_clickable .... 5/5 basarili
    ...        konum sabitligi beklemesi ..... 0/5 basarili
    ...        JavaScript click .............. 5/5 basarili
    ...
    ...    Yani tiklamadan hemen once elemanin KONUMUNU OKUMAK (WebDriver
    ...    `GET .../rect` cagrisi), Chrome 151'de sonraki tiklamayi etkisiz
    ...    hale getiriyor. "Daha dikkatli bekleyelim" diye eklenen kod,
    ...    tam olarak onlemeye calistigi sorunu URETIYORDU.
    ...
    ...    Bu, Selenium ekosisteminin en sinsi yanidir: bekleme stratejisi
    ...    tarayici surumune bagli olarak ters tepebilir ve bunu ancak
    ...    OLCEREK anlarsiniz. Playwright'ta bu karar framework'un icindedir.
    [Arguments]    ${locator}    @{verification}
    Wait Until Element Is Enabled    ${locator}    3s
    Click Element    ${locator}
    Run Keyword    @{verification}

Click And Wait For Element
    [Documentation]    Tikla; belirtilen eleman gorunene kadar gerekirse tekrarla.
    ...    `timeout` degeri KISA tutulmalidir (bkz. Click Element Until).
    [Arguments]    ${locator}    ${expected_locator}    ${timeout}=${VERIFY_TIMEOUT}
    Click Element Until    ${locator}
    ...    Wait Until Element Is Visible    ${expected_locator}    ${timeout}

Click And Wait For Location
    [Documentation]    Tikla; adres beklenen parcayi icerene kadar gerekirse tekrarla.
    [Arguments]    ${locator}    ${fragment}    ${timeout}=${VERIFY_TIMEOUT}
    Click Element Until    ${locator}
    ...    Wait Until Location Contains    ${fragment}    ${timeout}

Side Menu Should Be Open
    Wait Until Element Attribute Value Is    ${MENU_WRAP}    aria-hidden    false    timeout=3s
    Wait Until Element Is Visible    ${LOGOUT_LINK}    3s
    Wait Until Keyword Succeeds    3s    250ms    Side Menu Items Should Be Rendered

Side Menu Should Be Closed
    Wait Until Element Attribute Value Is    ${MENU_WRAP}    aria-hidden    true    timeout=3s
    Wait Until Element Is Not Visible    ${LOGOUT_LINK}    3s

Open Side Menu
    [Documentation]    Yan menuyu acar ve ANIMASYONUN BITMESINI bekler.
    ...    aria-hidden='false' = "acilmaya BASLADI", "acildi" degil; bu yuzden
    ...    menu ogelerinin metinlerinin de dolmasi beklenir.
    Click Element Until    ${BURGER_BUTTON}    Side Menu Should Be Open

Side Menu Items Should Be Rendered
    [Documentation]    Menunun GERCEKTEN acildiginin kaniti.
    ...
    ...    Selenium, viewport disindaki (kaymasi bitmemis) elemanlar icin
    ...    `.text` degerini BOS doner. Tum ogelerin metni dolduysa animasyon
    ...    bitmis demektir. Sadece aria-hidden'a bakildiginda, menu daha
    ...    kayarken tiklaniyor ve tiklama hicbir seye isabet etmiyordu.
    ${texts} =    Get Texts From Elements    ${MENU_ITEM}
    ${count} =    Get Length    ${texts}
    Should Be True    ${count} >= 4    Menu ogeleri henuz cizilmedi
    FOR    ${text}    IN    @{texts}
        Should Not Be Empty    ${text}    Menu ogesi metni henuz bos
    END

Close Side Menu
    Click Element Until    ${BURGER_CLOSE}    Side Menu Should Be Closed

Wait Until Element Attribute Value Is
    [Documentation]    SeleniumLibrary'de olmayan bir bekleme kosulu.
    ...    `Wait Until Keyword Succeeds` ile OZEL BEKLEME URETMEK, Robot'ta
    ...    custom Expected Condition yazmanin standart yoludur.
    [Arguments]    ${locator}    ${attribute}    ${expected}    ${timeout}=${DEFAULT_TIMEOUT}
    Wait Until Keyword Succeeds    ${timeout}    200ms
    ...    Element Attribute Value Should Be    ${locator}    ${attribute}    ${expected}

Logout From Application
    Open Side Menu
    Click Element Until    ${LOGOUT_LINK}
    ...    Wait Until Element Is Visible    css:[data-test='login-button']    3s

Reset Application State
    [Documentation]    Sepeti ve uygulama durumunu sifirlar.
    ...
    ...    ETKI OLCUTU SECIMI - OLCEREK BULUNDU:
    ...    'Reset App State' tiklandiginda SauceDemo sepet rozetini ANINDA
    ...    kaldirir, ancak urun kartlarindaki 'Remove' butonlarini SAYFA
    ...    YENILENENE KADAR geri cevirmez. Ilk denemede etki olcutu olarak
    ...    'Remove butonlari kaybolsun' secilmisti ve keyword hep basarisiz
    ...    oluyordu - tiklama calisiyordu, olcut yanlisti.
    ...    Dogru olcut: sepet rozetinin kaybolmasi.
    Open Side Menu
    Click Element Until    ${RESET_APP_LINK}
    ...    Wait Until Element Is Not Visible    ${CART_BADGE}    3s
    Close Side Menu
    Reload Page
    Wait For Page To Be Ready

Get Side Menu Items
    Open Side Menu
    ${texts} =    Get Texts From Elements    ${MENU_ITEM}
    Close Side Menu
    RETURN    ${texts}

Get Texts From Elements
    [Documentation]    Bir locator'a uyan tum elemanlarin metinlerini doner.
    ...    SeleniumLibrary 6'da `Get Text` tekil calisir; toplu okuma icin
    ...    dongü gerekir. Playwright'ta bu tek satirdir:
    ...    `locator.all_text_contents()`
    [Arguments]    ${locator}
    Wait Until Page Contains Element    ${locator}    ${DEFAULT_TIMEOUT}
    ${elements} =    Get WebElements    ${locator}
    ${texts} =    Create List
    FOR    ${element}    IN    @{elements}
        ${text} =    Get Text    ${element}
        Append To List    ${texts}    ${text}
    END
    RETURN    ${texts}

Location Should Not Contain
    [Documentation]    SeleniumLibrary'de `Location Should Contain` vardir ama
    ...    OLUMSUZ karsiligi YOKTUR. Eksik keyword'u BuiltIn keyword'leriyle
    ...    tamamlamak, Robot Framework'te cok sik yapilan bir istir; kutuphane
    ...    kapsami disina ciktiginiz anda bu tur "yamalar" yazarsiniz.
    [Arguments]    ${expected}    ${message}=Adres beklenmeyen parcayi iceriyor
    ${location} =    Get Location
    Should Not Contain    ${location}    ${expected}    msg=${message}

Error Message Should Be
    [Arguments]    ${expected}
    Wait Until Element Is Visible    ${ERROR_MESSAGE}    ${DEFAULT_TIMEOUT}
    ${actual} =    Get Text    ${ERROR_MESSAGE}
    Should Be Equal    ${actual}    ${expected}
    ...    msg=Hata mesaji beklenenden farkli
