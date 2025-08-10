# Enhanced MyCoder v2.0 - Česká příručka

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](../../LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](#testovani)
[![Q9550 Compatible](https://img.shields.io/badge/Q9550-thermal%20managed-orange.svg)](#tepelni-management)

Enhanced MyCoder v2.0 je komplexní AI vývojářský asistent s **5-stupňovou fallback architekturou API poskytovatelů**, **Q9550 tepelným managementem** a **FEI-inspirovanou architekturou**. Navržený pro produkční prostředí vyžadující vysokou dostupnost a tepelnou bezpečnost.

## 🎯 Klíčové vlastnosti

- **5-stupňová fallback architektura**: Claude Anthropic → Claude OAuth → Gemini → Ollama Local → Ollama Remote
- **Q9550 tepelný management**: Integrované monitorování a throttling pro Intel Q9550 procesory
- **FEI-inspirovaná architektura**: Tool Registry Pattern, Service Layer Pattern, Event-based execution
- **Komplexní testování**: 85% pokrytí testy (197 testů napříč všemi úrovněmi)
- **Session persistence**: Udržování kontextu konverzace napříč poskytovateli
- **Konfigurace z více zdrojů**: JSON, environment variables, výchozí hodnoty

## 🚀 Rychlý start

### Instalace

```bash
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
pip install -r requirements.txt
```

### Základní použití

```python
from enhanced_mycoder_v2 import EnhancedMyCoderV2
from pathlib import Path

# Základní konfigurace
config = {
    "claude_oauth": {"enabled": True},
    "ollama_local": {"enabled": True},
    "thermal": {"enabled": True, "max_temp": 75}
}

# Inicializace MyCoder
mycoder = EnhancedMyCoderV2(
    working_directory=Path("."),
    config=config
)

# Spuštění systému
await mycoder.initialize()

response = await mycoder.process_request(
    "Analyzuj tento Python soubor a navrhni optimalizace",
    files=[Path("example.py")]
)

print(f"Odpověď: {response['content']}")
print(f"Poskytovatel: {response['provider']}")
print(f"Cena: ${response['cost']}")
```

### Rychlé příkazy

```bash
# Spuštění funkčních testů
python tests/functional/test_mycoder_live.py --interactive

# Spuštění stress testů
python tests/stress/run_stress_tests.py --quick

# Kontrola stavu systému
python -c "from enhanced_mycoder_v2 import EnhancedMyCoderV2; import asyncio; asyncio.run(EnhancedMyCoderV2().get_system_status())"
```

## 🏗️ Architektura

### 5-stupňová Fallback Architektura API Poskytovatelů

```
1. Claude Anthropic API    ← Primární (placený, vysoká kvalita)
2. Claude OAuth           ← Sekundární (zdarma, autentifikovaný)  
3. Gemini API            ← Terciární (Google AI)
4. Ollama Local          ← Kvartérní (lokální inference)
5. Ollama Remote         ← Finální (vzdálené Ollama instance)
```

### FEI-Inspirované Komponenty

- **Tool Registry Pattern**: Centralizované správa nástrojů s execution kontexty
- **Service Layer Pattern**: Čisté oddělení mezi API poskytovateli a business logikou
- **Event-Based Architecture**: Reaktivní systém s health monitoringem a tepelným vědomím

### Q9550 Tepelný Management

Integrované tepelné monitorování a throttling pro Intel Q9550 procesory:

- **Monitorování Teploty**: Real-time sledování teploty CPU
- **Automatické Throttling**: Snižuje AI zátěž když teplota překročí 75°C
- **Nouzová Ochrana**: Hard shutdown při 85°C pro prevenci poškození hardware
- **PowerManagement Integrace**: Používá existující Q9550 tepelné skripty

## 🔧 Konfigurace

### Environment Variables

```bash
# API Klíče
export ANTHROPIC_API_KEY="váš_anthropic_klíč"
export GEMINI_API_KEY="váš_gemini_klíč"

# Systémová Konfigurace
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

### Konfigurační Soubor

Vytvořte `mycoder_config.json`:

```json
{
  "claude_anthropic": {
    "enabled": true,
    "timeout_seconds": 30,
    "model": "claude-3-5-sonnet-20241022"
  },
  "claude_oauth": {
    "enabled": true,
    "timeout_seconds": 45
  },
  "gemini": {
    "enabled": true,
    "timeout_seconds": 30,
    "model": "gemini-1.5-pro"
  },
  "ollama_local": {
    "enabled": true,
    "base_url": "http://localhost:11434",
    "model": "tinyllama"
  },
  "ollama_remote_urls": [
    "http://server1:11434",
    "http://server2:11434"
  ],
  "thermal": {
    "enabled": true,
    "max_temp": 75,
    "critical_temp": 85,
    "performance_script": "/path/to/performance_manager.sh"
  },
  "system": {
    "log_level": "INFO",
    "enable_tool_registry": true,
    "enable_mcp_integration": true
  }
}
```

### Pokročilá Konfigurace

```python
from config_manager import ConfigManager

# Načtení ze souboru
config_manager = ConfigManager("mycoder_config.json")
config = config_manager.load_config()

# Aktualizace konkrétního poskytovatele
config_manager.update_provider_config("ollama_local", {
    "model": "llama2:13b",
    "timeout_seconds": 120
})

# Uložení změn
config_manager.save_config("updated_config.json")
```

## 🛠️ Funkce

### Podpora Multi-API Providera

- **Inteligentní Fallback**: Automatické přepínání mezi poskytovateli
- **Health Monitoring**: Real-time sledování stavu poskytovatelů
- **Optimalizace Nákladů**: Preference pro levnější/zdarma poskytovatele
- **Metriky Výkonu**: Sledování response times a success rates

### Tepelný Management (Q9550)

- **Hardware Integrace**: Přímá integrace s Q9550 tepelnými senzory
- **Proaktivní Throttling**: Prevence tepelného poškození před jeho výskytem
- **Performance Scaling**: Úprava AI zátěže podle teploty
- **Systémová Ochrana**: Nouzové vypnutí při kritických teplotách

### Tool Registry Systém

- **Modulární Nástroje**: File operace, MCP integrace, tepelné monitorování
- **Execution Kontexty**: Bezpečné sandboxed spouštění nástrojů
- **Permission Systém**: Role-based access control pro nástroje
- **Performance Monitoring**: Sledování používání a výkonu nástrojů

### Session Management

- **Persistentní Sessions**: Udržování kontextu konverzace napříč requesty
- **Provider Transitions**: Bezproblémové přepínání mezi API poskytovateli
- **Automatické Cleanup**: Memory-eficient správa sessions
- **Recovery Support**: Obnovení sessions po restartu systému

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

## 🚀 Výkon

### Benchmarky (Q9550 @ 2.83GHz)

| Operace | Response Time | Poskytovatel | Poznámky |
|-----------|---------------|----------|-------|
| Jednoduchý Dotaz | 0.5-2.0s | Claude OAuth | Cached auth |
| Analýza Souboru | 2.0-5.0s | Ollama Local | Lokální inference |
| Komplexní Úloha | 5.0-15.0s | Claude Anthropic | API calls |
| Tepelná Kontrola | <0.1s | Q9550 Sensors | Hardware přímé |

### Systémové Prostředky

- **Paměť**: ~200MB baseline, ~500MB pod zátěží
- **CPU**: Variabilní na základě tepelných limitů (0-100%)
- **Síť**: Minimální pro lokální poskytovatele, ~1MB/request pro API poskytovatele
- **Úložiště**: ~50MB instalace, logy rostou s používáním

## 🔒 Bezpečnost & Ochrana

### Správa API Klíčů

- **Environment Variables**: Bezpečné ukládání klíčů
- **Žádné Logování**: API klíče nejsou nikdy loggované nebo cache-ované
- **Podpora Rotace**: Snadné aktualizace klíčů bez restartu

### Tepelná Bezpečnost

- **Hardware Ochrana**: Prevence poškození Q9550 přehřátím
- **Postupné Throttling**: Plynulé škálování výkonu
- **Nouzové Vypnutí**: Poslední nástroj ochrany při 85°C
- **Recovery Procedury**: Automatické obnovení když teploty klesnou

### Tool Sandboxing

- **Execution Kontexty**: Izolovaná prostředí nástrojů
- **File System Limity**: Omezení přístupu nástrojů na working directory
- **Resource Limity**: CPU/memory omezení per tool execution
- **Permission Validace**: Role-based tool access control

## 📁 Projektová Struktura

```
MyCoder-v2.0/
├── src/                          # Zdrojový kód
│   ├── enhanced_mycoder_v2.py   # Hlavní MyCoder třída
│   ├── api_providers.py         # Implementace API poskytovatelů
│   ├── config_manager.py        # Správa konfigurace
│   ├── tool_registry.py         # Tool registry systém
│   └── __init__.py              # Inicializace balíčku
├── tests/                       # Testovací sady
│   ├── unit/                    # Unit testy
│   ├── integration/             # Integrační testy
│   ├── functional/              # Funkční testy
│   ├── stress/                  # Stress testy
│   └── conftest.py              # Testovací konfigurace
├── docs/                        # Dokumentace
│   ├── api/                     # API dokumentace
│   ├── guides/                  # Uživatelské příručky
│   ├── examples/                # Příklady použití
│   └── cs/                      # Česká dokumentace
├── examples/                    # Kódové příklady
├── scripts/                     # Utility skripty
├── requirements.txt             # Závislosti
├── pyproject.toml              # Projektová konfigurace
└── README.md                   # Tento soubor
```

## 🔗 Integrace

### MCP (Model Context Protocol)

```python
from mcp_connector import MCPConnector

# Inicializace MCP připojení
mcp = MCPConnector(server_url="http://localhost:8000")
await mcp.connect()

# Použití s MyCoder
mycoder = EnhancedMyCoderV2(
    working_directory=Path("."),
    config={"mcp_integration": {"enabled": True, "server_url": "http://localhost:8000"}}
)
```

### Docker Podpora

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Pro Q9550 tepelný management
RUN apt-get update && apt-get install -y lm-sensors

ENV MYCODER_THERMAL_ENABLED=false  # Vypnout v kontejnerech
CMD ["python", "-m", "enhanced_mycoder_v2"]
```

### CI/CD Integrace

```yaml
# Příklad GitHub Actions
name: MyCoder Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ --no-thermal
```

## 🤝 Přispívání

### Vývojové Nastavení

```bash
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0

# Instalace vývojových závislostí
pip install -r requirements-dev.txt

# Spuštění pre-commit hooks
pre-commit install

# Spuštění testů
python -m pytest tests/
```

### Kódovací Standardy

- **Python 3.8+** kompatibilita
- **Type hints** pro všechny veřejné APIs
- **Docstrings** pro všechny třídy a metody
- **85%+ test coverage** pro nové funkce
- **Black** code formátování
- **Pytest** pro všechny testy

### Pull Request Proces

1. Fork repository
2. Vytvoření feature branch (`git checkout -b feature/amazing-feature`)
3. Napsání testů pro novou funkcionalitu
4. Zajištění, že všechny testy projdou
5. Aktualizace dokumentace
6. Odeslání pull request

## 📄 Licence

Tento projekt je licencován pod MIT License - viz [LICENSE](../../LICENSE) pro detaily.

## 🙏 Poděkování

- **Anthropic** za přístup k Claude API
- **Google** za Gemini API
- **Ollama** za lokální LLM infrastrukturu
- **Intel Q9550** komunitě za tepelné management poznatky
- **FEI** architektonické vzory inspirace

## 📞 Podpora

- **GitHub Issues**: [Hlášení chyb a feature requesty](https://github.com/milhy545/MyCoder-v2.0/issues)
- **Dokumentace**: [Úplná dokumentace](../README.md)
- **Příklady**: [Příklady použití](../../examples/)
- **Diskuze**: [Community diskuze](https://github.com/milhy545/MyCoder-v2.0/discussions)

---

**Vytvořeno s ❤️ pro AI vývojářskou komunitu**

*Enhanced MyCoder v2.0 - Kde AI potkává tepelnou zodpovědnost*