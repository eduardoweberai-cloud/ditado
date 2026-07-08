"""Teste E2E do pipeline de transcricao do ditado (sem hotkey/mic).
Uso: python test_ditado.py caminho/para/audio.wav
"""

import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))


def _load_cfg():
    for name in ("config.json", "config.example.json"):
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    raise SystemExit("config.example.json nao encontrado")


cfg = _load_cfg()
wav = sys.argv[1]

import ditado
from faster_whisper import WhisperModel

if str(cfg["device"]).startswith("cuda"):
    ditado.add_cuda_dll_dirs()
hotwords = ditado.load_hotwords()

t0 = time.time()
model = WhisperModel(cfg["model_size"], device=cfg["device"],
                     compute_type=cfg["compute_type"],
                     cpu_threads=cfg["cpu_threads"])
print(f"load do modelo: {time.time() - t0:.1f}s "
      f"({cfg['model_size']}/{cfg['device']}/{cfg['compute_type']})")

t0 = time.time()
segments, info = model.transcribe(
    wav, language=cfg["language"] or None, beam_size=cfg["beam_size"],
    vad_filter=True, condition_on_previous_text=False, hotwords=hotwords)
text = " ".join(s.text.strip() for s in segments).strip()
print(f"transcricao: {time.time() - t0:.1f}s | idioma: {info.language}")
print("TEXTO:", text)
