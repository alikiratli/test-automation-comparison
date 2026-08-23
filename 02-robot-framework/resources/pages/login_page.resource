*** Settings ***
Documentation       Login sayfasinin keyword'leri ve locator'lari.
...
...                 ROBOT'TA "PAGE OBJECT" NASIL OLUR?
...                 Robot'ta sinif yoktur. Onun yerine her sayfa icin bir
...                 .resource dosyasi acilir: locator'lar `*** Variables ***`
...                 icinde, davranislar `*** Keywords ***` icinde durur.
...                 Kapsulleme sinif yerine DOSYA duzeyindedir.

Resource            ../common.resource


*** Variables ***
${LOGIN_USERNAME_INPUT}     css:[data-test='username']
${LOGIN_PASSWORD_INPUT}     css:[data-test='password']
${LOGIN_BUTTON}             css:[data-test='login-button']
${LOGIN_LOGO}               css:.login_logo
${LOGIN_CREDENTIALS_BOX}    id:login_credentials


*** Keywords ***
Login Page Should Be Open
    Wait Until Element Is Visible    ${LOGIN_BUTTON}    ${DEFAULT_TIMEOUT}
    Element Should Be Visible    ${LOGIN_USERNAME_INPUT}
    Element Should Be Visible    ${LOGIN_PASSWORD_INPUT}

Go To Login Page
    Go To    ${LOGIN_URL}
    Wait For Page To Be Ready
    Login Page Should Be Open

Input Login Credentials
    [Documentation]    Kullanici adi ve sifreyi girer. Bos deger verilirse
    ...    alan React-guvenli bicimde temizlenir.
    [Arguments]    ${username}    ${password}

    IF    '${username}' != '${EMPTY}'
        Type Text With Verify    ${LOGIN_USERNAME_INPUT}    ${username}
    ELSE
        Clear Input Field    ${LOGIN_USERNAME_INPUT}
    END

    IF    '${password}' != '${EMPTY}'
        Type Text With Verify    ${LOGIN_PASSWORD_INPUT}    ${password}    secret=${True}
    ELSE
        Clear Input Field    ${LOGIN_PASSWORD_INPUT}
    END

Submit Login Form
    [Documentation]    Giris denemesi iki sonuctan birini uretmeli:
    ...    envanter sayfasi ya da hata mesaji.
    Click Element Until    ${LOGIN_BUTTON}
    ...    Wait Until Keyword Succeeds    3s    250ms    Login Result Should Appear

Login Result Should Appear
    ${url} =    Get Location
    ${logged_in} =    Run Keyword And Return Status
    ...    Should Contain    ${url}    inventory.html
    IF    not ${logged_in}
        Element Should Be Visible    ${ERROR_MESSAGE}
    END

Login With Credentials
    [Documentation]    Giris yapar; SONUCU DOGRULAMAZ.
    ...    Dogrulama cagiran testin isidir - bu ayrim, keyword'un hem pozitif
    ...    hem negatif senaryolarda kullanilabilmesini saglar.
    [Arguments]    ${username}    ${password}
    Input Login Credentials    ${username}    ${password}
    Submit Login Form

Login As
    [Documentation]    Basarili giris yapar ve envanter sayfasini dogrular.
    ...    Testlerin %80'i bu keyword ile baslar.
    [Arguments]    ${username}    ${password}=${PASSWORD}
    Login With Credentials    ${username}    ${password}
    Wait Until Location Contains    inventory.html    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    css:[data-test='inventory-list']    ${DEFAULT_TIMEOUT}
    Log    Giris basarili: ${username}

Login As Standard User
    Login As    ${STANDARD_USER}

Login Should Fail With Error
    [Arguments]    ${username}    ${password}    ${expected_error}
    Login With Credentials    ${username}    ${password}
    Error Message Should Be    ${expected_error}
    Location Should Not Contain    inventory.html

Login Error Should Be Visible
    Wait Until Element Is Visible    ${ERROR_MESSAGE}    ${DEFAULT_TIMEOUT}

Dismiss Login Error
    Click Element Until    ${ERROR_CLOSE}
    ...    Wait Until Element Is Not Visible    ${ERROR_MESSAGE}    3s

Login Field Should Be Marked Invalid
    [Documentation]    SauceDemo hatali alanlara 'error' CSS sinifi ekler.
    [Arguments]    ${locator}
    ${class} =    Get Element Attribute    ${locator}    class
    Should Contain    ${class}    error
    ...    msg=Alan hatali olarak isaretlenmemis: ${locator}

Password Field Should Be Masked
    ${type} =    Get Element Attribute    ${LOGIN_PASSWORD_INPUT}    type
    Should Be Equal    ${type}    password    msg=Sifre alani maskelenmemis
