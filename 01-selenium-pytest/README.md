# 01 – Selenium WebDriver + pytest

**Yaklaşım:** Kod merkezli, Page Object Model, tam kontrol.

## Mimari

```
01-selenium-pytest/
├── conftest.py          Fixture'lar + hook'lar (tarayıcı, ekran görüntüsü, rapor)
├── pytest.ini           Marker'lar, log ve rapor ayarları
├── config/
│   ├── config.yaml      Ortam / tarayıcı / timeout değerleri
│   └── settings.py      YAML -> tip güvenli dataclass dönüşümü
├── core/                FRAMEWORK KATMANI (elle yazılan altyapı)
│   ├── driver_factory.py   Chrome/Firefox/Edge başlatma
│   ├── base_page.py        Bekleme + retry + loglama sarmalayıcıları
│   ├── waits.py            Özel Expected Condition'lar
│   ├── soft_assert.py      Toplu doğrulama
│   ├── exceptions.py       Teşhis edilebilir hata tipleri
│   └── logger.py           Dosya + konsol logu
├── pages/               PAGE OBJECT KATMANI
│   ├── login_page.py
│   ├── inventory_page.py
│   ├── cart_page.py
│   ├── checkout_page.py    (3 adım = 3 sınıf)
│   ├── product_detail_page.py
│   └── components/header_component.py   Component Object deseni
├── utils/               Veri yükleme + metin ayrıştırma
├── tests/               61 test / 6 dosya
└── run_tests.ps1
```

## Ölçülen sonuç

61 test, headless Chrome, tek işlem: **6 dakika 7 saniye**, 61/61 geçti.
Test başına ortalama 6,0 saniye — bunun yaklaşık 1,5–2 saniyesi her test için
yeni tarayıcı süreci açma maliyetidir.

## Katman kuralı

```
tests/  ->  pages/  ->  core/  ->  selenium
```

* **Test** hiçbir zaman CSS selector veya `WebDriverWait` görmez.
* **Page Object** hiçbir zaman `assert` yazmaz — durum döner, testin işi doğrulamaktır.
* **Core** hiçbir zaman uygulamayı bilmez — genel amaçlıdır.

## Çalıştırma

```powershell
pip install -r requirements.txt
.\run_tests.ps1                    # tümü, headless
.\run_tests.ps1 -Marker smoke      # sadece smoke
.\run_tests.ps1 -Headed            # tarayıcı görünür
.\run_tests.ps1 -Parallel 4        # 4 process paralel
python -m pytest -m "cart or checkout" -v
python -m pytest tests/test_login.py::test_standard_user_can_login
```

## Bu projede özellikle gösterilenler

| Konu | Nerede |
|------|--------|
| Explicit wait stratejisi, implicit wait'in neden kapalı olduğu | `config/config.yaml`, `core/driver_factory.py` |
| Özel Expected Condition yazımı | `core/waits.py` |
| StaleElementReference'a karşı otomatik retry | `core/base_page.py::_with_stale_retry` |
| Sayfa geçişi döndüren akıcı (fluent) API | `pages/login_page.py::login` |
| Component Object deseni | `pages/components/header_component.py` |
| Veri odaklı test (`parametrize` + JSON) | `tests/test_login.py` |
| Soft assertion | `core/soft_assert.py`, `tests/test_inventory.py` |
| Hata anında ekran görüntüsü + HTML + konsol logu | `conftest.py::pytest_runtest_makereport` |
| İş kuralı doğrulaması (KDV matematiği) | `pages/checkout_page.py::CheckoutTotals.validate` |

## Selenium'un güçlü ve zayıf yanları (bu projede görüldüğü kadarıyla)

**Güçlü**
- W3C standardı; her tarayıcı, her dil, her grid altyapısı destekler.
- Ekosistem devasa: Selenium Grid, BrowserStack, Sauce Labs, Appium (mobil).
- Kurumsal ortamlarda "kabul edilmiş" teknoloji, işgücü bulmak kolay.
- Tam kontrol: her katmanı istediğiniz gibi tasarlarsınız.

**Zayıf**
- `core/` klasöründeki ~600 satır altyapı **her projede yeniden yazılır**.
- Auto-wait yok → flaky test riski doğrudan geliştiricinin disiplinine bağlı.
- Ağ katmanına erişim yok (mock/intercept yapılamaz).
- Test başına yeni tarayıcı = yavaş; izolasyon pahalı.
- Konsol logu yalnızca Chromium'da, "çekerek" okunabiliyor.
- Tarayıcı sürümüne bağımlı: bu projede Chrome 151, yaygın olarak önerilen
  `excludeSwitches: ["enable-automation"]` seçeneğiyle hiç açılmadı
  (`SessionNotCreatedException`). Kod değişmedi, tarayıcı güncellendi, paket kırıldı.

## Bu projede karşılaşılan gerçek sorunlar

| Sorun | Kök neden | Çözüm |
|-------|-----------|-------|
| Chrome hiç açılmıyor | Chrome 151 + `excludeSwitches` uyumsuzluğu | Seçenek kaldırıldı (`core/driver_factory.py`) |
| Menü öğeleri boş metin dönüyor | `aria-hidden=false` "açılmaya başladı" demek; Selenium görüntü alanı dışındaki elemanda `.text` boş döner | Tüm öğelerin metni dolana kadar beklenir (`header_component.py::open_menu`) |
| Konsol hatası testi hep kırmızı | SauceDemo'nun kendi telemetri servisi (backtrace.io) her koşumda 401 dönüyor | Gerekçelendirilmiş "bilinen gürültü" listesi |
| `--browser` çakışması | `pytest-playwright` aynı ortamda kuruluysa kendi `--browser` seçeneğini kaydediyor | `pytest.ini` içinde `-p no:playwright` |
