# Reconstruye el instalador de PokeFollower Desktop desde cero.
# Uso: powershell -ExecutionPolicy Bypass -File tools\build.ps1
#
# Requiere: venv activado con requirements-dev.txt instalado, e Inno Setup instalado
# (se busca en varias rutas conocidas - ver ISCC_CANDIDATES abajo, porque no siempre
# se instala en la ruta estandar de Inno Setup 6).

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "== 1/3: Generando icono (.ico) ==" -ForegroundColor Cyan
python tools\make_icon.py
if ($LASTEXITCODE -ne 0) { throw "make_icon.py fallo" }

Write-Host "== 2/3: Build de PyInstaller (onedir) ==" -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
python -m PyInstaller PokeFollower.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller fallo" }

Write-Host "== Verificando el bundle con --self-check ==" -ForegroundColor Cyan
& "dist\PokeFollower\PokeFollower.exe" --self-check
if ($LASTEXITCODE -ne 0) { throw "self-check fallo en el bundle recien construido, no se genera el instalador" }

Write-Host "== 3/3: Compilando el instalador con Inno Setup ==" -ForegroundColor Cyan
$ISCC_CANDIDATES = @(
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $ISCC_CANDIDATES | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    $found = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($found) { $iscc = $found.Source }
}
if (-not $iscc) {
    throw "No se encontro ISCC.exe. Instala Inno Setup desde https://jrsoftware.org/isdl.php"
}
Write-Host "Usando: $iscc"
& $iscc "installer\PokeFollower.iss"
if ($LASTEXITCODE -ne 0) { throw "ISCC (Inno Setup) fallo" }

Write-Host ""
Write-Host "Listo: installer\Output\PokeFollower-Setup-1.0.0.exe" -ForegroundColor Green
