#!/usr/bin/env bash
# Instalador do Ditado (macOS e Linux)
# Uso:  bash install.sh [--autostart]
set -euo pipefail

BASE="$(cd "$(dirname "$0")" && pwd)"
OS="$(uname -s)"
AUTOSTART=0
[ "${1:-}" = "--autostart" ] && AUTOSTART=1

echo "== Ditado: instalador ($OS) =="

# 1) Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 nao encontrado."; exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
    || { echo "ERRO: Python 3.10+ necessario."; exit 1; }
echo "[1/6] Python OK"

# tkinter costuma vir separado no Linux
if ! python3 -c 'import tkinter' 2>/dev/null; then
    echo "ERRO: tkinter ausente. Debian/Ubuntu: sudo apt install python3-tk"
    echo "      Fedora: sudo dnf install python3-tkinter"
    exit 1
fi

# 2) venv isolado
[ -d "$BASE/.venv" ] || python3 -m venv "$BASE/.venv"
VENV_PY="$BASE/.venv/bin/python"
echo "[2/6] venv OK"

# 3) dependencias
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r "$BASE/requirements.txt"
echo "[3/6] dependencias OK"

# 4) GPU NVIDIA (opcional, so Linux)
GPU=0
if [ "$OS" = "Linux" ] && command -v nvidia-smi >/dev/null 2>&1; then
    GPU=1
    "$VENV_PY" -m pip install --quiet -r "$BASE/requirements-gpu.txt"
    echo "[4/6] GPU NVIDIA detectada: usando modelo large-v3-turbo (CUDA)"
else
    echo "[4/6] sem GPU NVIDIA: usando modelo small (CPU)"
fi

# 5) config + dicionario + download do modelo (fica em ~/.cache/huggingface)
[ -f "$BASE/config.json" ] || cp "$BASE/config.example.json" "$BASE/config.json"
[ -f "$BASE/dicionario.txt" ] || cp "$BASE/dicionario.example.txt" "$BASE/dicionario.txt"
"$VENV_PY" - "$BASE" "$GPU" <<'PY'
import json, sys
base, gpu = sys.argv[1], sys.argv[2] == "1"
path = base + "/config.json"
cfg = json.load(open(path, encoding="utf-8"))
if gpu:
    cfg.update(model_size="large-v3-turbo", device="cuda",
               compute_type="int8_float16", beam_size=5)
json.dump(cfg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
from faster_whisper.utils import download_model
print("baixando modelo", cfg["model_size"], "(uma vez so)...")
download_model(cfg["model_size"])
print("modelo pronto")
PY
echo "[5/6] config + modelo OK"

# 6) launchers
cat > "$BASE/ditado-start.sh" <<EOF
#!/usr/bin/env bash
# GPU Linux: ctranslate2 acha cublas/cudnn dos wheels pip via LD_LIBRARY_PATH
NV_LIBS="\$(ls -d "$BASE"/.venv/lib/python*/site-packages/nvidia/*/lib 2>/dev/null | tr '\n' ':')"
export LD_LIBRARY_PATH="\${NV_LIBS}\${LD_LIBRARY_PATH:-}"
nohup "$BASE/.venv/bin/python" "$BASE/ditado.py" >/dev/null 2>&1 &
echo "Ditado iniciado."
EOF
cat > "$BASE/ditado-stop.sh" <<EOF
#!/usr/bin/env bash
pkill -f "$BASE/ditado.py" && echo "Ditado parado." || echo "Ditado nao estava rodando."
EOF
chmod +x "$BASE/ditado-start.sh" "$BASE/ditado-stop.sh"

if [ "$AUTOSTART" = 1 ]; then
    if [ "$OS" = "Darwin" ]; then
        PLIST="$HOME/Library/LaunchAgents/com.ditado.dictation.plist"
        mkdir -p "$HOME/Library/LaunchAgents"
        cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.ditado.dictation</string>
  <key>ProgramArguments</key><array>
    <string>$BASE/ditado-start.sh</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
        echo "[6/6] launchers OK + autostart (launchd) instalado"
    else
        mkdir -p "$HOME/.config/autostart"
        cat > "$HOME/.config/autostart/ditado.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Ditado
Exec=$BASE/ditado-start.sh
X-GNOME-Autostart-enabled=true
EOF
        echo "[6/6] launchers OK + autostart instalado"
    fi
else
    echo "[6/6] launchers OK (rode com --autostart para iniciar com o sistema)"
fi

echo ""
echo "Pronto! Inicie com: ./ditado-start.sh"
if [ "$OS" = "Darwin" ]; then
    echo "Segure Ctrl+Cmd, fale, solte. Sair: Ctrl+Alt+F12 ou ./ditado-stop.sh"
    echo ""
    echo "IMPORTANTE (macOS): em Ajustes > Privacidade e Seguranca, conceda ao"
    echo "Terminal/Python: Microfone, Acessibilidade e Monitoramento de Entrada."
else
    echo "Segure Ctrl+Super (tecla Windows), fale, solte. Sair: Ctrl+Alt+F12 ou ./ditado-stop.sh"
    echo ""
    echo "NOTA (Linux): requer X11 (no Wayland puro o atalho global nao funciona)."
    echo "pyperclip precisa de xclip: sudo apt install xclip"
fi
