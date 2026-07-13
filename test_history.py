"""Testes do historico de ditados e do atalho que abre a janela.
Cobre a rede de seguranca (persistir em disco) sem depender de mic/whisper.

Uso: python test_history.py
"""
import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import ditado
from pynput import keyboard as pkb


def check(name, cond):
    print(("OK  " if cond else "FALHA ") + name)
    if not cond:
        check.failed += 1
check.failed = 0


def make_app():
    with mock.patch.object(ditado, "Overlay"), \
            mock.patch.object(ditado, "Recorder"):
        app = ditado.App()
    app.active = False
    return app


# --- parse_combo_key -------------------------------------------------------
mods, char, label = ditado.parse_combo_key("ctrl+alt+h", {"ctrl", "alt"}, "h")
check("parse ctrl+alt+h", mods == {"ctrl", "alt"} and char == "h")
check("label do atalho de historico", label == "Ctrl+Alt+H")

mods, char, _ = ditado.parse_combo_key("lixo", {"ctrl", "alt"}, "h")
check("parse invalido cai no default", mods == {"ctrl", "alt"} and char == "h")

mods, char, _ = ditado.parse_combo_key("shift+sys+k", {"ctrl", "alt"}, "h")
check("parse shift+sys+k", mods == {"shift", "sys"} and char == "k")


# --- save / load round-trip ------------------------------------------------
tmp = os.path.join(tempfile.gettempdir(), "ditado_hist_test.jsonl")
if os.path.exists(tmp):
    os.remove(tmp)

with mock.patch.object(ditado, "HISTORY_PATH", tmp):
    app = make_app()
    app.cfg["max_history"] = 200
    app._save_history("primeiro ditado com acento: ação")
    app._save_history("segundo")
    app._save_history("terceiro")
    hist = app._load_history()

check("carregou 3 itens", len(hist) == 3)
check("mais recente primeiro", hist[0]["text"] == "terceiro")
check("acento preservado no disco", hist[2]["text"] ==
      "primeiro ditado com acento: ação")
check("cada item tem timestamp", all(h.get("ts") for h in hist))

# max_history limita a leitura
with mock.patch.object(ditado, "HISTORY_PATH", tmp):
    app = make_app()
    app.cfg["max_history"] = 2
    hist = app._load_history()
check("max_history limita a 2", len(hist) == 2 and hist[0]["text"] == "terceiro")

# load sem arquivo nao quebra
missing = os.path.join(tempfile.gettempdir(), "ditado_hist_inexistente.jsonl")
if os.path.exists(missing):
    os.remove(missing)
with mock.patch.object(ditado, "HISTORY_PATH", missing):
    app = make_app()
    check("historico inexistente retorna vazio", app._load_history() == [])


# --- key_matches_char (robusto ao control-char do Ctrl) --------------------
check("key_matches_char: 'h' simples",
      ditado.key_matches_char(pkb.KeyCode.from_char("h"), "h"))
# Com Ctrl pressionado o Windows entrega char='\x08' e vk=72 (nao 'h'):
check("key_matches_char: Ctrl+H (vk=72, control-char)",
      ditado.key_matches_char(pkb.KeyCode(vk=72, char="\x08"), "h"))
check("key_matches_char: tecla errada nao casa",
      not ditado.key_matches_char(pkb.KeyCode.from_char("j"), "h"))


# --- atalho Ctrl+Alt+H abre a janela, inclusive com o control-char ---------
for label, key in (("char 'h'", pkb.KeyCode.from_char("h")),
                   ("Ctrl+H real (vk=72, \\x08)", pkb.KeyCode(vk=72, char="\x08"))):
    app = make_app()
    app._load_history = lambda: [{"ts": "2026-07-12 17:43:04", "text": "oi"}]
    with mock.patch.object(ditado, "mod_physically_down",
                           side_effect=lambda m: m in ("ctrl", "alt")):
        app.on_press(key)
    check(f"Ctrl+Alt+H abre a janela ({label})",
          app.overlay.open_history.called)

# uma letra qualquer sem os modificadores NAO abre a janela
app = make_app()
app._load_history = lambda: []
with mock.patch.object(ditado, "mod_physically_down", side_effect=lambda m: False):
    app.on_press(pkb.KeyCode.from_char("h"))
check("H sozinho nao abre a janela", not app.overlay.open_history.called)


# --- smoke test da janela real (tolera ambiente sem display) ---------------
try:
    ov = ditado.Overlay(lambda: 0.0)
    ov._show_history([{"ts": "2026-07-12 17:43:04", "text": "olá açúcar"},
                      {"ts": "2026-07-12 17:40:00", "text": "segundo item"}])
    win_ok = ov._hist_win is not None
    ov._hist_win.update()
    ov._hist_win.destroy()
    ov.root.destroy()
    check("janela de historico construida sem erro", win_ok)
except tk.TclError as e:
    print("SKIP janela real (sem display):", e)

if os.path.exists(tmp):
    os.remove(tmp)

print()
if check.failed:
    print(f"{check.failed} teste(s) falharam")
    sys.exit(1)
print("todos os testes passaram")
