# Jalankan konsol di Windows. Aman diulang: pakai venv kalau ada, buat kalau belum.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")     # akar project, tempat app/ dan requirements.txt

# Cari Python 3.12+ : py launcher lebih dulu, lalu python di PATH.
$pyExe = $null
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.13 --version *> $null
    if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-3.13") }
    else {
        & py -3 --version *> $null
        if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-3") }
    }
}
if (-not $pyExe -and (Get-Command python -ErrorAction SilentlyContinue)) { $pyExe = "python" }
if (-not $pyExe) {
    Write-Error "Python 3.12+ tidak ditemukan. Pasang dari python.org (centang 'Add python.exe to PATH')."
    exit 1
}

$venvPy = ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    & $pyExe @pyArgs -m venv .venv
    & $venvPy -m pip install --upgrade pip | Out-Null
    # Lock ber-hash di requirements.lock dibuat di macOS; di sini pakai daftar yang
    # sama tanpa hash supaya wheel Windows bisa dipakai.
    & $venvPy -m pip install -r requirements.txt
}

if (-not $env:GAI_BIND_PORT) {
    $env:GAI_BIND_PORT = if ($env:PORT) { $env:PORT } else { "8765" }
}

$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ }
if (-not $chrome) {
    Write-Warning "Google Chrome tidak ditemukan — login akan gagal. Pasang Chrome dulu."
}

& $venvPy -m uvicorn app.main:app --host 127.0.0.1 --port $env:GAI_BIND_PORT --log-level warning
