# Enhanced MyCoder v2.2.0

> **Multi-API AI vývojářský asistent s řízením teploty pro Q9550**

[![Python 3.10-3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](#testování)
[![Q9550 Compatible](https://img.shields.io/badge/Q9550-thermal%20managed-orange.svg)](#řízení-teploty)

Enhanced MyCoder v2.2.0 je komplexní AI vývojářský asistent vybavený **modulární architekturou s podporou mnoha poskytovatelů**, **řízením teploty pro procesory Q9550**, **orchestrací agentů** a architekturou inspirovanou **FEI**. Je navržen pro produkční prostředí vyžadující vysokou dostupnost a teplotní bezpečnost.

[🇺🇸 English Version](README.md)

## 🚀 Rychlý start

### Instalace

```bash
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
# Pomocí Poetry (Doporučeno)
poetry install
```

### Základní použití

```python
from mycoder import EnhancedMyCoderV2
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

# Spuštění zpracování
await mycoder.initialize()

response = await mycoder.process_request(
    "Analyzuj tento Python soubor a navrhni optimalizace",
    files=[Path("example.py")]
)

print(f"Odpověď: {response['content']}")
print(f"Poskytovatel: {response['provider']}")
print(f"Cena: ${response['cost']}")
```

### Interaktivní CLI

```bash
poetry run mycoder
```

Příkazy:
- `/setup` - Konfigurace poskytovatelů a klíčů
- `/providers` - Seznam dostupných poskytovatelů
- `/plan <úkol>` - Generování implementačního plánu
- `/voice start` - Spuštění diktovacího režimu

## 🏗️ Architektura

### Modulární systém poskytovatelů

MyCoder nyní podporuje širokou škálu AI poskytovatelů prostřednictvím modulárního rozhraní:

**LLM Poskytovatelé (Jazykové modely):**
- **Claude Anthropic API** (Primární, Vysoká kvalita)
- **Claude OAuth** (Autentizované CLI)
- **Google Gemini** (Vysoká rychlost, velké kontextové okno, striktní rate limity)
- **AWS Bedrock** (Enterprise, Claude/Titan)
- **OpenAI** (GPT-4o, o1)
- **X.AI** (Grok)
- **Mistral AI** (Open/Commercial)
- **HuggingFace** (Inference API)
- **Ollama** (Lokální/Vzdálený/Termux)
- **Mercury** (Inception Labs)

**TTS Poskytovatelé (Převod textu na řeč):**
- **Azure Speech** (Vysoce kvalitní neurální hlasy)
- **Amazon Polly** (Neural/Standard)
- **ElevenLabs** (Prémiové klonování hlasu)
- **gTTS** (Google Translate)
- **Lokální** (pyttsx3, espeak)

**STT Poskytovatelé (Převod řeči na text):**
- **Whisper** (OpenAI API / Lokální)
- **Google Gemini** (Multimodální)
- **Azure Speech** (V reálném čase)

### Komponenty inspirované FEI

- **Tool Registry Pattern**: Centralizovaná správa nástrojů s kontexty provádění
- **Service Layer Pattern**: Čisté oddělení mezi API poskytovateli a byznys logikou
- **Event-Based Architecture**: Reaktivní systém s monitorováním zdraví a teploty

### Řízení teploty Q9550

Integrované monitorování a omezování výkonu pro procesory Intel Q9550:

- **Monitorování teploty**: Sledování teploty CPU v reálném čase
- **Automatické omezování (Throttling)**: Snížení AI zátěže při překročení 75°C
- **Nouzová ochrana**: Tvrdé vypnutí při 85°C pro prevenci poškození hardwaru
- **Integrace PowerManagement**: Využívá existující termální skripty

## 🔧 Konfigurace

### Proměnné prostředí

```bash
# API Klíče
export ANTHROPIC_API_KEY="sk-..."
export GEMINI_API_KEY="AIza..."
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export MISTRAL_API_KEY="..."
export HF_TOKEN="hf_..."
export ELEVENLABS_API_KEY="..."
export AZURE_SPEECH_KEY="..."
export AZURE_SPEECH_REGION="eastus"

# AWS Credentials (pokud používáte Bedrock/Polly)
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# Systémová konfigurace
export MYCODER_DEBUG=1
export MYCODER_THERMAL_MAX_TEMP=75
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

## 🛠️ Funkce

### Podpora více API poskytovatelů

- **Inteligentní fallback**: Automatické přepnutí při výpadku
- **Monitorování zdraví**: Sledování stavu poskytovatelů v reálném čase
- **Optimalizace nákladů**: Preferuje bezplatné/levnější poskytovatele, pokud jsou dostupní
- **Metriky výkonu**: Sledování doby odezvy a úspěšnosti
- **Circuit Breaker & Rate Limiting**: Odolná správa API s perzistentním omezením rychlosti (RPM/RPD), aby se předešlo banům (zejména u Google API).

### Řízení teploty (Q9550)

- **Hardwarová integrace**: Přímá integrace s termálními senzory Q9550
- **Proaktivní throttling**: Prevence tepelného poškození
- **Škálování výkonu**: Úprava zátěže podle teploty

### Systém registru nástrojů

- **Modulární nástroje**: Operace se soubory, integrace MCP, monitorování teploty
- **Kontexty provádění**: Bezpečné spouštění v sandboxu
- **Systém oprávnění**: Řízení přístupu k nástrojům na základě rolí

## 📊 Testování

### Komplexní testovací sada

- **Unit Testy** (90% úspěšnost): Funkčnost základních komponent
- **Integrační testy** (90% úspěšnost): Reálné scénáře
- **Funkční testy** (95% úspěšnost): End-to-end workflow
- **Zátěžové testy** (80% úspěšnost): Systémové limity

### Spuštění testů

```bash
# Všechny testy
python -m pytest tests/ -v
```

## 📄 Licence

Tento projekt je licencován pod licencí MIT - viz soubor [LICENSE](LICENSE) pro podrobnosti.

---

**Vytvořeno s ❤️ pro AI vývojářskou komunitu**

*Enhanced MyCoder v2.2.0 - Kde se AI setkává s teplotní zodpovědností*
