# MyCoder Chat Interface - J.A.R.V.I.S.

Lightweight chat interface s mini-orchestrací pro routing na HAS a LLM Server.

## 🎯 Co to dělá?

- **Unified Chat Interface** - Jeden chat pro všechny AI služby
- **Smart Routing** - Automaticky určí kam poslat request (HAS vs LLM Server)
- **Mode Detection** - Detekuje typ úkolu (code, research, translate, memory...)
- **Real-time WebSocket** - Okamžité odpovědi bez refreshe

## 🏗️ Architektura

```
User → Chat UI (WebSocket) → Mini-Orchestrator → HAS/LLM Server
```

### Routing Logic

| User Intent | Target | Service | Model |
|:-----------|:-------|:--------|:------|
| Code tasks | HAS | filesystem-mcp | Claude |
| Research | HAS | research-mcp | GPT-4 |
| Memory search | HAS | cldmemory-mcp | - |
| Transcription | LLM Server | transcriber-mcp | Whisper |
| Translation | LLM Server | translation | Local/GPT-4 |
| Home automation | HAS | home-assistant | - |
| General chat | HAS | zen-coordinator | Auto |

## 🚀 Quick Start

### 1. Instalace

```bash
git clone <repo>
cd mycoder-chat
cd backend
pip install -r requirements.txt
```

### 2. Konfigurace

Uprav `backend/main.py`:

```python
HAS_URL = "http://192.168.0.58:8020"  # <-- TVÁ HAS IP!
LLM_SERVER_URL = "http://llm-server:8000"
```

### 3. Spuštění

```bash
python main.py
```

Otevři: **http://localhost:8000**

### 4. Docker Deployment

```bash
docker-compose up -d
```

Přístup: **http://localhost:8080**

## 🧪 Testování

```bash
# Unit testy
pytest tests/test_router.py -v

# Integration testy
pytest tests/test_api.py -v

# Všechny testy
pytest -v

# S coverage
pytest --cov=. --cov-report=html
```

## 🐛 Debug Mode

### Debug Endpoints

- `GET /debug/routing/{message}` - Test routing pro zprávu
- `GET /debug/logs?lines=100` - Posledních N řádků logu
- `GET /debug/stats` - Statistiky
- `POST /debug/test-has` - Test HAS spojení
- `POST /debug/test-llm-server` - Test LLM Server spojení

### Příklad:

```bash
curl http://localhost:8000/debug/routing/Refactor%20auth.py
```

Response:
```json
{
  "message": "Refactor auth.py",
  "routing_decision": {
    "target": "has",
    "service": "filesystem-mcp",
    "mode": "refactor",
    "model": "claude"
  },
  "patterns_matched": {
    "code": ["\\b(refactor|code|function|...)", "\\.py\\b"]
  }
}
```

## 📊 Logování

Logy se ukládají do `mycoder_chat.log`:

```bash
# Sledování logů real-time
tail -f mycoder_chat.log

# Vyhledání chyb
grep ERROR mycoder_chat.log
```

## 🔧 Troubleshooting

### Problem: Cannot connect to HAS

**Symptom:**
```
❌ Nelze se připojit k HAS (http://192.168.0.58:8020)
```

**Fix:**
1. Zkontroluj že HAS běží: `docker ps | grep mega-coordinator`
2. Ping HAS: `ping 192.168.0.58`
3. Test portu: `curl http://192.168.0.58:8020/health`
4. Zkontroluj firewall

Více v [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📝 Přidání Nového Routing Patternu

**Příklad**: Přidat support pro Docker úkoly

1. Otevři `backend/router.py`
2. Přidej pattern:

```python
PATTERNS = {
    # ... existing patterns ...
    'docker': [
        r'\b(docker|container|image|dockerfile)\b',
        r'\b(build|run|stop|ps|logs)\b.*container'
    ]
}
```

3. Přidej routing logiku:

```python
if self._match_patterns(msg_lower, self.PATTERNS['docker']):
    return {
        'target': 'has',
        'service': 'terminal-mcp',
        'mode': 'command',
        'model': 'gpt4'
    }
```

4. Test:
```bash
pytest tests/test_router.py -v -k docker
```

## 🔐 Security Best Practices

- ❌ **NIKDY** necommituj API keys do Gitu
- ✅ Používej environment variables
- ✅ HTTPS v produkci
- ✅ Rate limiting na WebSocket
- ✅ Input validation

## 📦 Deployment Checklist

- [ ] HAS_URL správně nastavená
- [ ] LLM_SERVER_URL správně nastavená
- [ ] Všechny testy procházejí (`pytest -v`)
- [ ] Debug endpoints vypnuté v produkci
- [ ] Logování nastaveno (file rotation)
- [ ] Firewall rules configured
- [ ] Monitoring enabled (Prometheus)
- [ ] Backups configured

## 📄 License

MIT
