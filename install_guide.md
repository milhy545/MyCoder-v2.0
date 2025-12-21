# 🤖 MyCoder v2.0 - Instalační Návod

## 📋 Rychlá instalace (doporučeno)

```bash
# 1. Naklonuj MyCoder v2.0
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0

# 2. Nainstaluj Poetry (pokud nemáš)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Nainstaluj závislosti
poetry install

# 4. Aktivuj prostředí
poetry shell

# 5. Test instalace
python -c "from mycoder import MyCoder; print('✅ MyCoder v2.0 nainstalován!')"
```

## 🔧 Krok za krokem setup

### 1. Systémové požadavky
```bash
# Python 3.10-3.13
python3 --version

# Git
git --version

# Poetry (package manager)
poetry --version
```

### 2. Clone a setup
```bash
# Stáhni projekt
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0

# Nainstaluj závislosti (automaticky stáhne claude-cli-auth)
poetry install

# Vstup do virtual environment
poetry shell
```

### 3. Test základních funkcí
```bash
# Test importů
python -c "from mycoder import MyCoder, EnhancedMyCoder, AdaptiveModeManager; print('Imports OK')"

# Spusť demo
python test_integration.py

# CLI interface
mycoder --help
```

## 📱 Praktické použití

### Základní Python skript
```python
#!/usr/bin/env python3
import asyncio
from mycoder import MyCoder

async def main():
    # Inicializace
    mycoder = MyCoder()
    
    # Dotaz na kód
    result = await mycoder.process_request(
        "Vytvoř Python funkci pro parsování CSV souborů"
    )
    
    print("Odpověď:", result['content'])

if __name__ == "__main__":
    asyncio.run(main())
```

### CLI použití
```bash
# Spusť MyCoder CLI
mycoder

# Nebo přímo s dotazem
echo "Vytvoř hello world v Pythonu" | mycoder
```

## ⚙️ Konfigurace režimů

```python
from mycoder import AdaptiveModeManager, OperationalMode

# Ruční přepnutí režimu
manager = AdaptiveModeManager()
await manager.transition_to_mode(OperationalMode.AUTONOMOUS, "offline work")
```

## 🔍 Dostupné režimy

| Režim | Požadavky | Funkce |
|-------|-----------|--------|
| **FULL** | Internet + Claude + MCP | Všechny AI funkce |
| **DEGRADED** | Internet + Claude | Základní AI bez MCP |
| **AUTONOMOUS** | Pouze lokální | Templates + patterns |
| **RECOVERY** | Minimum | Error handling |

## 🚨 Troubleshooting

### Claude CLI není potřeba!
```bash
# MyCoder v2.0 funguje i bez Claude CLI
# V AUTONOMOUS režimu používá lokální templates
```

### Chyba při instalaci Poetry
```bash
# Ubuntu/Debian
sudo apt install python3-poetry

# macOS
brew install poetry

# Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python3 -
```

### Import errors
```bash
# Ujisti se, že jsi v poetry shell
poetry shell

# Nebo použij poetry run
poetry run python your_script.py
```

## 🎯 Hotové příklady

Ve složce najdeš:
- `test_integration.py` - Test všech funkcí
- `network_demo.py` - Demo adaptivních režimů  
- `generated_log_analyzer.py` - Příklad vygenerovaného kódu
- `sharp_test.py` - Ostrý test s reálným dotazem

## 💡 Pro vývojáře

```bash
# Development setup
git clone https://github.com/milhy545/MyCoder-v2.0.git
cd MyCoder-v2.0
poetry install --with dev

# Testy
poetry run pytest

# Linting
poetry run black src/
poetry run flake8 src/
```