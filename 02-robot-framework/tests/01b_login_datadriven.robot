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

# dialect=excel ZORUNLU: DataDriver'in varsayilan lehcesi 'Excel-EU' olup
# ayrac olarak NOKTALI VIRGUL kullanir. Virgullu CSV'de tum satir tek bir
# sutun olarak okunur, hicbir arguman sutunu bulunamaz ve suite
# "Test cannot be empty" ile duser.
Library             DataDriver    file=../data/login_scenarios.csv    encoding=utf-8    dialect=excel
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
    [Documentation]    ARGUMAN ADLARI CSV BASLIKLARIYLA BIREBIR AYNI OLMALIDIR.
    ...
    ...    DataDriver, her satir icin bu keyword'u cagirirken argumanlari
    ...    ADLARINA GORE eslestirir ve eslestirme BUYUK/KUCUK HARFE DUYARLIDIR
    ...    (bkz. DataDriver.py -> _get_template_arguments). Yani CSV'deki
    ...    `${USERNAME}` sutunu ancak `${USERNAME}` adli bir argumana baglanir;
    ...    `${username}` yazilirsa "Unassigned requiered argument" hatasi alinir.
    [Arguments]    ${USERNAME}    ${PASSWORD_VALUE}    ${EXPECTED_ERROR}
    Login Should Fail With Error    ${USERNAME}    ${PASSWORD_VALUE}    ${EXPECTED_ERROR}
