# ---------------------------------------------------------------------------
# Playwright test kosum betigi
#
#   .\run_tests.ps1                     -> tum testler (chromium, headless)
#   .\run_tests.ps1 -Marker smoke       -> yalnizca smoke
#   .\run_tests.ps1 -Browser firefox    -> chromium | firefox | webkit
#   .\run_tests.ps1 -AllBrowsers        -> uc tarayicida birden
#   .\run_tests.ps1 -Headed             -> tarayici gorunur
#   .\run_tests.ps1 -Parallel 4         -> 4 process paralel
#   .\run_tests.ps1 -Debug              -> yavaslatilmis + gorunur + inspector
# ---------------------------------------------------------------------------
param(
    [string]$Marker   = "",
    [string]$Browser  = "chromium",
    [switch]$AllBrowsers,
    [switch]$Headed,
    [switch]$Debug,
    [int]$Parallel    = 0
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$pytestArgs = @("-v")

if ($AllBrowsers) {
    $pytestArgs += "--browser=chromium"
    $pytestArgs += "--browser=firefox"
    $pytestArgs += "--browser=webkit"
} else {
    $pytestArgs += "--browser=$Browser"
}

if ($Marker)          { $pytestArgs += "-m"; $pytestArgs += $Marker }
if ($Headed -or $Debug) { $pytestArgs += "--headed" }
if ($Debug) {
    $pytestArgs += "--slowmo"; $pytestArgs += "500"
    $env:PWDEBUG = "1"
}
if ($Parallel -gt 0)  { $pytestArgs += "-n"; $pytestArgs += "$Parallel" }

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " PLAYWRIGHT + PYTEST - SauceDemo test paketi"          -ForegroundColor Cyan
Write-Host " Tarayici : $(if ($AllBrowsers) { 'chromium+firefox+webkit' } else { $Browser })" -ForegroundColor Cyan
Write-Host " Marker   : $(if ($Marker) { $Marker } else { 'tumu' })" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

python -m pytest @pytestArgs
$exitCode = $LASTEXITCODE

if ($Debug) { Remove-Item Env:\PWDEBUG -ErrorAction SilentlyContinue }

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "TUM TESTLER GECTI" -ForegroundColor Green
} else {
    Write-Host "BASARISIZ TESTLER VAR (cikis kodu: $exitCode)" -ForegroundColor Red
    Write-Host "Trace goruntulemek icin:" -ForegroundColor Yellow
    Write-Host "  python -m playwright show-trace reports\artifacts\<test-adi>\trace.zip" -ForegroundColor Yellow
}
Write-Host "HTML rapor: $PSScriptRoot\reports\report.html" -ForegroundColor Yellow

exit $exitCode
