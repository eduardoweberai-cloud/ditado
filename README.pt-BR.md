# Ditado

**[English](README.md)** · Português

Ditado por voz **100% local e gratuito**, estilo Wispr Flow, para **Windows, macOS e Linux**.

Segure **Ctrl + tecla do sistema** (Win no Windows, Cmd no Mac, Super no Linux), fale, solte: o texto aparece onde o cursor estiver, em qualquer aplicativo. Um pill discreto no rodapé mostra a waveform da sua voz enquanto grava.

- **Offline de verdade:** o áudio nunca sai da sua máquina. Sem conta, sem assinatura, sem telemetria.
- **Precisão de topo:** Whisper `large-v3-turbo` na GPU NVIDIA (detectada automaticamente) ou `small` na CPU.
- **Dicionário pessoal:** ensine seu jargão, nomes e marcas (como o dicionário do Wispr).
- **Atalho configurável:** o combo padrão é Ctrl+Win/Cmd/Super, mas você troca no `config.json`.
- **Leve:** processo residente com prioridade baixa; não disputa CPU com o que você estiver usando.

## Instalação

Pré-requisito: [Python 3.10+](https://python.org) (no Windows, marque "Add to PATH" ao instalar).

O instalador cria um ambiente isolado (`.venv`), instala as dependências, detecta GPU NVIDIA, **baixa o modelo de voz** (uma vez só, ~500MB CPU ou ~1,6GB GPU, do Hugging Face) e gera os scripts de iniciar/parar. Nada é instalado fora da pasta do projeto além do modelo (cache padrão do Hugging Face).

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Autostart
```

Depois: dê dois cliques em `iniciar-ditado.vbs`. O `-Autostart` faz iniciar junto com o Windows (opcional).

### macOS

```bash
bash install.sh --autostart
./ditado-start.sh
```

Na primeira execução o macOS vai pedir permissões. Conceda ao Terminal (ou ao Python) em **Ajustes → Privacidade e Segurança**: **Microfone**, **Acessibilidade** e **Monitoramento de Entrada** (necessários para o atalho global e para colar o texto). Sem CUDA no Mac: roda em CPU.

### Linux

```bash
bash install.sh --autostart
./ditado-start.sh
```

Requisitos: sessão **X11** (no Wayland puro, atalhos globais são bloqueados pelo compositor), `python3-tk` e `xclip` (`sudo apt install python3-tk xclip`). Com GPU NVIDIA + driver, o instalador configura CUDA sozinho.

## Uso

1. Posicione o cursor onde quer o texto (chat, editor, browser, qualquer campo).
2. **Segure** o atalho (padrão `Ctrl + Win/Cmd/Super`) e fale: o pill mostra sua voz ao vivo.
3. **Solte**: a onda fica âmbar enquanto transcreve e o texto é colado no cursor (flash verde).

Extras:

- Atalho + qualquer outra tecla **cancela** a gravação: seus atalhos do sistema (ex: trocar de desktop virtual) continuam funcionando.
- Sair do app: `Ctrl+Alt+F12`, ou `parar-ditado.bat` (Windows) / `./ditado-stop.sh` (Mac/Linux).
- Trocou de microfone (plugou um headset)? A próxima gravação já usa o novo input padrão do sistema, sozinho.

## Trocar o atalho

Edite `hotkey` no `config.json` e reinicie o ditado. Combine `ctrl`, `alt`, `shift` e `sys` (a tecla do sistema: Win/Cmd/Super) com `+`:

```json
"hotkey": "ctrl+shift"
```

Exemplos: `ctrl+sys` (padrão), `ctrl+shift`, `alt+shift`, `ctrl+alt`. Evite deixar exatamente `ctrl+alt`, que colide com a saída (`Ctrl+Alt+F12`).

## Dicionário pessoal (`dicionario.txt`)

Um termo por linha (jargão, nomes próprios, marcas). O Whisper favorece esses termos ao decodificar. Palavra saindo errada toda vez? Adicione aqui e reinicie o ditado.

```
# exemplos
deploy
pull request
Nome Da Sua Empresa
```

## Configuração (`config.json`)

Criado pelo instalador a partir do `config.example.json`. Edite e reinicie o ditado.

| Chave | Default | Notas |
|---|---|---|
| `model_size` | `small` (CPU) / `large-v3-turbo` (GPU) | Qualquer modelo do faster-whisper |
| `device` | `cpu` / `cuda` | Definido pelo instalador; com falha de GPU, cai sozinho pra CPU |
| `compute_type` | `int8` (CPU) / `int8_float16` (GPU) | |
| `language` | `pt` | Troque pelo seu idioma (`en`, `es`...) ou `null` = detecção automática |
| `beam_size` | `1` (CPU) / `5` (GPU) | Maior = mais preciso e mais lento |
| `hotkey` | `ctrl+sys` | Atalho de ditado (segurar). Combine `ctrl`, `alt`, `shift`, `sys` com `+` |
| `insert_mode` | `paste` | `paste` (clipboard + Ctrl/Cmd+V) ou `type` (digitação simulada) |
| `restore_clipboard` | `true` | Restaura o clipboard anterior após colar |
| `trailing_space` | `true` | Espaço ao final, para emendar ditados |
| `wave_gain` | `12` | Sensibilidade visual da waveform |
| `beeps` | `false` | Sinais sonoros de início/fim (só Windows) |
| `log_text` | `false` | `true` grava os textos ditados no `ditado.log` (útil pra debug, pior pra privacidade) |
| `max_seconds` | `120` | Teto de gravação (proteção contra tecla presa) |
| `post_process` | `false` | Camada opcional de correção via LLM local ([Ollama](https://ollama.com)); adiciona latência |

## Privacidade e segurança

- **Nenhum dado sai da máquina.** A única conexão de rede do projeto é o download do modelo no Hugging Face durante a instalação (e uma checagem de versão do modelo ao iniciar, que falha sem quebrar nada se você estiver offline).
- **Sem chaves de API, sem contas, sem telemetria, sem portas abertas.** O código é um único arquivo (`ditado.py`) que você pode auditar.
- **Hook global de teclado:** é o que permite o atalho funcionar em qualquer app: a biblioteca `pynput` escuta as teclas pressionadas. O app só reage à combinação do ditado e descarta o resto; nada é gravado (não é um keylogger, e o código está aí pra conferir). Antivírus ocasionalmente sinalizam hooks de teclado; é um falso positivo esperado nessa categoria de ferramenta (qualquer app de hotkey/ditado usa o mesmo mecanismo).
- **Log:** por default o `ditado.log` registra só métricas (duração, tempo de processamento). Os textos ditados só entram no log se você ligar `log_text`.

## Performance (referência: i5-12450HX + RTX 3050 6GB)

| Config | 14s de fala | Precisão |
|---|---|---|
| large-v3-turbo GPU | ~0,9s | topo de linha, jargão intacto |
| small CPU | ~3,0s | boa, tropeça em jargão |

RAM: ~800MB residente. VRAM (modo GPU): ~1,5GB. Boot: 5 a 60s carregando o modelo (uma vez por login).

## Troubleshooting

- **Nada acontece ao soltar as teclas:** veja `ditado.log`. "nao captei fala" = o VAD não detectou voz (mic mudo? confira o input padrão do sistema).
- **macOS: atalho não dispara:** falta permissão de Acessibilidade/Monitoramento de Entrada (Ajustes → Privacidade e Segurança). Feche e reabra o app depois de conceder.
- **Linux: não digita/cola:** confirme sessão X11 (`echo $XDG_SESSION_TYPE`) e `xclip` instalado.
- **Texto não cola em app rodando como admin (Windows):** limitação do SO; rode o ditado como admin se precisar ditar em apps elevados.
- **GPU não usada:** confira `nvidia-smi` e o `ditado.log` (linha "fallback small/cpu" indica falha de CUDA; o app segue funcionando em CPU).
- **Palavra técnica sai errada:** adicione ao `dicionario.txt`.

## Desinstalação

Pare o app, remova a pasta do projeto e, se ativou autostart: Windows `shell:startup` → `ditado.vbs`; macOS `~/Library/LaunchAgents/com.ditado.dictation.plist`; Linux `~/.config/autostart/ditado.desktop`. Modelo baixado: `~/.cache/huggingface/hub` (Windows: `%USERPROFILE%\.cache\huggingface\hub`).

## Licença

[MIT](LICENSE)
