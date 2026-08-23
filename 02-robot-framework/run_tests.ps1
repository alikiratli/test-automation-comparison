# ---------------------------------------------------------------------------
# Robot Framework test kosum betigi
#
#   .\run_tests.ps1                     -> tum testler
#   .\run_tests.ps1 -Tags smoke         -> yalnizca smoke
#   .\run_tests.ps1 -Tags "cart OR checkout"
#   .\run_tests.ps1 -Browser firefox
#   .\run_tests.ps1 -Headed
#   .\run_tests.ps1 -Parallel 4         -> pabot ile paralel
#   .\run_tests.ps1 -Suite 03_cart
# ---------------------------------------------------------------------------
param(
    [string]$Tags     = "",
    [string]$Browser  = "chrome",
    [string]$Env      = "prod",
    [string]$Suite    = "",
    [switch]$Headed,
    [int]$Parallel    = 0
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$headless = if ($Headed) { "false" } else { "true" }
$outputDir = Join-Path $PSScriptRoot "results"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# --variablefile <dosya>:<arg1>:<arg2> ... -> get_variables(env, browser, headless)
$variableFile = "variables/environment.py:${Env}:${Browser}:${headless}"

$robotArgs = @(
    "--outputdir", $outputDir,
    "--variablefile", $variableFile,
    "--pythonpath", ".",
    "--loglevel", "INFO",
    "--reporttitle", "SauceDemo - Robot Framework Raporu",
    "--logtitle",    "SauceDemo - Detayli Kosum Logu",
    "--metadata",    "Calistiran:$env:USERNAME"
)

if ($Tags)  { $robotArgs += "--include"; $robotArgs += $Tags }
if ($Suite) { $robotArgs += "--suite";   $robotArgs += $Suite }

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ROBOT FRAMEWORK - SauceDemo test paketi"              -ForegroundColor Cyan
Write-Host " Ortam    : $Env"                                      -ForegroundColor Cyan
Write-Host " Tarayici : $Browser (headless=$headless)"             -ForegroundColor Cyan
Write-Host " Etiket   : $(if ($Tags) { $Tags } else { 'tumu' })"   -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

if ($Parallel -gt 0) {
    # pabot: suite'leri N process arasinda dagitir
    python -m pabot.pabot --processes $Parallel @robotArgs tests/
} else {
    python -m robot @robotArgs tests/
}
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "TUM TESTLER GECTI" -ForegroundColor Green
} else {
    Write-Host "$exitCode test basarisiz" -ForegroundColor Red
}
Write-Host "Rapor : $outputDir\report.html" -ForegroundColor Yellow
Write-Host "Log   : $outputDir\log.html"    -ForegroundColor Yellow

exit $exitCode
