*** Settings ***
Documentation       CSV dosyasindan uretilen veri odakli login testleri.
...
...                 DATADRIVER NEDIR?
...                 Asagida TEK BIR test tanimi vardir. DataDriver kutuphanesi
...                 kosum aninda `data/login_scenarios.csv` dosyasini okur ve
...                 HER SATIR ICIN AYRI BIR TEST URETIR. Rapor 5 ayri test
...                 gosterir, kod tek satirdir.
...
...                 NEDEN ONEMLI?
...                 Test senaryolarini Excel/CSV'de tutabilen bir is analisti,
...                 tek satir kod yazmadan yeni test ekleyebilir. Bu, Robot
...                 Framework'un "teknik olmayan ekip uyeleri de katkida
...                 bulunabilsin" felsefesinin en somut ornegidir.
...
...                 Selenium/Playwright karsiligi: `@pytest.mark.parametrize`
...                 ile JSON okumak - ama orada veriyi kod ile testlere
...                 baglamak yine gelistiricinin isidir.

Library             DataDriver    file=../data/login_scenarios.csv    encoding=utf-8
Resource            ../resources/common.resource
Resource            ../resources/pages/login_page.resource

Test Setup          Begin Web Test
Test Teardown       End Web Test
Test Template       Gecersiz Giris Denemesi

Force Tags          login    datadriven


*** Test Cases ***
Login senaryosu sablonu    ${USERNAME}    ${PASSWORD_VALUE}    ${EXPECTED_ERROR}


*** Keywords ***
Gecersiz Giris Denemesi
    [Arguments]    ${username}    ${password}    ${expected_error}
    Login Should Fail With Error    ${username}    ${password}    ${expected_error}
