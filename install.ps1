# Instalador do Ditado (Windows)
# Uso:  powershell -ExecutionPolicy Bypass -File install.ps1 [-Autostart]
param([switch]$Autostart)

$ErrorActionPreference = "Stop"
$base = $PSScriptRoot
Write-Host "== Ditado: instalador Windows ==" -ForegroundColor Cyan

# 1) Python 3.10+
$py = $null
foreach ($cand in @("python", "py")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cand; break }
}
if (-not $py) { throw "Python nao encontrado. Instale em https://python.org (marque 'Add to PATH')." }
$vOk = & $py -c "import sys; print(1 if sys.version_info >= (3,10) else 0)"
if ($vOk -ne "1") { throw "Python 3.10+ necessario." }
Write-Host "[1/6] Python OK"

# 2) venv isolado
if (-not (Test-Path "$base\.venv")) { & $py -m venv "$base\.venv" }
$venvPy = "$base\.venv\Scripts\python.exe"
Write-Host "[2/6] venv OK"

# 3) dependencias
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -r "$base\requirements.txt"
Write-Host "[3/6] dependencias OK"

# 4) GPU NVIDIA (opcional)
$gpu = $null -ne (Get-Command nvidia-smi -ErrorAction SilentlyContinue)
if ($gpu) {
    & $venvPy -m pip install --quiet -r "$base\requirements-gpu.txt"
    Write-Host "[4/6] GPU NVIDIA detectada: usando modelo large-v3-turbo (CUDA)"
} else {
    Write-Host "[4/6] sem GPU NVIDIA: usando modelo small (CPU)"
}

# 5) config + dicionario + download do modelo
if (-not (Test-Path "$base\config.json")) {
    Copy-Item "$base\config.example.json" "$base\config.json"
}
if (-not (Test-Path "$base\dicionario.txt")) {
    Copy-Item "$base\dicionario.example.txt" "$base\dicionario.txt"
}
$gpuFlag = if ($gpu) { "1" } else { "0" }
@"
import json, sys
base, gpu = sys.argv[1], sys.argv[2] == "1"
path = base + r"\config.json"
cfg = json.load(open(path, encoding="utf-8"))
if gpu:
    cfg.update(model_size="large-v3-turbo", device="cuda",
               compute_type="int8_float16", beam_size=5)
json.dump(cfg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
from faster_whisper.utils import download_model
print("baixando modelo", cfg["model_size"], "(uma vez so)...")
download_model(cfg["model_size"])
print("modelo pronto")
"@ | & $venvPy - $base $gpuFlag
Write-Host "[5/6] config + modelo OK"

# 6) launchers
$vbs = "$base\iniciar-ditado.vbs"
@"
' Inicia o Ditado em background (sem janela de console)
Set sh = CreateObject("WScript.Shell")
sh.Run """$base\.venv\Scripts\pythonw.exe"" ""$base\ditado.py""", 0, False
"@ | Out-File -FilePath $vbs -Encoding ascii
@"
@echo off
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { `$_.CommandLine -like '*ditado.py*' } | ForEach-Object { Stop-Process -Id `$_.ProcessId -Force }"
echo Ditado parado.
"@ | Out-File -FilePath "$base\parar-ditado.bat" -Encoding ascii
if ($Autostart) {
    Copy-Item $vbs "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ditado.vbs" -Force
    Write-Host "[6/6] launchers OK + autostart instalado"
} else {
    Write-Host "[6/6] launchers OK (rode de novo com -Autostart para iniciar com o Windows)"
}

Write-Host ""
Write-Host "Pronto! Inicie com: iniciar-ditado.vbs" -ForegroundColor Green
Write-Host "Segure Ctrl+Win, fale, solte. Sair: Ctrl+Alt+F12 ou parar-ditado.bat"
