# 02 – Robot Framework + SeleniumLibrary

**Yaklaşım:** Keyword-driven, doğal dile yakın, düşük giriş bariyeri.

> **Önemli:** Robot Framework, Selenium'un *alternatifi* değildir.
> SeleniumLibrary'nin altında **yine Selenium WebDriver çalışır**.
> Robot Framework, Selenium'un **üzerine kurulan bir soyutlama katmanıdır**.

## Mimari

```
02-robot-framework/
├── tests/                         TEST KATMANI (.robot)
│   ├── __init__.robot             Suite seviyesi setup/teardown
│   ├── 01_login.robot             [Template] ile veri odaklı
│   ├── 01b_login_datadriven.robot DataDriver + CSV
│   ├── 02_inventory.robot
│   ├── 03_cart.robot
│   ├── 04_checkout.robot
│   └── 05_e2e.robot
├── resources/                     KEYWORD KATMANI (.resource)
│   ├── common.resource            Tarayıcı yaşam döngüsü + ortak keyword'ler
│   └── pages/                     "Page Object"in Robot karşılığı
│       ├── login_page.resource
│       ├── inventory_page.resource
│       ├── cart_page.resource
│       └── checkout_page.resource
├── libraries/
│   └── SauceDemoLibrary.py        Python keyword kütüphanesi (hesaplama/doğrulama)
├── variables/
│   └── environment.py             Ortam değişkenleri (Python variable file)
├── data/
│   └── login_scenarios.csv        DataDriver test verisi
├── results/                       report.html + log.html + ekran görüntüleri
└── run_tests.ps1
```

## Robot'ta "Page Object" nasıl olur?

Robot'ta sınıf yoktur. Kapsülleme **dosya düzeyindedir**:

| Selenium (Python) | Robot Framework |
|-------------------|-----------------|
| `class LoginPage:` | `resources/pages/login_page.resource` |
| Sınıf sabiti `USERNAME_INPUT` | `*** Variables ***` içindeki `${LOGIN_USERNAME_INPUT}` |
| Metot `def login(self, ...)` | `*** Keywords ***` içindeki `Login As` |
| `conftest.py` fixture | `Test Setup` / `Suite Setup` |
| `@pytest.mark.parametrize` | `[Template]` veya DataDriver |
| `pytest -m smoke` | `robot --include smoke` |

## Çalıştırma

```powershell
pip install -r requirements.txt
.\run_tests.ps1                       # tümü
.\run_tests.ps1 -Tags smoke           # etiket filtresi
.\run_tests.ps1 -Tags "cart OR checkout"
.\run_tests.ps1 -Suite 03_cart        # tek suite
.\run_tests.ps1 -Headed               # görünür tarayıcı
.\run_tests.ps1 -Parallel 4           # pabot ile paralel

# Doğrudan robot komutuyla:
robot --outputdir results --variablefile variables/environment.py:prod:chrome:true tests/
robot --include smoke --exclude slow --outputdir results tests/
```

## Bu projede özellikle gösterilenler

| Konu | Nerede |
|------|--------|
| Keyword katmanlaması (test → sayfa → ortak → Python) | tüm `resources/` |
| `[Template]` ile veri odaklı test | `tests/01_login.robot`, `04_checkout.robot` |
| DataDriver + CSV ile test üretimi | `tests/01b_login_datadriven.robot` |
| Python kütüphanesi ile hesaplama | `libraries/SauceDemoLibrary.py` |
| `Wait Until Keyword Succeeds` ile özel bekleme | `resources/common.resource` |
| **Etki doğrulamalı tıklama** (`Click Element Until`) | `resources/common.resource` |
| JavaScript tıklama (son çare, gerekçesiyle) | `Click Element Via JavaScript` |
| React kontrollü input'u gerçekten temizleme | `login_page.resource::Clear React Input` |
| Ham WebDriver'a inme (kaçış kapısı) | `Get WebDriver Instance` |
| Soft assertion (`Run Keyword And Continue On Failure`) | `inventory_page.resource` |
| İş kuralı doğrulaması (KDV) | `SauceDemoLibrary.Verify Checkout Totals` |
| Otomatik hata ekran görüntüsü | `Library SeleniumLibrary run_on_failure=...` |
| Rapora HTML tablo basma | `Log Test Data Table` |

## Robot Framework'ün güçlü ve zayıf yanları

**Güçlü**
- **Rapor kalitesi rakipsiz**: `log.html` her keyword'ü, argümanını ve süresini
  ağaç yapısında gösterir. Hiçbir şey kodlamadan.
- Öğrenme eğrisi çok düşük; test yazmak için programlama bilmek gerekmez.
- Kurulum/temizlik, etiketleme, veri odaklı test **dilin içinde**, kütüphane değil.
- Aynı test dosyası SeleniumLibrary yerine Browser (Playwright) kütüphanesine
  geçirilebilir — testler değil, keyword katmanı değişir.
- İş analisti / manuel testçi ekiplerinin katkı verebildiği tek yaklaşım.

**Zayıf**
- Karmaşık mantık (döngü içinde koşul, veri dönüşümü) çabuk okunaksızlaşır;
  Python'a inmek gerekir — `libraries/` klasörünün varlık sebebi budur.
- Boşluk duyarlı sözdizimi (2+ boşluk ayırıcı) yeni başlayanı çok yorar.
- IDE desteği ve refactor araçları Python/TypeScript kadar olgun değil.
- Kod tekrarını engellemek (DRY) sınıf/kalıtım olmadığı için daha zordur.
- SeleniumLibrary üzerinden çalıştığı için Selenium'un tüm sınırları geçerlidir
  (ağ mock'lama yok, auto-wait yok).

## Bu projede karşılaşılan gerçek sorunlar

Kod içindeki yorumlarda ayrıntılı anlatıldı; özet:

| Sorun | Kök neden | Çözüm |
|-------|-----------|-------|
| Tıklama hatasız geçiyor ama etkisiz | `react-burger-menu`'nün `opacity:0` buton katmanına giden fare olayları Chrome 151 headless'ta kayboluyor (ölçüm: native ~%50, JS 6/6) | `Click Element Until` — etki doğrula, gerekirse JS tıklamaya düş |
| "Boş kullanıcı adı" testi yanlış hata alıyor | `Clear Element Text` DOM'u temizler, React state'ini güncellemez | `Press Keys ... CTRL+a DELETE` |
| `cannot be converted to dictionary` | `@{products}` vararg'ı global `${PRODUCTS}` sözlüğünü gölgeledi (Robot değişken adları boşluk/harf duyarsız) | `@{product_names}` olarak yeniden adlandırıldı |
| Bileşenler üst üste biniyor | `Maximize Browser Window` headless'ta pencereyi 800×600'e düşürüyor | Headless'ta `Set Window Size` |
| Yavaş kullanıcı testi timeout | `Set Selenium Timeout` yalnızca varsayılanı değiştirir, açıkça verilen süreleri değil | `Set Test Variable ${DEFAULT_TIMEOUT}` da gerekiyor |
