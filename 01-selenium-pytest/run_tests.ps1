# ---------------------------------------------------------------------------
# Selenium test kosum betigi
#
#   .\run_tests.ps1                       -> tum testler (headless chrome)
#   .\run_tests.ps1 -Marker smoke         -> yalnizca smoke paketi
#   .\run_tests.ps1 -Browser firefox      -> farkli tarayici
#   .\run_tests.ps1 -Headed               -> tarayici gorunur
#   .\run_tests.ps1 -Parallel 4           -> 4 process ile paralel
# ---------------------------------------------------------------------------
param(
    [string]$Marker   = "",
    [string]$Browser  = "chrome",
    [switch]$Headed,
    [int]$Parallel    = 0,
    [int]$Reruns      = 0
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$pytestArgs = @("-v", "--browser=$Browser")

if ($Marker)   { $pytestArgs += "-m"; $pytestArgs += $Marker }
if ($Headed)   { $pytestArgs += "--headed" }
if ($Parallel -gt 0) { $pytestArgs += "-n"; $pytestArgs += "$Parallel" }
if ($Reruns   -gt 0) { $pytestArgs += "--reruns"; $pytestArgs += "$Reruns" }

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " SELENIUM + PYTEST - SauceDemo test paketi"            -ForegroundColor Cyan
Write-Host " Tarayici : $Browser"                                  -ForegroundColor Cyan
Write-Host " Marker   : $(if ($Marker) { $Marker } else { 'tumu' })" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

python -m pytest @pytestArgs
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "TUM TESTLER GECTI" -ForegroundColor Green
} else {
    Write-Host "BASARISIZ TESTLER VAR (cikis kodu: $exitCode)" -ForegroundColor Red
}
Write-Host "HTML rapor: $PSScriptRoot\reports\report.html" -ForegroundColor Yellow

exit $exitCode
