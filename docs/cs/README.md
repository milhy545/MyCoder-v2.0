# Claude CLI Authentication Module - Česká dokumentace

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Robustní, produkčně připravený Python modul pro integraci s Claude AI **bez API klíčů**. Využívá autentifikaci Claude CLI pro bezproblémový přístup k funkcím Claude Code.

## 🎯 Klíčové vlastnosti

- **Žádné API klíče nejsou potřeba**: Používá autentifikaci Claude CLI (`claude auth login`)
- **Trojitý fallback systém**: SDK → CLI → Graceful error handling
- **Persistence sessions**: Inteligentní správa a obnovení sessions
- **Produkčně připravený**: Comprehensive error handling a logging
- **Snadná integrace**: Jednoduchý jednotný interface pro jakýkoli Python projekt
- **Paměťově optimalizovaný**: Efektivní streaming a bounded buffers

## 🚀 Rychlý start

### Instalace

```bash
# Instalace Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Autentifikace s Claude
claude auth login

# Instalace tohoto modulu
pip install claude-cli-auth
```

### Základní použití

```python
from claude_cli_auth import ClaudeAuthManager
from pathlib import Path

# Inicializace
claude = ClaudeAuthManager()

# Jednoduchý dotaz
response = await claude.query(
    "Vysvětli tento kód stručně",
    working_directory=Path(".")
)

print(response.content)
print(f"Cena: ${response.cost:.4f}")
```

### Se streamingem a správou sessions

```python
# Streaming callback
async def on_stream(update):
    print(f"[{update.type}] {update.content}")

response = await claude.query(
    "Vytvoř Python funkci",
    working_directory=Path("./src"),
    stream_callback=on_stream,
    session_id="muj-projekt-session"
)

# Pokračování v konverzaci
response2 = await claude.query(
    "Přidej error handling do té funkce",
    session_id="muj-projekt-session",
    continue_session=True
)
```

## 📚 Kompletní použití

### Správa sessions

```python
# Seznam všech sessions
sessions = claude.list_sessions()

# Získání detailů session
session = claude.get_session("muj-projekt-session")
if session:
    print(f"Celková cena: ${session.total_cost:.4f}")
    print(f"Zprávy: {session.total_turns}")

# Vyčištění starých sessions
cleaned = await claude.cleanup_sessions()
print(f"Vyčištěno {cleaned} expirovaných sessions")
```

### Konfigurace

```python
from claude_cli_auth import AuthConfig

config = AuthConfig(
    timeout_seconds=60,           # Timeout pro dotazy
    max_turns=10,                 # Max počet tahů v konverzaci
    session_timeout_hours=48,     # Expiration sessions
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    use_sdk=True,                 # Preferovat SDK před CLI
    enable_streaming=True,        # Povolit streaming
)

claude = ClaudeAuthManager(config=config)
```

### Monitorování a statistiky

```python
# Zdravotní kontrola
if claude.is_healthy():
    print("✅ Systém je zdravý")

# Statistiky použití
stats = claude.get_stats()
print(f"Celkem dotazů: {stats['total_requests']}")
print(f"Úspěšnost: {stats['success_rate']:.1%}")
print(f"Celková cena: ${stats['total_cost']:.4f}")
print(f"Průměrná doba: {stats['avg_duration_ms']:.0f}ms")

# Detaily konfigurace
config_info = claude.get_config()
print(f"SDK dostupný: {config_info['sdk_available']}")
print(f"CLI interface: {'✅' if config_info['cli_interface_initialized'] else '❌'}")
```

## 🏗️ Architektura

```
┌─────────────────────────────────────┐
│           Vaše aplikace             │
├─────────────────────────────────────┤
│        ClaudeAuthManager            │
│         (Hlavní interface)          │
├─────────────────────────────────────┤
│  Primary: Python SDK + CLI Auth    │
│  Fallback: Direct CLI Subprocess   │
│  Emergency: Error Recovery          │
├─────────────────────────────────────┤
│        Claude CLI (~/.claude/)     │
└─────────────────────────────────────┘
```

## 🔧 Jádro komponent

- **`AuthManager`**: Správa sessions a přihlašovacích údajů
- **`CLIInterface`**: Direct CLI subprocess wrapper
- **`SDKInterface`**: Python SDK s CLI autentifikací (volitelné)
- **`ClaudeAuthManager`**: Jednotný API s inteligentními fallbacks

## 🔍 Error handling

Modul poskytuje komprehensivní error handling pro všechny běžné scénáře:

### Typy chyb

