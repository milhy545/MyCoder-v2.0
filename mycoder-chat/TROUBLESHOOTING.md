# Troubleshooting Guide

## 🔍 Common Issues

### 1. Backend Won't Start

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

---

**Error:**
```
Address already in use: 8000
```

**Solution:**
```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

### 2. HAS Connection Issues

**Error:**
```
❌ Nelze se připojit k HAS
```

**Debug Steps:**

1. **Check HAS is running:**
```bash
ssh user@has-server
docker ps | grep coordinator
```

2. **Test HAS endpoint:**
```bash
curl http://192.168.0.58:8020/health
```

3. **Check network:**
```bash
ping 192.168.0.58
traceroute 192.168.0.58
```

4. **Check firewall:**
```bash
# On HAS server
sudo ufw status
sudo ufw allow 8020/tcp
```

5. **Check HAS logs:**
```bash
docker logs mega-coordinator
```

---

### 3. WebSocket Disconnects

**Symptom:** Chat disconnects frequently

**Solutions:**

1. **Increase timeout in `main.py`:**
```python
async with httpx.AsyncClient(timeout=120.0) as client:  # Increase from 60
```

2. **Check reverse proxy (if using nginx):**
```nginx
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

3. **Browser console check:**
Press F12 → Console → look for errors

---

### 4. Routing Incorrect

**Symptom:** "Refactor code" goes to research instead of filesystem

**Debug:**

```bash
curl http://localhost:8000/debug/routing/Refactor%20code
```

Check which patterns matched. If wrong, adjust in `router.py`.

---

### 5. Tests Failing

**Error:**
```
ImportError: cannot import name 'MiniOrchestrator'
```

**Solution:**
```bash
# Make sure you're in backend directory
cd backend
export PYTHONPATH=.
pytest -v
```

---

## 🐛 Debug Checklist

When something breaks:

- [ ] Check logs: `tail -f mycoder_chat.log`
- [ ] Test HAS connection: `curl http://HAS:8020/health`
- [ ] Test LLM Server: `curl http://LLM:8000/health`
- [ ] Browser console (F12) for frontend errors
- [ ] Docker logs: `docker logs mycoder-chat`
- [ ] Restart everything: `docker-compose restart`

---

## 📊 Performance Issues

### Slow Response Times

1. **Check HAS load:**
```bash
ssh user@has
top
docker stats
```

2. **Check network latency:**
```bash
ping -c 10 192.168.0.58
```

3. **Enable timing logs:**
In `main.py`, use `@timing_decorator`:
```python
from debug_utils import timing_decorator

@timing_decorator
async def call_has(message, routing):
    # ...
```

---

## 🔒 Security Checks

### Exposed Debug Endpoints

**Problem:** Debug endpoints accessible in production

**Fix:**

Add to `main.py`:
```python
import os

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

if DEBUG_MODE:
    @app.get("/debug/routing/{message}")
    async def debug_routing(message: str):
        # ...
```

Then in production:
```bash
export DEBUG_MODE=false
```

---

## 📞 Getting Help

1. **Collect diagnostic info:**
```bash
curl http://localhost:8000/health > health.json
curl http://localhost:8000/debug/stats > stats.json
tail -100 mycoder_chat.log > recent_logs.txt
```

2. **Create issue with:**
- Error message
- Steps to reproduce
- Diagnostic files above
- Your environment (OS, Python version, Docker version)
