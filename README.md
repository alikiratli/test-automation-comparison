# Test Otomasyon Karşılaştırma Projesi

**Aynı uygulama. Aynı test senaryoları. Üç farklı otomasyon teknolojisi.**

🇹🇷 **Türkçe** · 🇬🇧 [English](README.en.md) · 🇩🇪 [Deutsch](README.de.md)

[![CI](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml)
[![Tam paket](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.20+-43B02A?logo=selenium&logoColor=white)
![Robot Framework](https://img.shields.io/badge/Robot%20Framework-7.0+-000000?logo=robotframework&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.44+-2EAD33?logo=playwright&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

Bu depo [SauceDemo](https://www.saucedemo.com) uygulamasını **üç ayrı otomasyon
yığınıyla** baştan sona test eder. Amaç bir framework'ü "kazandırmak" değil;
gerçek bir projede üç yaklaşımın **mimari, okunabilirlik, bakım maliyeti, hız ve
yetenek** farklarını yan yana, ölçülmüş verilerle göstermektir.

---

## İçindekiler

- [Neden aynı uygulama, aynı senaryolar?](#neden-aynı-uygulama-aynı-senaryolar)
- [Depo yapısı](#depo-yapısı)
- [Ölçülen sonuçlar](#ölçülen-sonuçlar)
- [Üç proje, üç mimari yaklaşım](#üç-proje-üç-mimari-yaklaşım)
- [Neden üçü de Python?](#neden-üçü-de-python)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Bu projenin bulduğu gerçek kusur](#bu-projenin-bulduğu-gerçek-kusur)
- [Test hesapları](#test-hesapları)
- [Sürekli entegrasyon (CI)](#sürekli-entegrasyon-ci)
- [Raporu yeniden üretmek](#raporu-yeniden-üretmek)
- [Lisans](#lisans)

---

## Neden aynı uygulama, aynı senaryolar?

Framework karşılaştırmalarının çoğu elma ile armudu kıyaslar: farklı sitelerde,
farklı senaryolarla yazılmış kodlara bakılır ve çıkan fark framework'e yazılır.
Burada **tek değişken framework'tür** — uygulama, senaryolar, doğrulamalar ve
test verisi üç projede de birebir aynıdır.

| # | Senaryo | Selenium | Robot | Playwright |
|---|---------|:--------:|:-----:|:----------:|
| 1 | Login – geçerli / geçersiz / kilitli kullanıcı (data-driven) | ✔ | ✔ | ✔ |
| 2 | Ürün listesi – sayı, isim/fiyat sıralama doğrulaması | ✔ | ✔ | ✔ |
| 3 | Sepet – ekle / çıkar / rozet sayacı / kalıcılık | ✔ | ✔ | ✔ |
| 4 | Checkout – form validasyonu, KDV & toplam matematiği | ✔ | ✔ | ✔ |
| 5 | Uçtan uca satın alma akışı | ✔ | ✔ | ✔ |
| 6 | Navigasyon / menü / logout / session temizliği | ✔ | ✔ | ✔ |
| 7 | Ağ katmanı mock'lama, trace, video, görsel regresyon, API testi | ✖ | ✖ | ✔ |

Son satır kasıtlıdır: Playwright'ın diğer ikisinde **native olarak bulunmayan**
yeteneklerini de göstermek için eklenmiştir. Hız kıyası ise her zaman **birebir
aynı senaryolar** üzerinden yapılır, bu ek testler kıyasa dahil edilmez.

---

## Depo yapısı

```
Automation/
├── 01-selenium-pytest/     Selenium WebDriver 4 + pytest + Page Object Model
├── 02-robot-framework/     Robot Framework 7 + SeleniumLibrary (keyword-driven)
├── 03-playwright-pytest/   Playwright (sync API) + pytest + Locator/POM
├── shared/                 Üç projenin de okuduğu ortak test verisi
│   ├── users.json          Kullanıcı hesapları ve beklenen davranışları
│   └── products.json       Ürün adları, fiyatları, sıralama beklentileri
├── docs/
│   └── generate_report.py  Karşılaştırma raporunu (.docx) üreten script
└── Otomasyon_Karsilastirma_Raporu.docx   Nihai karşılaştırma raporu
```

`shared/` klasörü bilerek ortaktır: üç proje de aynı JSON dosyalarını okur, böylece
"test verisi farklıydı" itirazı baştan kapanır. Selenium projesindeki
`test_shared_data_file_is_consistent` testi bu dosyaların tutarlılığını doğrular.

---

## Ölçülen sonuçlar

> Aşağıdaki sayılar tahmin değildir — hepsi **aynı makinede, headless Chrome ile
> gerçekten koşturulan** testlerden alınmıştır.

### Tüm paket

| Yığın | Test sayısı | Süre | Test başına | Sonuç |
|-------|:-----------:|------|:-----------:|-------|
| Selenium + pytest | 61 | 6 dk 07 sn (367 sn) | 6,0 sn | 61 geçti |
| Robot Framework | 51 | ≈9,5 dk (577 sn) | ≈11,3 sn | 50 geçti, 1 tekrar denemede |
| Playwright + pytest | 75 | 1 dk 37 sn (97 sn) | 1,3 sn | 74 geçti, 1 `xfail` |

### Birebir aynı login senaryoları (adil kıyas)

| Yığın | Senaryo | Süre | Göreli |
|-------|:-------:|------|:------:|
| Selenium + pytest | 16 | 77 sn | 3,2× |
| Robot Framework | 15 | 102 sn | 4,2× |
| Playwright + pytest | 15 | 24 sn | 1,0× (referans) |

> **Robot satırındaki iki not.** Test sayısı 47 değil 51: DataDriver suite'i
> CSV'yi artık gerçekten genişletiyor ve tek satırlık şablondan 5 test üretiyor
> (önceden CSV hiç okunamıyor, suite tek bir bozuk testle düşüyordu). "1 tekrar
> denemede" ise `performance_glitch_user` senaryosudur: SauceDemo'nun kasıtlı
> olarak yavaşlatılmış hesabı canlı siteye karşı ölçüldüğünde ~3 koşumda 1
> düşüyor, tek başına tekrarlandığında geçiyor. CI bu yüzden Robot'u da
> Selenium/Playwright gibi yeniden deniyor.

**Fark nereden geliyor?** Selenium ve Robot her test için yeni bir tarayıcı süreci
açar; bu tek başına test başına ~1–2 saniyedir. Playwright ise tek tarayıcı süreci
üzerinde izole `BrowserContext` açar — maliyeti ~20–50 milisaniyedir. Ayrıca
Playwright tarayıcıyı CDP/WebSocket üzerinden doğrudan sürer; WebDriver protokolü
ve aradaki `chromedriver` süreci devre dışıdır.

---

## Üç proje, üç mimari yaklaşım

### `01-selenium-pytest/` — Kod merkezli, tam kontrol

Elle yazılmış bir **framework katmanı** içerir; hazır bir soyutlamaya yaslanmaz.
Katman kuralı katıdır:

```
tests/  ->  pages/  ->  core/  ->  selenium
```

* **Test** hiçbir zaman CSS selector veya `WebDriverWait` görmez.
* **Page Object** hiçbir zaman `assert` yazmaz — durum döner, doğrulamak testin işidir.
* **Core** hiçbir zaman uygulamayı bilmez — genel amaçlıdır.

`core/` altında driver factory, bekleme/retry sarmalayıcıları, özel Expected
Condition'lar, soft assert, teşhis edilebilir hata tipleri ve loglama bulunur.
Selenium 4.6+ ile gelen **Selenium Manager** sürücüyü otomatik indirir; ayrıca
`chromedriver.exe` indirmenize gerek yoktur.

### `02-robot-framework/` — Keyword-driven, düşük giriş bariyeri

> Robot Framework, Selenium'un *alternatifi* değildir. SeleniumLibrary'nin altında
> **yine Selenium WebDriver çalışır**. Robot, Selenium'un **üzerine kurulan bir
> soyutlama katmanıdır**.

Robot'ta sınıf yoktur; kapsülleme **dosya düzeyindedir**:

| Selenium (Python) | Robot Framework |
|-------------------|-----------------|
| `class LoginPage:` | `resources/pages/login_page.resource` |
| Sınıf sabiti `USERNAME_INPUT` | `*** Variables ***` içindeki `${LOGIN_USERNAME_INPUT}` |
| Metot `def login(self, ...)` | `*** Keywords ***` içindeki `Login As` |
| `conftest.py` fixture | `Test Setup` / `Suite Setup` |
| `@pytest.mark.parametrize` | `[Template]` veya DataDriver |
| `pytest -m smoke` | `robot --include smoke` |

Hesaplama ve karmaşık doğrulama gerektiren işler `libraries/SauceDemoLibrary.py`
içindeki **Python keyword kütüphanesine** taşınmıştır — Robot'un doğal sınırının
nerede başladığını göstermek için.

### `03-playwright-pytest/` — Modern, hızlı, geniş yetenekli

`tests/ui/` diğer iki projeyle **birebir aynı** senaryoları içerir. `tests/advanced/`
ise Selenium ve Robot'ta native karşılığı olmayanları gösterir:

* **Ağ katmanı mock'lama** — `page.route()` ile istek yakalama / değiştirme
* **Görsel regresyon** — referans PNG'ler `reports/visual_baseline/` altında sürüm kontrolündedir
* **Cihaz emülasyonu** — mobil viewport / user-agent / touch
* **API testi** — `APIRequestContext` ile UI'sız doğrulama
* **Trace & video** — başarısız testin adım adım kaydı

Otomatik bekleme (auto-waiting) sayesinde `WebDriverWait` benzeri açık beklemeler
neredeyse tamamen ortadan kalkar; `get_by_role()` locator'ları ise DOM yerine
**erişilebilirlik ağacını** sorgular.

---

## Neden üçü de Python?

Playwright'ın en yaygın kullanımı TypeScript'tir, fakat bu projede üçü de Python
ile yazılmıştır. Sebep: karşılaştırmanın **dil farkıyla kirlenmemesi**. TypeScript
ile yazılsaydı gördüğünüz farkların bir kısmı "TS vs Python" farkı olurdu,
framework farkı değil. Raporda TypeScript varyantının getirdiği ek farklar ayrıca
not edilmiştir.

---

## Kurulum

**Önerilen: her proje için ayrı sanal ortam.**

```powershell
foreach ($p in "01-selenium-pytest","02-robot-framework","03-playwright-pytest") {
    python -m venv "$p\.venv"
    & "$p\.venv\Scripts\python.exe" -m pip install -r "$p\requirements.txt"
}
& "03-playwright-pytest\.venv\Scripts\python.exe" -m playwright install chromium firefox webkit
```

<details>
<summary><b>Neden ayrı ortam? (tek ortam kullanmak isterseniz okuyun)</b></summary>

<br>

`pytest-playwright` eklentisi, kurulduğu ortamdaki **her** pytest koşumunda
otomatik yüklenir ve kendi `--browser` seçeneğini kaydeder. Selenium projesi de
`--browser` tanımladığı için tek ortamda şu hata alınır:

```
argparse.ArgumentError: argument --browser: conflicting option string: --browser
```

Selenium projesi bunu `pytest.ini` içindeki `-p no:playwright` satırıyla zaten
devre dışı bırakır, dolayısıyla tek ortam da çalışır:

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r 01-selenium-pytest\requirements.txt
pip install -r 02-robot-framework\requirements.txt
pip install -r 03-playwright-pytest\requirements.txt
python -m playwright install chromium firefox webkit
```

</details>

---

## Çalıştırma

Her projenin kendi `run_tests.ps1` sarmalayıcısı vardır:

```powershell
cd 01-selenium-pytest ; .\run_tests.ps1
cd 02-robot-framework ; .\run_tests.ps1
cd 03-playwright-pytest ; .\run_tests.ps1
```

Sık kullanılan seçenekler:

```powershell
# Selenium / Playwright (pytest)
.\run_tests.ps1 -Marker smoke      # sadece smoke testleri
.\run_tests.ps1 -Headed            # tarayıcı görünür
.\run_tests.ps1 -Parallel 4        # 4 process paralel
python -m pytest -m "cart or checkout" -v
python -m pytest tests/test_login.py::test_standard_user_can_login

# Robot Framework
.\run_tests.ps1 -Tags smoke
.\run_tests.ps1 -Tags "cart OR checkout"
.\run_tests.ps1 -Suite 03_cart
.\run_tests.ps1 -Parallel 4        # pabot ile paralel
```

**Raporlar** (her koşumda yeniden üretilir, sürüm kontrolüne girmez):

| Proje | Çıktı |
|-------|-------|
| Selenium | `01-selenium-pytest/reports/report.html` + log + hata ekran görüntüleri |
| Robot | `02-robot-framework/results/report.html` + `log.html` |
| Playwright | `03-playwright-pytest/reports/report.html` + trace + video |

Tek istisna `03-playwright-pytest/reports/visual_baseline/` klasörüdür: görsel
regresyon referans görüntüleri bilerek depoya dahil edilmiştir, aksi halde
karşılaştırılacak bir referans kalmaz.

---

## Bu projenin bulduğu gerçek kusur

Playwright paketi, SauceDemo'da **gerçek bir erişilebilirlik kusuru** ortaya
çıkardı: envanter sayfasında hiçbir `heading` (h1–h6) elemanı yok — sayfa başlığı
`<span>` olarak işlenmiş. Ekran okuyucu kullanan biri sayfa yapısında gezinemez
(**WCAG 2.1 – 1.3.1**).

Bu kusur, `get_by_role()` locator'ının DOM yerine **erişilebilirlik ağacını**
sorgulaması sayesinde bulundu; CSS selector'a dayanan Selenium ve Robot
projelerinde fark edilmeden kalırdı. İlgili test, uygulamanın bilinen açık kusuru
olarak `xfail` ile işaretlenmiştir — bu yüzden tablodaki "74 geçti, 1 xfail"
sonucu bir başarısızlık değil, **kasıtlı bir bulgudur**.

---

## Test hesapları

SauceDemo bu hesapları giriş sayfasında public olarak yayınlar; gizli bir bilgi değildir.

| Kullanıcı | Davranış |
|-----------|----------|
| `standard_user` | Normal akış |
| `locked_out_user` | Giriş engellenir |
| `problem_user` | Bozuk görseller / hatalı alanlar |
| `performance_glitch_user` | Kasıtlı gecikme (bekleme stratejisi testi) |
| `error_user`, `visual_user` | Checkout ve görsel hataları |

Şifre hepsi için: `secret_sauce`

---

## Sürekli entegrasyon (CI)

Testler **canlı bir üçüncü taraf siteye** bağlandığı ve tam paket üçü birden
~16 dakika sürdüğü için CI ikiye bölünmüştür:

| Workflow | Ne zaman | Ne koşar | Süre |
|----------|----------|----------|------|
| [`ci.yml`](.github/workflows/ci.yml) | Her push / PR | Statik kontroller + üç yığının **smoke** testleri | ~5 dk |
| [`full-suite.yml`](.github/workflows/full-suite.yml) | Her gece 03:00 UTC + elle | Üç yığının **tüm** paketi | ~20 dk |

**`ci.yml` — statik kontroller** (tarayıcı açmadan, saniyeler içinde):
Python söz dizimi derlemesi, `shared/*.json` geçerlilik kontrolü, Robot
suite'lerinin `--dryrun` ile çözümlenmesi (yazım hatası / eksik keyword burada
yakalanır) ve pytest `--collect-only` ile import hatası taraması. Bunlar geçmeden
smoke işleri başlamaz.

**Smoke işleri** üç yığın için paralel koşar ve `fail-fast: false` ile
tanımlanmıştır — amaç "hangi yığın bozuldu" sorusunu tek koşumda cevaplayabilmek.
Her koşumun HTML raporu artifact olarak yüklenir.

**`full-suite.yml`** elle tetiklendiğinde tek bir yığın seçilebilir
(`all` / `selenium` / `robot` / `playwright`) ve her işin süresi GitHub iş özetine
tablo olarak yazılır.

İki ayrıntı bilinçli tercihtir:

* **`--reruns`** — testler kontrolümüzde olmayan bir siteye bağlandığı için ağ
  kaynaklı tek seferlik hatalar build'i kırmasın diye yeniden deneme açıktır.
  Gerçek bir regresyon her denemede düşeceği için maskelenmez.
* **Playwright'ta `-m "not visual"`** — görsel regresyon referansları Windows'ta
  üretildi; Linux runner'da yazı tipi render'ı farklı olduğu için bu testler
  gerçek bir regresyondan değil, **platform farkından** düşer. Görsel testler bu
  yüzden yerelde (Windows'ta) koşturulmalıdır.

---

## Raporu yeniden üretmek

```powershell
pip install python-docx
python docs\generate_report.py
```

Script, `Otomasyon_Karsilastirma_Raporu.docx` dosyasını proje kökünde yeniden
oluşturur. Rapordaki tüm sayısal değerler yukarıdaki gerçek koşum sonuçlarından
gelir.

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile yayınlanmıştır — serbestçe kullanabilir,
değiştirebilir ve dağıtabilirsiniz; tek koşul telif bildiriminin korunmasıdır.

Test edilen uygulama [SauceDemo](https://www.saucedemo.com) bu projeye ait
değildir; Sauce Labs tarafından otomasyon pratiği için public olarak sunulan bir
demo uygulamasıdır. MIT lisansı yalnızca bu depodaki test kodunu kapsar.
