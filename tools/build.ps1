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
# Instaladores viejos fuera: la RC debe salir de un estado limpio y sin .exe de versiones
# anteriores en Output/ (todo Output/ esta en .gitignore).
if (Test-Path "installer\Output") { Remove-Item -Recurse -Force "installer\Output" }
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

# Version: unica fuente en version.py. El .iss debe coincidir con ella.
$ver = (& python -c "import version; print(version.__version__)").Trim()
if ($LASTEXITCODE -ne 0) { throw "no se pudo leer version.py" }
$issVer = (Select-String -Path "installer\PokeFollower.iss" -Pattern '^#define MyAppVersion "(.+)"').Matches[0].Groups[1].Value
if ($ver -ne $issVer) {
    throw "Descuadre de version: version.py='$ver' pero PokeFollower.iss='$issVer'. Sincronizalos."
}

$installer = "installer\Output\PokeFollower-Setup-$ver.exe"
if (-not (Test-Path $installer)) { throw "no se genero el instalador esperado: $installer" }

# SHA-256 junto al instalador (formato 'hash  nombre', como sha256sum).
$hash = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLower()
$sha = "installer\Output\SHA256SUMS.txt"
"$hash  PokeFollower-Setup-$ver.exe" | Out-File -FilePath $sha -Encoding ascii
$sizeMB = [math]::Round((Get-Item $installer).Length / 1MB, 1)

Write-Host ""
Write-Host "Listo: $installer  ($sizeMB MB)" -ForegroundColor Green
Write-Host "SHA-256: $hash" -ForegroundColor Green
Write-Host "         escrito en $sha" -ForegroundColor Green
