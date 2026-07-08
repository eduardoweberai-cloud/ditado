# Ditado

English · **[Português](README.pt-BR.md)**

**100% local, free voice dictation**, in the spirit of Wispr Flow, for **Windows, macOS, and Linux**.

Hold **Ctrl + system key** (Win on Windows, Cmd on Mac, Super on Linux), speak, release: the text appears wherever your cursor is, in any app. A discreet pill at the bottom of the screen shows your voice as a live waveform while recording.

- **Truly offline:** audio never leaves your machine. No account, no subscription, no telemetry.
- **Top accuracy:** Whisper `large-v3-turbo` on NVIDIA GPU (auto-detected) or `small` on CPU.
- **Personal dictionary:** teach it your jargon, names, and brands (like Wispr's dictionary).
- **Configurable hotkey:** default is Ctrl+Win/Cmd/Super, changeable in `config.json`.
- **Lightweight:** a resident process at low priority; it won't fight your apps for CPU.

> The UI messages and the bundled example dictionary are in Brazilian Portuguese, but Ditado works in **any language Whisper supports** — just set `language` in `config.json` (`en`, `es`, `fr`, `null` for auto-detect, etc.).

## Installation

Prerequisite: [Python 3.10+](https://python.org) (on Windows, tick "Add to PATH" during setup).

The installer creates an isolated environment (`.venv`), installs dependencies, detects an NVIDIA GPU, **downloads the speech model** (once, ~500MB CPU or ~1.6GB GPU, from Hugging Face), and generates start/stop scripts. Nothing is installed outside the project folder except the model (Hugging Face's default cache).

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Autostart
```

Then double-click `iniciar-ditado.vbs`. `-Autostart` makes it launch with Windows (optional).

### macOS

```bash
bash install.sh --autostart
./ditado-start.sh
```

On first run macOS will ask for permissions. Grant Terminal (or Python), under **Settings → Privacy & Security**: **Microphone**, **Accessibility**, and **Input Monitoring** (needed for the global hotkey and to paste text). No CUDA on Mac: it runs on CPU.

### Linux

```bash
bash install.sh --autostart
./ditado-start.sh
```

Requirements: an **X11** session (on pure Wayland, global hotkeys are blocked by the compositor), plus `python3-tk` and `xclip` (`sudo apt install python3-tk xclip`). With an NVIDIA GPU + driver, the installer configures CUDA automatically.

## Usage

1. Place your cursor where you want the text (chat, editor, browser, any field).
2. **Hold** the hotkey (default `Ctrl + Win/Cmd/Super`) and speak: the pill shows your voice live.
3. **Release**: the wave turns amber while transcribing, then the text is pasted at the cursor (green flash).

Extras:

- Hotkey + any other key **cancels** the recording, so your system shortcuts (e.g. switching virtual desktops) keep working.
- Quit the app: `Ctrl+Alt+F12`, or `parar-ditado.bat` (Windows) / `./ditado-stop.sh` (Mac/Linux).
- Plugged in a headset? The next recording uses the new system default input automatically.

## Changing the hotkey

Edit `hotkey` in `config.json` and restart Ditado. Combine `ctrl`, `alt`, `shift`, and `sys` (the system key: Win/Cmd/Super) with `+`:

```json
"hotkey": "ctrl+shift"
```

Examples: `ctrl+sys` (default), `ctrl+shift`, `alt+shift`, `ctrl+alt`. Avoid exactly `ctrl+alt`, which collides with the quit shortcut (`Ctrl+Alt+F12`).

## Personal dictionary (`dicionario.txt`)

One term per line (jargon, proper nouns, brands). Whisper favors these terms when decoding. A word coming out wrong every time? Add it here and restart Ditado.

```
# examples
deploy
pull request
Your Company Name
```

## Configuration (`config.json`)

Created by the installer from `config.example.json`. Edit and restart Ditado.

| Key | Default | Notes |
|---|---|---|
| `model_size` | `small` (CPU) / `large-v3-turbo` (GPU) | Any faster-whisper model |
| `device` | `cpu` / `cuda` | Set by the installer; on GPU failure it falls back to CPU by itself |
| `compute_type` | `int8` (CPU) / `int8_float16` (GPU) | |
| `language` | `pt` | Set your language (`en`, `es`...) or `null` for auto-detect |
| `beam_size` | `1` (CPU) / `5` (GPU) | Higher = more accurate and slower |
| `hotkey` | `ctrl+sys` | Dictation hotkey (hold). Combine `ctrl`, `alt`, `shift`, `sys` with `+` |
| `insert_mode` | `paste` | `paste` (clipboard + Ctrl/Cmd+V) or `type` (simulated typing) |
| `restore_clipboard` | `true` | Restores the previous clipboard after pasting |
| `trailing_space` | `true` | Trailing space, to chain dictations |
| `wave_gain` | `12` | Visual sensitivity of the waveform |
| `beeps` | `false` | Start/stop sound cues (Windows only) |
| `log_text` | `false` | `true` writes dictated text to `ditado.log` (handy for debugging, worse for privacy) |
| `max_seconds` | `120` | Recording cap (guards against a stuck key) |
| `post_process` | `false` | Optional correction layer via a local LLM ([Ollama](https://ollama.com)); adds latency |

## Privacy & security

- **No data leaves your machine.** The project's only network connection is downloading the model from Hugging Face during installation (plus a model-version check on startup, which fails harmlessly if you're offline).
- **No API keys, no accounts, no telemetry, no open ports.** The code is a single file (`ditado.py`) you can audit.
- **Global keyboard hook:** this is what lets the hotkey work in any app — the `pynput` library listens for key presses. The app only reacts to the dictation combo and discards the rest; nothing is recorded (it is not a keylogger, and the code is right there to check). Antivirus tools occasionally flag keyboard hooks; that's an expected false positive for this class of tool (any hotkey/dictation app uses the same mechanism).
- **Log:** by default `ditado.log` records only metrics (duration, processing time). Dictated text is logged only if you enable `log_text`.

## Performance (reference: i5-12450HX + RTX 3050 6GB)

| Config | 14s of speech | Accuracy |
|---|---|---|
| large-v3-turbo GPU | ~0.9s | top-tier, jargon intact |
| small CPU | ~3.0s | good, stumbles on jargon |

RAM: ~800MB resident. VRAM (GPU mode): ~1.5GB. Boot: 5 to 60s loading the model (once per login).

## Troubleshooting

- **Nothing happens on release:** check `ditado.log`. "nao captei fala" = the VAD detected no voice (mic muted? check the system's default input).
- **macOS: hotkey doesn't fire:** missing Accessibility/Input Monitoring permission (Settings → Privacy & Security). Quit and relaunch the app after granting it.
- **Linux: won't type/paste:** confirm an X11 session (`echo $XDG_SESSION_TYPE`) and that `xclip` is installed.
- **Text won't paste into an app running as admin (Windows):** OS limitation; run Ditado as admin if you need to dictate into elevated apps.
- **GPU not used:** check `nvidia-smi` and `ditado.log` (a "fallback small/cpu" line means CUDA failed; the app keeps working on CPU).
- **A technical word comes out wrong:** add it to `dicionario.txt`.

## Uninstall

Stop the app, delete the project folder, and if you enabled autostart: Windows `shell:startup` → `ditado.vbs`; macOS `~/Library/LaunchAgents/com.ditado.dictation.plist`; Linux `~/.config/autostart/ditado.desktop`. Downloaded model: `~/.cache/huggingface/hub` (Windows: `%USERPROFILE%\.cache\huggingface\hub`).

## License

[MIT](LICENSE)
