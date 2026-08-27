# Testautomatisierung im Vergleich

**Dieselbe Anwendung. Dieselben Testszenarien. Drei verschiedene Automatisierungs-Stacks.**

🇹🇷 [Türkçe](README.md) · 🇬🇧 [English](README.en.md) · 🇩🇪 **Deutsch**

[![CI](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml)
[![Vollständige Suite](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.20+-43B02A?logo=selenium&logoColor=white)
![Robot Framework](https://img.shields.io/badge/Robot%20Framework-7.0+-000000?logo=robotframework&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.44+-2EAD33?logo=playwright&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)
![Lizenz](https://img.shields.io/badge/License-MIT-yellow)

Dieses Repository testet die Anwendung [SauceDemo](https://www.saucedemo.com)
durchgängig mit **drei getrennten Automatisierungs-Stacks**. Ziel ist nicht, einen
Sieger zu küren, sondern nebeneinander und mit gemessenen Daten zu zeigen, wie
sich die drei Ansätze in **Architektur, Lesbarkeit, Wartungsaufwand,
Geschwindigkeit und Funktionsumfang** in einem echten Projekt unterscheiden.

> **Hinweis zur Sprache:** Der Testcode, die Kommentare und die projektinternen
> READMEs in `01-*`, `02-*` und `03-*` sind auf Türkisch verfasst, ebenso der
> abschließende Vergleichsbericht. Diese Datei ist eine deutschsprachige
> Gesamtübersicht des Projekts.

---

## Inhaltsverzeichnis

- [Warum dieselbe Anwendung und dieselben Szenarien?](#warum-dieselbe-anwendung-und-dieselben-szenarien)
- [Aufbau des Repositorys](#aufbau-des-repositorys)
- [Gemessene Ergebnisse](#gemessene-ergebnisse)
- [Drei Projekte, drei Architekturansätze](#drei-projekte-drei-architekturansätze)
- [Warum für alle drei Python?](#warum-für-alle-drei-python)
- [Einrichtung](#einrichtung)
- [Tests ausführen](#tests-ausführen)
- [Ein echter Fehler, den dieses Projekt gefunden hat](#ein-echter-fehler-den-dieses-projekt-gefunden-hat)
- [Testkonten](#testkonten)
- [Continuous Integration (CI)](#continuous-integration-ci)
- [Den Bericht neu erzeugen](#den-bericht-neu-erzeugen)
- [Lizenz](#lizenz)

---

## Warum dieselbe Anwendung und dieselben Szenarien?

Die meisten Framework-Vergleiche vergleichen Äpfel mit Birnen: Sie betrachten
Code, der gegen unterschiedliche Websites und mit unterschiedlichen Szenarien
geschrieben wurde, und schreiben den entstandenen Unterschied dann dem Framework
zu. Hier ist **das Framework die einzige Variable** — Anwendung, Szenarien,
Prüfungen und Testdaten sind in allen drei Projekten identisch.

| # | Szenario | Selenium | Robot | Playwright |
|---|----------|:--------:|:-----:|:----------:|
| 1 | Login – gültig / ungültig / gesperrter Benutzer (datengetrieben) | ✔ | ✔ | ✔ |
| 2 | Produktliste – Anzahl, Sortierung nach Name/Preis | ✔ | ✔ | ✔ |
| 3 | Warenkorb – hinzufügen / entfernen / Zähler / Persistenz | ✔ | ✔ | ✔ |
| 4 | Checkout – Formularvalidierung, Steuer- und Summenberechnung | ✔ | ✔ | ✔ |
| 5 | Durchgängiger Kaufprozess | ✔ | ✔ | ✔ |
| 6 | Navigation / Menü / Logout / Session-Bereinigung | ✔ | ✔ | ✔ |
| 7 | Netzwerk-Mocking, Trace, Video, visuelle Regression, API-Tests | ✖ | ✖ | ✔ |

Die letzte Zeile ist Absicht: Sie zeigt die Fähigkeiten, die Playwright **nativ**
mitbringt und die den anderen beiden fehlen. Geschwindigkeitsvergleiche werden
jedoch stets über die **identischen Szenarien** geführt — diese Zusatztests
bleiben dabei ausgeschlossen.

---

## Aufbau des Repositorys

```
Automation/
├── 01-selenium-pytest/     Selenium WebDriver 4 + pytest + Page Object Model
├── 02-robot-framework/     Robot Framework 7 + SeleniumLibrary (keyword-getrieben)
├── 03-playwright-pytest/   Playwright (sync API) + pytest + Locator/POM
├── shared/                 Testdaten, die alle drei Projekte einlesen
│   ├── users.json          Benutzerkonten und ihr erwartetes Verhalten
│   └── products.json       Produktnamen, Preise, Sortiererwartungen
├── docs/
│   └── generate_report.py  Skript, das den Vergleichsbericht (.docx) erzeugt
└── Otomasyon_Karsilastirma_Raporu.docx   Abschließender Vergleichsbericht (Türkisch)
```

`shared/` ist bewusst gemeinsam: Alle drei Projekte lesen dieselben JSON-Dateien,
womit der Einwand "die Testdaten waren unterschiedlich" von vornherein entkräftet
ist. Der Selenium-Test `test_shared_data_file_is_consistent` prüft die
Konsistenz dieser Dateien.

---

## Gemessene Ergebnisse

> Die folgenden Zahlen sind keine Schätzungen — jede einzelne stammt aus Tests,
> die **tatsächlich auf derselben Maschine mit headless Chrome ausgeführt** wurden.

### Vollständige Suite

| Stack | Tests | Dauer | Pro Test | Ergebnis |
|-------|:-----:|-------|:--------:|----------|
| Selenium + pytest | 61 | 6 min 07 s (367 s) | 6,0 s | 61 bestanden |
| Robot Framework | 51 | ≈9,5 min (577 s) | ≈11,3 s | 50 bestanden, 1 im zweiten Versuch |
| Playwright + pytest | 75 | 1 min 37 s (97 s) | 1,3 s | 74 bestanden, 1 `xfail` |

### Identische Login-Szenarien (direkter Vergleich)

| Stack | Szenarien | Dauer | Relativ |
|-------|:---------:|-------|:-------:|
| Selenium + pytest | 16 | 77 s | 3,2× |
| Robot Framework | 15 | 102 s | 4,2× |
| Playwright + pytest | 15 | 24 s | 1,0× (Referenz) |

> **Zwei Anmerkungen zur Robot-Zeile.** Die Testanzahl ist 51, nicht 47: Die
> DataDriver-Suite expandiert die CSV jetzt tatsächlich und erzeugt aus einer
> einzeiligen Vorlage 5 Tests (zuvor war die CSV überhaupt nicht lesbar und die
> Suite fiel mit einem einzigen defekten Test durch). "1 im zweiten Versuch"
> bezeichnet das Szenario `performance_glitch_user`: SauceDemos bewusst
> verlangsamtes Konto fällt gegen die Live-Seite etwa in einem von drei Läufen
> durch und besteht, wenn es allein wiederholt wird. Deshalb wiederholt die CI
> nun auch Robot — genau wie Selenium und Playwright.

**Woher kommt der Unterschied?** Selenium und Robot starten für jeden Test einen
neuen Browser-Prozess; allein das kostet ~1–2 Sekunden pro Test. Playwright öffnet
stattdessen einen isolierten `BrowserContext` auf einem einzigen Browser-Prozess —
Kosten: ~20–50 Millisekunden. Hinzu kommt, dass Playwright den Browser direkt über
CDP/WebSocket steuert; das WebDriver-Protokoll und der zwischengeschaltete
`chromedriver`-Prozess entfallen.

---

## Drei Projekte, drei Architekturansätze

### `01-selenium-pytest/` — Code-zentriert, volle Kontrolle

Enthält eine handgeschriebene **Framework-Schicht** und stützt sich nicht auf eine
fertige Abstraktion. Die Schichtregel ist streng:

```
tests/  ->  pages/  ->  core/  ->  selenium
```

* Ein **Test** sieht niemals einen CSS-Selektor oder ein `WebDriverWait`.
* Ein **Page Object** schreibt niemals ein `assert` — es liefert Zustand zurück; das Prüfen ist Aufgabe des Tests.
* **Core** kennt die Anwendung nicht — es ist allgemein verwendbar.

In `core/` liegen die Driver-Factory, Wait-/Retry-Wrapper, eigene Expected
Conditions, Soft Asserts, diagnosefähige Exception-Typen und das Logging. Der
Selenium Manager (ab Selenium 4.6+ enthalten) lädt den Treiber automatisch, sodass
`chromedriver.exe` nicht separat besorgt werden muss.

### `02-robot-framework/` — Keyword-getrieben, niedrige Einstiegshürde

> Robot Framework ist keine *Alternative* zu Selenium. Unter SeleniumLibrary
> **läuft weiterhin Selenium WebDriver**. Robot ist eine **Abstraktionsschicht
> oberhalb von Selenium**.

Robot kennt keine Klassen; Kapselung geschieht **auf Dateiebene**:

| Selenium (Python) | Robot Framework |
|-------------------|-----------------|
| `class LoginPage:` | `resources/pages/login_page.resource` |
| Klassenkonstante `USERNAME_INPUT` | `${LOGIN_USERNAME_INPUT}` unter `*** Variables ***` |
| Methode `def login(self, ...)` | `Login As` unter `*** Keywords ***` |
| `conftest.py`-Fixture | `Test Setup` / `Suite Setup` |
| `@pytest.mark.parametrize` | `[Template]` oder DataDriver |
| `pytest -m smoke` | `robot --include smoke` |

Arbeiten, die echte Berechnungen oder komplexe Prüfungen erfordern, wandern in die
**Python-Keyword-Bibliothek** `libraries/SauceDemoLibrary.py` — genau um zu zeigen,
wo die natürliche Grenze von Robot beginnt.

### `03-playwright-pytest/` — Modern, schnell, breiter Funktionsumfang

`tests/ui/` enthält die **identischen** Szenarien der beiden anderen Projekte.
`tests/advanced/` zeigt, wofür es in Selenium oder Robot keine native Entsprechung gibt:

* **Netzwerk-Mocking** — Anfragen mit `page.route()` abfangen/verändern
* **Visuelle Regression** — Referenz-PNGs liegen versioniert unter `reports/visual_baseline/`
* **Geräteemulation** — mobiler Viewport / User Agent / Touch
* **API-Tests** — Prüfungen ohne UI über `APIRequestContext`
* **Trace & Video** — schrittweise Aufzeichnung eines fehlgeschlagenen Tests

Das automatische Warten macht nahezu jedes explizite Warten im Stil von
`WebDriverWait` überflüssig, und `get_by_role()`-Locators fragen den
**Accessibility-Baum** ab statt das DOM.

---

## Warum für alle drei Python?

Playwright wird meist mit TypeScript eingesetzt, dennoch sind hier alle drei
Projekte in Python geschrieben. Der Grund: den Vergleich **nicht durch
Sprachunterschiede zu verfälschen**. Wäre eines in TypeScript geschrieben, wäre ein
Teil des Sichtbaren ein "TS vs. Python"-Unterschied statt eines
Framework-Unterschieds. Der Bericht hält gesondert fest, welche zusätzlichen
Unterschiede eine TypeScript-Variante mit sich bringt.

---

## Einrichtung

**Empfohlen: eine eigene virtuelle Umgebung pro Projekt.**

```powershell
foreach ($p in "01-selenium-pytest","02-robot-framework","03-playwright-pytest") {
    python -m venv "$p\.venv"
    & "$p\.venv\Scripts\python.exe" -m pip install -r "$p\requirements.txt"
}
& "03-playwright-pytest\.venv\Scripts\python.exe" -m playwright install chromium firefox webkit
```

<details>
<summary><b>Warum getrennte Umgebungen? (lies dies, wenn du nur eine willst)</b></summary>

<br>

Das Plugin `pytest-playwright` lädt in der Umgebung, in der es installiert ist, bei
**jedem** pytest-Lauf automatisch und registriert eine eigene `--browser`-Option.
Das Selenium-Projekt definiert `--browser` ebenfalls, sodass eine gemeinsame
Umgebung Folgendes erzeugt:

```
argparse.ArgumentError: argument --browser: conflicting option string: --browser
```

Das Selenium-Projekt schaltet dies über die Zeile `-p no:playwright` in seiner
`pytest.ini` bereits ab, eine einzelne Umgebung funktioniert also:

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r 01-selenium-pytest\requirements.txt
pip install -r 02-robot-framework\requirements.txt
pip install -r 03-playwright-pytest\requirements.txt
python -m playwright install chromium firefox webkit
```

</details>

---

## Tests ausführen

Jedes Projekt bringt seinen eigenen `run_tests.ps1`-Wrapper mit:

```powershell
cd 01-selenium-pytest ; .\run_tests.ps1
cd 02-robot-framework ; .\run_tests.ps1
cd 03-playwright-pytest ; .\run_tests.ps1
```

Häufig genutzte Optionen:

```powershell
# Selenium / Playwright (pytest)
.\run_tests.ps1 -Marker smoke      # nur Smoke-Tests
.\run_tests.ps1 -Headed            # sichtbarer Browser
.\run_tests.ps1 -Parallel 4        # 4 Prozesse parallel
python -m pytest -m "cart or checkout" -v
python -m pytest tests/test_login.py::test_standard_user_can_login

# Robot Framework
.\run_tests.ps1 -Tags smoke
.\run_tests.ps1 -Tags "cart OR checkout"
.\run_tests.ps1 -Suite 03_cart
.\run_tests.ps1 -Parallel 4        # parallel über pabot
```

**Berichte** (bei jedem Lauf neu erzeugt, nicht versioniert):

| Projekt | Ausgabe |
|---------|---------|
| Selenium | `01-selenium-pytest/reports/report.html` + Logs + Fehler-Screenshots |
| Robot | `02-robot-framework/results/report.html` + `log.html` |
| Playwright | `03-playwright-pytest/reports/report.html` + Traces + Video |

Die einzige Ausnahme ist `03-playwright-pytest/reports/visual_baseline/`: Die
Referenzbilder der visuellen Regression sind bewusst eingecheckt — sonst gäbe es
nichts mehr, wogegen verglichen werden könnte.

---

## Ein echter Fehler, den dieses Projekt gefunden hat

Die Playwright-Suite hat einen **echten Barrierefreiheitsfehler** in SauceDemo
zutage gefördert: Die Inventarseite enthält überhaupt kein `heading`-Element
(h1–h6) — der Seitentitel wird als `<span>` gerendert. Wer einen Screenreader
benutzt, kann die Seitenstruktur nicht navigieren (**WCAG 2.1 – 1.3.1**).

Gefunden wurde der Fehler, weil `get_by_role()` den **Accessibility-Baum** abfragt
statt das DOM; in den Selenium- und Robot-Projekten, die auf CSS-Selektoren
beruhen, wäre er unbemerkt geblieben. Der zugehörige Test ist als `xfail` markiert,
also als bekannter offener Fehler der Anwendung — deshalb ist die Zeile
"74 bestanden, 1 xfail" kein Fehlschlag, sondern ein **bewusster Befund**.

---

## Testkonten

SauceDemo veröffentlicht diese Konten offen auf seiner Login-Seite; es sind keine
Geheimnisse.

| Benutzer | Verhalten |
|----------|-----------|
| `standard_user` | Normaler Ablauf |
| `locked_out_user` | Login wird blockiert |
| `problem_user` | Defekte Bilder / falsche Felder |
| `performance_glitch_user` | Absichtliche Verzögerung (prüft die Wartestrategie) |
| `error_user`, `visual_user` | Checkout- und Darstellungsfehler |

Passwort für alle: `secret_sauce`

---

## Continuous Integration (CI)

Da die Tests eine **live erreichbare Drittanbieter-Website** ansprechen und die
drei vollständigen Suiten zusammen rund 16 Minuten brauchen, ist die CI zweigeteilt:

| Workflow | Wann | Was ausgeführt wird | Dauer |
|----------|------|---------------------|-------|
| [`ci.yml`](.github/workflows/ci.yml) | Bei jedem Push / PR | Statische Prüfungen + die **Smoke**-Tests aller drei Stacks | ~5 min |
| [`full-suite.yml`](.github/workflows/full-suite.yml) | Nachts um 03:00 UTC + manuell | Die **vollständige** Suite aller drei Stacks | ~20 min |

**`ci.yml` — statische Prüfungen** (ohne Browser, in Sekunden erledigt):
Python-Bytecode-Kompilierung, Gültigkeit von `shared/*.json`, Auflösen der
Robot-Suiten mit `--dryrun` (Tippfehler und fehlende Keywords werden hier
gefunden) sowie ein `--collect-only`-Durchlauf von pytest für Importfehler. Die
Smoke-Jobs starten erst, wenn diese bestanden sind.

**Die Smoke-Jobs** laufen für die drei Stacks parallel mit `fail-fast: false` — es
geht darum, die Frage "welcher Stack ist kaputt" in einem einzigen Lauf zu
beantworten. Der HTML-Bericht jedes Laufs wird als Artefakt hochgeladen.

**`full-suite.yml`** akzeptiert beim manuellen Start einen einzelnen Stack
(`all` / `selenium` / `robot` / `playwright`) und schreibt die Dauer jedes Jobs als
Tabelle in die GitHub-Job-Zusammenfassung.

Zwei Details sind Absicht:

* **`--reruns`** — da die Tests von einer Website außerhalb unserer Kontrolle
  abhängen, sind Wiederholungen aktiviert, damit einmalige Netzwerkfehler den Build
  nicht zerstören. Eine echte Regression schlägt bei jedem Versuch fehl und wird
  daher nicht verdeckt.
* **`-m "not visual"` für Playwright** — die Referenzbilder der visuellen Regression
  wurden unter Windows erzeugt; auf dem Linux-Runner unterscheidet sich das
  Font-Rendering, sodass diese Tests wegen eines **Plattformunterschieds** und nicht
  wegen einer echten Regression fehlschlagen würden. Visuelle Tests sollten deshalb
  lokal unter Windows laufen.

---

## Den Bericht neu erzeugen

```powershell
pip install python-docx
python docs\generate_report.py
```

Das Skript baut `Otomasyon_Karsilastirma_Raporu.docx` im Projektstamm neu auf. Jede
Zahl im Bericht stammt aus den oben gezeigten echten Laufergebnissen.

---

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE) — Nutzung, Änderung und Weitergabe
sind frei, einzige Bedingung ist die Beibehaltung des Copyright-Hinweises.

Die getestete Anwendung [SauceDemo](https://www.saucedemo.com) ist nicht Teil dieses
Projekts; sie ist eine von Sauce Labs öffentlich bereitgestellte Demo-Anwendung zum
Üben von Automatisierung. Die MIT-Lizenz deckt ausschließlich den Testcode in
diesem Repository ab.
