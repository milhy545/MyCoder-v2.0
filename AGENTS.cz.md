# Pokyny pro agenty a kontext projektu

**Poznámka:** Tento soubor je hlavním zdrojem pravdy pro všechny AI agenty (Claude Code, Jules/Gemini, Codex) pracující na tomto projektu. Definuje architekturu projektu, konvence a provozní protokoly.

## Nedávné změny a aktualizace
- 2026-03-11: Jules - Oprava bezpečnostních hlášení CodeQL odebráním nepoužívaných importů `Mock` z `tests/unit/test_tool_registry.py` a `subprocess` z `src/mycoder/providers/llm/ollama.py`; spuštěné testy: `poetry run flake8`, `poetry run mypy`, `poetry run pytest`.
*Agenti: Zde přidávejte záznamy při provádění významných změn*
- 2026-01-30: Codex - Opraveny CodeQL alerty (nepoužité importy, smíšené návraty, nedosažitelný kód, guard proti nevolatelnému objektu) a upraveny testy; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-30: Codex - Zpřísněny kontroly instancování OverlayButton kvůli CodeQL; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-30: Codex - Přesun OverlayApp pod PyQt guard a přidána tovární funkce pro CodeQL; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-30: Codex - Refaktorován OverlayButton na jednotnou implementaci aliasu kvůli CodeQL; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-30: Codex - Odstraněna podmíněná definice OverlayButton a přidány runtime PyQt guardy; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-30: Codex - Přidán CodeQL suppression na volání OverlayButton po falešném pozitivu; testy: `poetry run pytest tests/unit/ -v`, `poetry run pytest tests/providers/ -v`.
- 2026-01-23: Jules - Aktualizován systémový prompt `src/mycoder/triage_agent.py` pro soulad s "Principem zvracející kozy" v2 a vynucení striktního JSONu; testy: `poetry run pytest tests/unit/test_triage_agent.py`.
- 2026-01-23: Jules - Aktualizován `src/mycoder/triage_agent.py` pro použití nového formátu promptu, odstraněna konfliktní instrukce pro generování shell příkazů pro zajištění striktního JSON výstupu; testy: `poetry run pytest tests/unit/test_triage_agent.py`.
- 2026-01-21: Jules - Aktualizován systémový prompt `src/mycoder/triage_agent.py` pro soulad s "Principem zvracející kozy" v2 a vylepšena striktnost JSON; testy: `poetry run pytest tests/unit/test_triage_agent.py`.

## 🌍 Přehled projektu

**Enhanced MyCoder v2.2.0** je kriticky důležitý AI vývojářský asistent navržený pro **vysokou dostupnost**, **teplotní bezpečnost** (Intel Q9550) a **odolnost díky více poskytovatelům**.

### Hlavní mise
Poskytovat robustního, modulárního a teplotně uvědomělého kódovacího asistenta, který může fungovat autonomně nebo interaktivně, využívat nejlepší dostupné AI modely a zároveň chránit hardware a respektovat limity API.

## 🏗️ Architektonické standardy

### 1. Modulární systém poskytovatelů (`src/mycoder/providers/`)
- Všechny interakce s AI MUSÍ jít přes `APIProviderRouter`.
- **LLM Poskytovatelé:** Implementují `BaseAPIProvider`. Umístění: `src/mycoder/providers/llm/`.
- **TTS Poskytovatelé:** Implementují `BaseTTSProvider`. Umístění: `src/mycoder/providers/tts/`.
- **STT Poskytovatelé:** Implementují `BaseSTTProvider`. Umístění: `src/mycoder/providers/stt/`.
- **Omezení rychlosti (Rate Limiting):** PŘÍSNĚ dodržujte limity (zejména pro Google Gemini: 15 RPM, 1500 RPD) pomocí `PersistentRateLimiter`. NEVYTVÁŘEJTE hardcoded volání, která toto obcházejí.

### 2. Řízení teploty (`src/mycoder/adaptive_modes.py`)
- Systém běží na procesoru **Q9550**, který je citlivý na teplotu.
- **NIKDY** nevypínejte teplotní kontroly v produkčním kódu (pouze ve specifických testech s explicitními markery).
- Respektujte `MYCODER_THERMAL_MAX_TEMP` (výchozí 75°C).

### 3. Operace se soubory
- **VŽDY** používejte `tool_registry` pro operace se soubory.
- **NIKDY** nepřepisujte soubory naslepo. Použijte `file_read` nejprve, poté `file_edit` (vyhledat a nahradit) nebo `file_write` (pokud je nový).
- **Bezpečnost:** Respektujte omezení `FileSecurityManager` (povolený aktuální adresář).

## 🛠️ Vývojové protokoly

### Testování (POVINNÉ)
Před označením jakéhokoli úkolu za dokončený **MUSÍTE** spustit testy.
```bash
# Spuštění všech relevantních testů
poetry run pytest tests/unit/ -v
poetry run pytest tests/providers/ -v
```
- **Pokrytí:** Cílem je 100% pokrytí u nových funkcí.
- **Mockování:** Ve unit testech mockujte všechna externí API volání.

### Závislosti
- Pro správu závislostí používejte **Poetry**.
- Pokud přidáte závislost, aktualizujte `pyproject.toml` a spusťte `poetry lock`.

### Dokumentace
- Udržujte **Anglickou** (`*.md`) a **Českou** (`*.cz.md`) dokumentaci vedle sebe.
- Aktualizujte `README.md` a `README.cz.md` pro změny viditelné uživatelem.
- Aktualizujte `AGENTS.md` (tento soubor) pro změny týkající se vývojářů.

## 🤖 Pokyny pro interakci

### Komunikace s uživatelem
- **Jazyk:** Odpovídejte **česky** (pokud není uvedeno jinak).
- **Tón:** Profesionální, nápomocný, technický, ale přístupný.
- **Formátování:** Pro kód používejte Markdown bloky kódu.

### Zpracování chyb
- **Elegantní degradace (Graceful Degradation):** Pokud poskytovatel selže, router by měl automaticky přejít na záložní řešení.
- **Upozornění uživatele:** Informujte uživatele, pokud dojde k přepnutí na záložní řešení nebo pokud je funkčnost omezena (např. "Přepínám na Ollama z důvodu chyby sítě").

## 📂 Klíčové adresáře
- `src/mycoder/providers/`: Implementace AI služeb.
- `src/mycoder/agents/`: Autonomní agenti (Plan, Explore, Bash).
- `src/speech_recognition/`: Hlasové funkce (STT/TTS/Diktování).
- `tests/`: Komplexní testovací sada.

---
*Poslední aktualizace: 2026-01-21 Agentem Codex (nahrazení shell=True spuštění příkazů, přechod na sha256 pro cache klíče ve web_tools; testy pytest unit/providers).*