```python
from claude_cli_auth import (
    ClaudeAuthError,           # Základní autentifikační chyba
    ClaudeConfigError,         # Konfigurační problémy
    ClaudeSessionError,        # Problémy se sessions
    ClaudeTimeoutError,        # Timeouty
    ClaudeCLIError,           # CLI execution errors
    ClaudeParsingError,       # Chyby při parsování odpovědí
)

try:
    response = await claude.query("Test dotaz")
except ClaudeAuthError as e:
    print(f"Autentifikační problém: {e.message}")
    print(f"Návrhy řešení: {'; '.join(e.suggestions)}")
except ClaudeTimeoutError as e:
    print(f"Timeout po {e.details['timeout']} sekundách")
```

### Automatické řešení problémů

- **Autentifikační problémy**: Automatické re-login prompts
- **Síťové problémy**: Inteligentní retry s backoff
- **Session expiration**: Automatické recovery sessions
- **Tool validation**: Security-aware filtrování nástrojů
- **Memory management**: Bounded buffers a cleanup

## ⚙️ Pokročilé funkce

### Adaptive režimy

Modul automaticky detekuje dostupné metody a přepíná mezi nimi:

```python
# Doma s plným přístupem
claude = ClaudeAuthManager(
    prefer_sdk=True,        # Preferuj SDK
    enable_fallback=True    # Povolit CLI fallback
)

# Omezené prostředí (pouze CLI)
claude = ClaudeAuthManager(
    prefer_sdk=False,       # Pouze CLI
    enable_fallback=False   # Bez fallback
)
```

### Batch operations

```python
# Více dotazů v sérii
queries = [
    "Analyzuj tento soubor",
    "Navrhni vylepšení", 
    "Vytvoř testy"
]

session_id = "batch-session"
for i, query in enumerate(queries):
    response = await claude.query(
        query,
        session_id=session_id,
        continue_session=i > 0
    )
    print(f"Odpověď {i+1}: {response.content[:100]}...")
```

## 🚨 Troubleshooting

### Časté problémy

1. **"Claude CLI not authenticated"**
   ```bash
   claude auth login
   ```

2. **"Claude CLI not found"**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **"Session expired"**
   ```python
   # Sessions expirují po 24 hodinách (konfigurovatelné)
   await claude.cleanup_sessions()
   ```

4. **"Usage limit reached"**
   - Čekejte na reset limitů
   - Používejte menší dotazy
   - Kontrolujte usage s `claude.get_stats()`

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Zapnout debug pro modul
logging.getLogger("claude_cli_auth").setLevel(logging.DEBUG)
```

## 📖 Příklady integrace

### S Flask/FastAPI

```python
from flask import Flask, request, jsonify
from claude_cli_auth import ClaudeAuthManager

app = Flask(__name__)
claude = ClaudeAuthManager()

@app.route('/ask', methods=['POST'])
async def ask_claude():
    try:
        data = request.json
        response = await claude.query(
            prompt=data['question'],
            working_directory=Path(data.get('project_dir', '.')),
            session_id=data.get('session_id')
        )
        
        return jsonify({
            'response': response.content,
            'session_id': response.session_id,
            'cost': response.cost
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### S Telegram botom

```python
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

claude = ClaudeAuthManager()

async def handle_message(update: Update, context):
    try:
        user_id = update.effective_user.id
        response = await claude.query(
            prompt=update.message.text,
            user_id=user_id,
            session_id=f"telegram_{user_id}"
        )
        
        await update.message.reply_text(response.content)
        
    except Exception as e:
        await update.message.reply_text(f"Chyba: {str(e)}")

# Setup Telegram bot...
```

## 🔒 Bezpečnost

- **Ochrana přihlašovacích údajů**: Bezpečné token storage v `~/.claude/`
- **Tool validation**: Konfigurovatelné povolené/zakázané nástroje
- **Session isolation**: User-specific session management
- **Rate limiting**: Vestavěné request throttling
- **Audit logging**: Komprehensivní operation tracking

## 🤝 Přispívání

Tento modul byl původně vyvinut pro MyCoder projekt a extraktován jako znovupoužitelný modul. Kompatibilní s:

- Telegram boty (testován v produkci)
- Web aplikace
- CLI nástroje
- Jupyter notebooks
- Docker kontejnery

## 📄 Licence

MIT License - viz [LICENSE](../../LICENSE) pro detaily.

---

**Poznámka**: Tento modul vyžaduje nainstalovaný a autentifikovaný Claude Code CLI. Nepoužívá ani nevyžaduje Anthropic API klíče.