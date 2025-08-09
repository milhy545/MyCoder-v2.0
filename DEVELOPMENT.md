# 🚀 MyCoder Development Guide

Tento dokument popisuje jak efektivně vyvíjet MyCoder s live reload a bez neustálých rebuildů!

## 🎯 Quick Start

```bash
# Spuštění development prostředí
make dev

# Alternativně
docker-compose -f docker-compose.dev.yml up
```

**🔥 ŽIVÉ ZMĚNY** - jakákoliv úprava v `src/` se projeví okamžitě bez rebuildu!

## 📁 Struktura Development Setup

```
📦 MyCoder Development
├── 🐳 docker-compose.dev.yml    # Dev environment
├── 🐳 Dockerfile.dev            # Dev image s extra tools
├── 🚀 docker-entrypoint.dev.sh  # Dev startup script
├── 📋 Makefile                  # Snadné příkazy
├── 🔧 .env.dev                  # Dev konfigurace
└── 📚 DEVELOPMENT.md            # Tento guide
```

## 🔥 Live Reload Workflow

### 1️⃣ Spuštění Dev Prostředí
```bash
make dev
# nebo
docker-compose -f docker-compose.dev.yml up
```

### 2️⃣ Edit & Test (Bez Rebuildů!)
```bash
# Edit soubor
vim src/mycoder.py

# Změny se projeví OKAMŽITĚ! ⚡
# Žádný rebuild nutný!
```

### 3️⃣ Debugging
```bash
# Otevři shell v kontejneru
make dev-shell

# Python shell s načteným MyCoder
make dev-python

# Remote debugging (VS Code/PyCharm)
# Připoj na localhost:5678
```

### 4️⃣ Testing
```bash
# Spuštění testů
make test

# Rychlé testy
make test-quick

# Integration testy
make test-integration
```

## 🔧 Užitečné Příkazy

### Development
| Příkaz | Popis |
|--------|--------|
| `make dev` | 🚀 Spustí dev server s live reload |
| `make dev-shell` | 🐚 Shell v dev kontejneru |
| `make dev-python` | 🐍 Python shell s MyCoder |
| `make logs` | 📋 Zobraz logy |
| `make debug` | 🐛 Spustí s debugger portem |

### Testing & Quality
| Příkaz | Popis |
|--------|--------|
| `make test` | 🧪 Spustí všechny testy |
| `make test-quick` | ⚡ Rychlé testy |
| `make lint` | 📋 Code linting |
| `make format` | 🎨 Formátování kódu |

### Monitoring
| Příkaz | Popis |
|--------|--------|
| `make status` | 📊 Stav všech služeb |
| `make health` | 💓 Health check |
| `make dev-models` | 🤖 Dostupné modely |

### Control
| Příkaz | Popis |
|--------|--------|
| `make stop` | 🛑 Zastaví všechny služby |
| `make restart` | 🔄 Restart dev serveru |
| `make clean` | 🧹 Vyčisti Docker cache |

## 🎯 Development vs Production

### 🔥 Development Mode
- **Live reload** - změny okamžité
- **Debug tools** - debugpy, ipdb, profiling
- **Verbose logging** - DEBUG level
- **File watching** - automatické detekce změn
- **Hot restart** - rychlý restart služeb
- **Development dependencies** - pytest, black, flake8

### 🏭 Production Mode
- **Static image** - stabilní, nemění se
- **Optimalized** - rychlý start, malá velikost
- **Security** - minimální surface area
- **Resource efficient** - méně RAM/CPU
- **Monitoring ready** - health checks, metrics

## 📊 Live Reload Funguje Pro:

✅ **Python kód** (`src/*.py`)  
✅ **Konfigurace** (`.env`, `*.yaml`)  
✅ **Testy** (`tests/*.py`)  
✅ **Dokumentace** (`docs/*.md`)  
✅ **Příklady** (`examples/*.py`)  

❌ **Nepotřebuje rebuild:**
- Změny v source kódu
- Úprava konfigurace
- Nové soubory v mounted folders

🔨 **Potřebuje rebuild:**
- Nové Python balíčky (pyproject.toml)
- Změny Dockerfile.dev
- System dependencies

## 🐛 Debugging

### Remote Debugging (VS Code)
1. Spuštění s debug portem:
   ```bash
   make debug
   ```

