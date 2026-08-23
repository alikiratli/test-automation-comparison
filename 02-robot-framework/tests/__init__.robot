*** Settings ***
Documentation       SauceDemo Regresyon Paketi - Robot Framework
...
...                 Bu __init__.robot dosyasi, `tests/` klasorunu bir SUITE
...                 haline getirir ve altindaki tum suite'ler icin ortak
...                 kurulum/temizlik saglar.
...
...                 KARSILASTIRMA NOTU:
...                 pytest'te bunun karsiligi `conftest.py` icindeki
...                 `scope="session"` fixture'lardir. Robot'ta hiyerarsi
...                 KLASOR YAPISINDAN gelir - kod yazmadan, dosya adiyla.

Resource            ../resources/common.resource

Suite Setup         Suite Setup Actions
Suite Teardown      Suite Teardown Actions

Metadata            Uygulama        SauceDemo
Metadata            Ortam           ${ENV}
Metadata            Tarayici        ${BROWSER}
Metadata            Adres           ${BASE_URL}
Metadata            Framework       Robot Framework + SeleniumLibrary
