# Test Automation Comparison Project

**Same application. Same test scenarios. Three different automation stacks.**

🇹🇷 [Türkçe](README.md) · 🇬🇧 **English** · 🇩🇪 [Deutsch](README.de.md)

[![CI](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/ci.yml)
[![Full suite](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml/badge.svg)](https://github.com/alikiratli/test-automation-comparison/actions/workflows/full-suite.yml)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.20+-43B02A?logo=selenium&logoColor=white)
![Robot Framework](https://img.shields.io/badge/Robot%20Framework-7.0+-000000?logo=robotframework&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.44+-2EAD33?logo=playwright&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

This repository tests the [SauceDemo](https://www.saucedemo.com) application
end to end with **three separate automation stacks**. The goal is not to crown a
winner, but to show — side by side and backed by measured data — how the three
approaches differ in **architecture, readability, maintenance cost, speed and
capability** on a real project.

> **Note on language:** the test code, comments and per-project READMEs inside
> `01-*`, `02-*` and `03-*` are written in Turkish, as is the final comparison
> report. This file is an English overview of the project as a whole.

---

## Table of contents

- [Why the same app and the same scenarios?](#why-the-same-app-and-the-same-scenarios)
- [Repository layout](#repository-layout)
- [Measured results](#measured-results)
- [Three projects, three architectural approaches](#three-projects-three-architectural-approaches)
- [Why Python for all three?](#why-python-for-all-three)
- [Setup](#setup)
- [Running the tests](#running-the-tests)
- [A real defect this project found](#a-real-defect-this-project-found)
- [Test accounts](#test-accounts)
- [Continuous integration (CI)](#continuous-integration-ci)
- [Regenerating the report](#regenerating-the-report)
- [License](#license)

---

## Why the same app and the same scenarios?

Most framework comparisons compare apples to oranges: they look at code written
against different sites, with different scenarios, and then attribute the
resulting difference to the framework. Here **the framework is the only
variable** — the application, the scenarios, the assertions and the test data are
identical across all three projects.

| # | Scenario | Selenium | Robot | Playwright |
|---|----------|:--------:|:-----:|:----------:|
| 1 | Login – valid / invalid / locked-out user (data-driven) | ✔ | ✔ | ✔ |
| 2 | Product list – count, name/price sorting assertions | ✔ | ✔ | ✔ |
| 3 | Cart – add / remove / badge counter / persistence | ✔ | ✔ | ✔ |
| 4 | Checkout – form validation, tax & total arithmetic | ✔ | ✔ | ✔ |
| 5 | End-to-end purchase flow | ✔ | ✔ | ✔ |
| 6 | Navigation / menu / logout / session cleanup | ✔ | ✔ | ✔ |
| 7 | Network mocking, trace, video, visual regression, API testing | ✖ | ✖ | ✔ |

The last row is deliberate: it exists to demonstrate the capabilities Playwright
has **natively** and the other two do not. Speed comparisons, however, are always
made on the **identical scenarios** — these extra tests are excluded from them.

---

## Repository layout

```
Automation/
├── 01-selenium-pytest/     Selenium WebDriver 4 + pytest + Page Object Model
├── 02-robot-framework/     Robot Framework 7 + SeleniumLibrary (keyword-driven)
├── 03-playwright-pytest/   Playwright (sync API) + pytest + Locator/POM
├── shared/                 Test data read by all three projects
│   ├── users.json          User accounts and their expected behaviour
│   └── products.json       Product names, prices, sorting expectations
├── docs/
│   └── generate_report.py  Script that generates the comparison report (.docx)
└── Otomasyon_Karsilastirma_Raporu.docx   Final comparison report (Turkish)
```

`shared/` is deliberately common: all three projects read the same JSON files, so
the "the test data was different" objection is closed up front. The Selenium test
`test_shared_data_file_is_consistent` verifies the consistency of these files.

---

## Measured results

> The numbers below are not estimates — every one of them comes from tests that
> were **actually executed on the same machine with headless Chrome**.

### Full suite

| Stack | Tests | Duration | Per test | Result |
|-------|:-----:|----------|:--------:|--------|
| Selenium + pytest | 61 | 6 min 07 s (367 s) | 6.0 s | 61 passed |
| Robot Framework | 51 | ≈9.5 min (577 s) | ≈11.3 s | 50 passed, 1 on retry |
| Playwright + pytest | 75 | 1 min 37 s (97 s) | 1.3 s | 74 passed, 1 `xfail` |

### Identical login scenarios (like-for-like)

| Stack | Scenarios | Duration | Relative |
|-------|:---------:|----------|:--------:|
| Selenium + pytest | 16 | 77 s | 3.2× |
| Robot Framework | 15 | 102 s | 4.2× |
| Playwright + pytest | 15 | 24 s | 1.0× (baseline) |

> **Two notes on the Robot row.** The test count is 51, not 47: the DataDriver
> suite now really does expand the CSV and generates 5 tests from a one-line
> template (previously the CSV could not be read at all and the suite failed with
> a single broken test). "1 on retry" is the `performance_glitch_user` scenario:
> SauceDemo's deliberately slowed-down account fails roughly 1 run in 3 against
> the live site and passes when retried on its own. That is why CI now reruns
> Robot too, just as it does Selenium and Playwright.

**Where does the difference come from?** Selenium and Robot start a new browser
process for every test, which alone costs ~1–2 seconds per test. Playwright
instead opens an isolated `BrowserContext` on a single browser process — that
costs ~20–50 milliseconds. On top of that, Playwright drives the browser directly
over CDP/WebSocket; the WebDriver protocol and the intermediate `chromedriver`
process are out of the picture.

---

## Three projects, three architectural approaches

### `01-selenium-pytest/` — Code-centric, full control

Contains a hand-written **framework layer**; it does not lean on a ready-made
abstraction. The layering rule is strict:

```
tests/  ->  pages/  ->  core/  ->  selenium
```

* A **test** never sees a CSS selector or a `WebDriverWait`.
* A **page object** never writes an `assert` — it returns state; asserting is the test's job.
* **Core** never knows about the application — it is general purpose.

`core/` holds the driver factory, wait/retry wrappers, custom expected
conditions, soft asserts, diagnosable exception types and logging. Selenium
Manager (shipped with Selenium 4.6+) downloads the driver automatically, so there
is no need to fetch `chromedriver.exe` separately.

### `02-robot-framework/` — Keyword-driven, low barrier to entry

> Robot Framework is not an *alternative* to Selenium. Underneath SeleniumLibrary,
> **Selenium WebDriver is still what runs**. Robot is an **abstraction layer built
> on top of Selenium**.

Robot has no classes; encapsulation happens **at the file level**:

| Selenium (Python) | Robot Framework |
|-------------------|-----------------|
| `class LoginPage:` | `resources/pages/login_page.resource` |
| Class constant `USERNAME_INPUT` | `${LOGIN_USERNAME_INPUT}` under `*** Variables ***` |
| Method `def login(self, ...)` | `Login As` under `*** Keywords ***` |
| `conftest.py` fixture | `Test Setup` / `Suite Setup` |
| `@pytest.mark.parametrize` | `[Template]` or DataDriver |
| `pytest -m smoke` | `robot --include smoke` |

Work that needs real computation or complex assertions is pushed into the
**Python keyword library** at `libraries/SauceDemoLibrary.py` — precisely to show
where Robot's natural limit begins.

### `03-playwright-pytest/` — Modern, fast, broad capabilities

`tests/ui/` contains the **identical** scenarios of the other two projects.
`tests/advanced/` demonstrates what has no native equivalent in Selenium or Robot:

* **Network mocking** — intercepting/modifying requests with `page.route()`
* **Visual regression** — baseline PNGs are version-controlled under `reports/visual_baseline/`
* **Device emulation** — mobile viewport / user agent / touch
* **API testing** — assertions without a UI via `APIRequestContext`
* **Trace & video** — step-by-step recording of a failing test

Auto-waiting removes almost every explicit `WebDriverWait`-style wait, and
`get_by_role()` locators query the **accessibility tree** rather than the DOM.

---

## Why Python for all three?

Playwright is most commonly used with TypeScript, yet all three projects here are
written in Python. The reason: keeping the comparison **uncontaminated by
language differences**. Had one been written in TypeScript, part of what you see
would be a "TS vs Python" difference rather than a framework difference. The
report separately notes the additional differences a TypeScript variant brings.

---

## Setup

**Recommended: a separate virtual environment per project.**

```powershell
foreach ($p in "01-selenium-pytest","02-robot-framework","03-playwright-pytest") {
    python -m venv "$p\.venv"
    & "$p\.venv\Scripts\python.exe" -m pip install -r "$p\requirements.txt"
}
& "03-playwright-pytest\.venv\Scripts\python.exe" -m playwright install chromium firefox webkit
```

<details>
<summary><b>Why separate environments? (read this if you want a single one)</b></summary>

<br>

The `pytest-playwright` plugin loads automatically on **every** pytest run in the
environment it is installed into, and registers its own `--browser` option. The
Selenium project also defines `--browser`, so a shared environment produces:

```
argparse.ArgumentError: argument --browser: conflicting option string: --browser
```

The Selenium project already disables this via the `-p no:playwright` line in its
`pytest.ini`, so a single environment does work:

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r 01-selenium-pytest\requirements.txt
pip install -r 02-robot-framework\requirements.txt
pip install -r 03-playwright-pytest\requirements.txt
python -m playwright install chromium firefox webkit
```

</details>

---

## Running the tests

Each project ships its own `run_tests.ps1` wrapper:

```powershell
cd 01-selenium-pytest ; .\run_tests.ps1
cd 02-robot-framework ; .\run_tests.ps1
cd 03-playwright-pytest ; .\run_tests.ps1
```

Commonly used options:

```powershell
# Selenium / Playwright (pytest)
.\run_tests.ps1 -Marker smoke      # smoke tests only
.\run_tests.ps1 -Headed            # visible browser
.\run_tests.ps1 -Parallel 4        # 4 processes in parallel
python -m pytest -m "cart or checkout" -v
python -m pytest tests/test_login.py::test_standard_user_can_login

# Robot Framework
.\run_tests.ps1 -Tags smoke
.\run_tests.ps1 -Tags "cart OR checkout"
.\run_tests.ps1 -Suite 03_cart
.\run_tests.ps1 -Parallel 4        # in parallel via pabot
```

**Reports** (regenerated on every run, not version-controlled):

| Project | Output |
|---------|--------|
| Selenium | `01-selenium-pytest/reports/report.html` + logs + failure screenshots |
| Robot | `02-robot-framework/results/report.html` + `log.html` |
| Playwright | `03-playwright-pytest/reports/report.html` + traces + video |

The single exception is `03-playwright-pytest/reports/visual_baseline/`: the
visual regression baseline images are committed on purpose — otherwise there
would be nothing left to compare against.

---

## A real defect this project found

The Playwright suite surfaced a **genuine accessibility defect** in SauceDemo: the
inventory page contains no `heading` element (h1–h6) at all — the page title is
rendered as a `<span>`. Anyone using a screen reader cannot navigate the page
structure (**WCAG 2.1 – 1.3.1**).

The defect was found because `get_by_role()` queries the **accessibility tree**
instead of the DOM; it would have gone unnoticed in the Selenium and Robot
projects, which rely on CSS selectors. The corresponding test is marked `xfail` as
a known open defect of the application — which is why the "74 passed, 1 xfail"
row is not a failure but a **deliberate finding**.

---

## Test accounts

SauceDemo publishes these accounts publicly on its login page; they are not secrets.

| User | Behaviour |
|------|-----------|
| `standard_user` | Normal flow |
| `locked_out_user` | Login is blocked |
| `problem_user` | Broken images / wrong fields |
| `performance_glitch_user` | Deliberate delay (tests the waiting strategy) |
| `error_user`, `visual_user` | Checkout and visual failures |

Password for all of them: `secret_sauce`

---

## Continuous integration (CI)

Because the tests hit a **live third-party site** and the three full suites take
~16 minutes combined, CI is split in two:

| Workflow | When | What it runs | Duration |
|----------|------|--------------|----------|
| [`ci.yml`](.github/workflows/ci.yml) | Every push / PR | Static checks + the **smoke** tests of all three stacks | ~5 min |
| [`full-suite.yml`](.github/workflows/full-suite.yml) | Nightly at 03:00 UTC + manual | The **full** suite of all three stacks | ~20 min |

**`ci.yml` — static checks** (no browser, done in seconds): Python bytecode
compilation, `shared/*.json` validity, resolving the Robot suites with `--dryrun`
(typos and missing keywords are caught here) and a pytest `--collect-only` sweep
for import errors. The smoke jobs do not start until these pass.

**The smoke jobs** run in parallel for the three stacks with `fail-fast: false` —
the point is to answer "which stack broke" in a single run. Each run's HTML report
is uploaded as an artifact.

**`full-suite.yml`** accepts a single stack when triggered manually
(`all` / `selenium` / `robot` / `playwright`), and writes each job's duration to
the GitHub job summary as a table.

Two details are deliberate:

* **`--reruns`** — since the tests depend on a site outside our control, retries
  are enabled so that one-off network failures do not break the build. A genuine
  regression fails on every attempt and is therefore not masked.
* **`-m "not visual"` for Playwright** — the visual regression baselines were
  generated on Windows; font rendering differs on the Linux runner, so those tests
  would fail because of a **platform difference**, not a real regression. Visual
  tests should therefore be run locally on Windows.

---

## Regenerating the report

```powershell
pip install python-docx
python docs\generate_report.py
```

The script rebuilds `Otomasyon_Karsilastirma_Raporu.docx` at the project root. Every
figure in the report comes from the real run results shown above.

---

## License

Released under the [MIT License](LICENSE) — you are free to use, modify and
distribute it, the only condition being that the copyright notice is preserved.

The application under test, [SauceDemo](https://www.saucedemo.com), is not part of
this project; it is a demo application published publicly by Sauce Labs for
automation practice. The MIT license covers only the test code in this repository.