2. VS Code launch.json:
   ```json
   {
     "name": "MyCoder Remote Debug",
     "type": "python",
     "request": "attach",
     "connect": {
       "host": "localhost",
       "port": 5678
     },
     "pathMappings": [
       {
         "localRoot": "${workspaceFolder}/src",
         "remoteRoot": "/app/src"
       }
     ]
   }
   ```

### Interactive Debugging
```python
# V kódu
import ipdb; ipdb.set_trace()

# Nebo
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()
```

### Log Debugging
```bash
# Sleduj logy live
make logs

# Jen Ollama logy
make logs-ollama

# Posledních 100 řádků
make dev-logs-tail
```

## 🚀 Optimalizace Performance

### Development Container
- **Bind mounts** místo COPY - okamžité změny
- **Cached dependencies** - Poetry cache
- **Lightweight base** - Python 3.11 slim
- **Smart layering** - rarery změny dole

### Live Reload Mechanismus
- **File watching** - inotify pro detekci změn
- **Hot restart** - jen Python proces, ne celý container
- **Smart mounting** - read-only pro kód, RW pro data
- **Volume optimization** - separátní volumes pro různé typy dat

## 🔍 Troubleshooting

### ❌ Live Reload Nefunguje
```bash
# Zkontroluj mounted volumes
docker-compose -f docker-compose.dev.yml config | grep -A5 volumes

# Restart file watcheru
make restart
```

### ❌ Ollama Není Dostupný
```bash
# Health check
make health

# Restart Ollama
make stop && make dev

# Manuální Ollama příkazy
make dev-shell
ollama list
ollama pull deepseek-coder:1.3b-base-q4_0
```

### ❌ Pomalé Buildy
```bash
# Používej development mode!
make dev  # Místo make prod

# Rebuild jen když je třeba
make dev-rebuild-quick

# Vyčisti cache
make clean
```

### ❌ Port Konflikty
```bash
# Zkontroluj porty
make ports

# Změň porty v docker-compose.dev.yml
ports:
  - "8001:8000"  # Místo 8000:8000
```

## 💡 Pro Tips

### 1️⃣ **Fast Iteration**
```bash
# Terminal 1: Dev server
make dev

# Terminal 2: Logs
make logs

# Terminal 3: Testing
make dev-shell
# Nebo průběžně
make test
```

### 2️⃣ **Debugging Session**
```bash
# Spuštění s debuggerem
make debug

# V kódu přidej breakpoint
import ipdb; ipdb.set_trace()

# Nebo remote debug z IDE
```

### 3️⃣ **Code Quality**
```bash
# Před commitem
make lint
make format
make test
```

### 4️⃣ **Performance Monitoring**
```bash
# Sleduj výkon
make health
make dev-models
make status
```

## 🎯 Development Checklist

### ✅ Před začátkem vývoje:
- [ ] `make dev` - spustí dev prostředí
- [ ] `make health` - zkontroluj zdraví služeb  
- [ ] `make dev-models` - potvrď dostupné modely
- [ ] `make test-quick` - základní test

### ✅ Během vývoje:
- [ ] Edit files in `src/` - live reload aktivní
- [ ] `make logs` - sleduj výstup
- [ ] `make test` - testuj změny
- [ ] `make lint` - kontroluj kvalitu kódu

### ✅ Před ukončením:
- [ ] `make test` - finální test
- [ ] `make format` - formátuj kód
- [ ] `make stop` - zastav služby
- [ ] Commit změny

## 🚀 Advanced Development

### Multi-Model Testing
```bash
# Test s různými modely
export MYCODER_LLM_MODEL=deepseek-coder:6.7b-instruct-q4_0
make restart

# Nebo
make dev-shell
ollama pull codellama:7b-instruct
# Edit .env.dev a restart
```

### Performance Profiling
```bash
# Aktivuj profiling
export ENABLE_PROFILING=true
make restart

# Sleduj performance
make logs | grep -i performance
```

### Custom Development Setup
```bash
# Vlastní dev konfigurace
cp .env.dev .env.dev.local
# Edit .env.dev.local
# Git ignoruje *.local soubory
```

---

## 🎉 Shrnutí

**Development s MyCoder = ŽÁDNÉ REBUILDY!** 🚀

1. **Spuštění**: `make dev`
2. **Editace**: Měň soubory v `src/`
3. **Testování**: `make test`  
4. **Debugging**: `make debug`
5. **Zastavení**: `make stop`

**Live reload = Okamžité změny = Rychlý vývoj!** ⚡

Pro help: `make help` nebo `make examples`