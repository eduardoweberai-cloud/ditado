"""Testes da maquina de estados do atalho (sem mic/tkinter/whisper).

Regressao do bug em que modificadores "presos" (release perdido em combos
com a tecla Win) faziam QUALQUER tecla disparar o ditado. O fix reconcilia
held com o teclado real via mod_physically_down (GetAsyncKeyState no Windows).

Uso: python test_hotkey.py
"""
import os
import sys
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ditado
from pynput import keyboard as pkb

KEY_A = pkb.KeyCode.from_char("a")
WIN = pkb.Key.cmd
CTRL = pkb.Key.ctrl


def make_app():
    with mock.patch.object(ditado, "Overlay"), \
            mock.patch.object(ditado, "Recorder"):
        app = ditado.App()
    app.hotkey_mods, app.hotkey_label = ditado.parse_hotkey("ctrl+sys")
    app.held = {m: False for m in ("ctrl", "sys", "alt")}
    app.active = False
    app.started = []
    app._start = lambda: app.started.append(True)
    app._finish = lambda: None
    return app


def os_state(**physical):
    """side_effect p/ mod_physically_down: mod -> True/False."""
    return lambda mod: physical.get(mod, False)


def check(name, cond):
    print(("OK  " if cond else "FALHA ") + name)
    if not cond:
        check.failed += 1
check.failed = 0


# 1) Modificadores presos (held True) mas fisicamente soltos: uma letra
#    qualquer NAO pode disparar o ditado, e held deve ser corrigido.
app = make_app()
app.held["ctrl"] = app.held["sys"] = True
with mock.patch.object(ditado, "mod_physically_down",
                       side_effect=os_state()):
    app.on_press(KEY_A)
check("tecla qualquer com mods presos nao dispara", app.started == [])
check("held reconciliado para solto", app.held == {"ctrl": False,
                                                   "sys": False, "alt": False})

# 2) Combo real (Ctrl fisicamente segurado + aperta Win): dispara.
app = make_app()
with mock.patch.object(ditado, "mod_physically_down",
                       side_effect=os_state(ctrl=True, sys=True)):
    app.on_press(WIN)
check("Ctrl+Win real dispara o ditado", app.started == [True])

# 3) Parcial preso (sys grudado) + usuario aperta so Ctrl: nao dispara,
#    porque o SO confirma que a tecla Win nao esta pressionada.
app = make_app()
app.held["sys"] = True
with mock.patch.object(ditado, "mod_physically_down",
                       side_effect=os_state(ctrl=True)):
    app.on_press(CTRL)
check("sys preso + Ctrl real nao dispara sozinho", app.started == [])

# 4) Demonstra o BUG original: sem reconciliacao (comportamento antigo,
#    mod_physically_down -> None), mods presos + letra qualquer disparam.
app = make_app()
app.held["ctrl"] = app.held["sys"] = True
with mock.patch.object(ditado, "mod_physically_down", side_effect=lambda m: None):
    app.on_press(KEY_A)
check("sem reconciliacao o bug reaparece (esperado)", app.started == [True])

print()
if check.failed:
    print(f"{check.failed} teste(s) falharam")
    sys.exit(1)
print("todos os testes passaram")
