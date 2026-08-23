# 03 – Playwright + pytest

**Yaklaşım:** Modern, "batarya dahil", auto-wait odaklı.

## Mimari

```
03-playwright-pytest/
├── conftest.py          Uygulamaya özel fixture'lar (browser yaşam döngüsü HAZIR gelir)
├── pytest.ini           Marker'lar + trace/video/screenshot bayrakları
├── config/settings.py   Ortam ayarları (Selenium sürümünün ~1/3'ü kadar)
├── core/base_page.py    ~90 satır (Selenium sürümü ~250 satır)
├── pages/               Locator tabanlı Page Object'ler
├── utils/
├── tests/
│   ├── ui/              Selenium & Robot ile BİREBİR aynı senaryolar
│   │   ├── test_login.py
│   │   ├── test_inventory.py
│   │   ├── test_cart.py
│   │   ├── test_checkout.py
│   │   └── test_e2e_purchase.py
│   └── advanced/        DİĞER İKİSİNDE KARŞILIĞI OLMAYAN yetenekler
│       ├── test_network_interception.py   Ağ mock'lama, offline, performans
│       ├── test_visual_and_devices.py     Görsel snapshot, mobil emülasyon, a11y
│       └── test_api.py                    API testleri (aynı framework içinde)
└── run_tests.ps1
```

## Ölçülen sonuç

`tests/ui/` (Selenium ve Robot ile birebir aynı 59 test) **100 saniyede**,
tüm paket (75 test) **97–110 saniyede** koşuyor. Aynı senaryolar Selenium'da
6 dakika 7 saniye sürüyor.

Bu paketin bulduğu **gerçek bir kusur**: SauceDemo'nun envanter sayfasında
hiçbir `heading` (h1–h6) elemanı yok — sayfa başlığı `<span>` olarak işlenmiş.
Ekran okuyucu kullanıcıları sayfa yapısında gezinemez (WCAG 2.1 – 1.3.1).
Test `xfail` ile bilinen açık kusur olarak işaretlendi. `get_by_role()`
erişilebilirlik ağacını sorguladığı için bu kusuru buldu; Selenium ve Robot
projelerinde fark edilmeden kalırdı.

## Kurulum

```powershell
pip install -r requirements.txt
python -m playwright install chromium firefox webkit   # tek seferlik
```

Selenium'dan farkı: tarayıcı binary'lerini **Playwright indirir ve sürümü kilitler**.
"Chrome güncellendi, chromedriver uyumsuz" sorunu bu modelde oluşmaz.

## Çalıştırma

```powershell
.\run_tests.ps1                     # tümü
.\run_tests.ps1 -Marker smoke
.\run_tests.ps1 -AllBrowsers        # chromium + firefox + webkit
.\run_tests.ps1 -Headed
.\run_tests.ps1 -Parallel 4
.\run_tests.ps1 -Debug              # inspector + slowmo

# Hata ayıklama araçları (Selenium/Robot'ta karşılığı yok):
python -m playwright show-trace reports\artifacts\<test>\trace.zip
python -m playwright codegen https://www.saucedemo.com    # tıkla, kod üretsin
```

## Selenium'a göre somut farklar (bu projede görülebilen)

| Konu | Selenium projesinde | Playwright projesinde |
|------|--------------------|-----------------------|
| Bekleme | `core/waits.py` (7 özel condition) + her çağrıda `WebDriverWait` | Otomatik; dosya bile yok |
| Stale element | `_with_stale_retry`, 3 deneme + backoff | Locator lazy olduğu için **kavram yok** |
| BasePage boyutu | ~250 satır | ~90 satır |
| conftest — işlevsel kod | 114 satır (60'ı hata anı teşhisi) | 92 satır (teşhis = 3 CLI bayrağı) |
| Test izolasyonu | Test başına yeni **tarayıcı** (~1-2 sn) | Test başına yeni **context** (~20-50 ms) |
| Oturum yeniden kullanımı | Yok (çerezleri elle taşımak gerekir) | `storage_state` ile 1 kez giriş, N test |
| Konsol logları | Yalnızca Chromium, sonradan çekilir | Olay tabanlı, tüm tarayıcılarda |
| Ağ katmanı | Erişim yok (proxy gerekir) | `page.route()` ile tam kontrol |
| API testi | `requests` ile ayrı yapı | `APIRequestContext` framework içinde |
| Mobil | Sadece pencere boyutu; gerçeği için Appium | ~130 hazır cihaz profili |
| Hata ayıklama | Ekran görüntüsü + log | **Trace viewer**: her adımın DOM anlık görüntüsü, ağ, konsol |

## Playwright'ın güçlü ve zayıf yanları

**Güçlü**
- Auto-wait sayesinde flaky test oranı belirgin şekilde düşük.
- Trace Viewer: bir hatayı "zaman içinde geri sararak" incelemek.
- Ağ mock'lama, cihaz emülasyonu, çoklu context, API — hepsi tek pakette.
- Context modeli sayesinde izolasyon hem tam hem ucuz → paralellik çok verimli.
- `codegen` ile kayıt-oynat başlangıcı, `--ui` modu.

**Zayıf**
- Yalnızca Chromium/Firefox/WebKit; **gerçek** Chrome/Edge yerine bundled
  sürümler kullanılır (kanal seçilebilir ama IE/Safari-macOS desteği yok).
- Ekosistem Selenium kadar geniş değil; kurumsal araç entegrasyonları daha yeni.
- Python sürümü, TypeScript sürümünün gerisinde (`expect.soft`,
  `toHaveScreenshot`, fixture zenginliği).
- Mobil için gerçek cihaz testi yok — emülasyon var, Appium'un yerini tutmaz.
- Tarayıcı binary'leri ~300 MB disk alanı ister.
