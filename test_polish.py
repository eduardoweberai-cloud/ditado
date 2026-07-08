"""Teste da camada de polish (LLM local via Ollama), sem mic/hotkey.
Uso: python test_polish.py  (roda casos embutidos)
     python test_polish.py "texto bruto qualquer"
"""

import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))


def _load_cfg():
    for name in ("config.json", "config.example.json"):
        path = os.path.join(BASE, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    raise SystemExit("config.example.json nao encontrado")


cfg = _load_cfg()

# mesmo prompt do ditado.py
import ditado

CASOS = [
    "então tipo assim eu preciso que você mande o relatório pro cliente amanhã "
    "cedo sem falta tá e depois marca reunião com a equipe quinta às dez",
    "oi tudo bem passando pra avisar que eu vou chegar mais tarde hoje "
    "pode deixar que eu compro o pão",
    "cria uma story nova sobre o centro de moderação e "
    "depois roda o cue a gate antes de fazer o push",
    "você consegue me mandar aquele arquivo do orçamento até sexta feira "
    "porque eu preciso apresentar na reunião de segunda",
]


MODEL = cfg["ollama_model"]
if "--model" in sys.argv:
    i = sys.argv.index("--model")
    MODEL = sys.argv[i + 1]
    del sys.argv[i:i + 2]


def polish(text):
    payload = json.dumps({
        "model": MODEL,
        "stream": False,
        "keep_alive": cfg["ollama_keep_alive"],
        "options": {"temperature": 0.1, "num_predict": 1024},
        "messages": ditado.build_polish_messages(text),
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["ollama_url"].rstrip("/") + "/api/chat", data=payload,
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"].strip(), time.time() - t0


if __name__ == "__main__":
    casos = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else CASOS
    for bruto in casos:
        final, dt = polish(bruto)
        print(f"\n[{dt:.1f}s]")
        print("BRUTO :", bruto)
        print("POLIDO:", final)
