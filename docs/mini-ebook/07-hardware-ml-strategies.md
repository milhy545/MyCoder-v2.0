# Kapitola 7: Hardware Strategie pro ML/LLM

## Úvod

Máte stack různého hardware - Raspberry Pi, starý PC s Q9550, možná PS4, možná Xbox. Jak to všechno efektivně využít pro Machine Learning a LLM inference? V této kapitole sestavíme praktické strategie pro různé scénáře a budgety.

---

## Hardware Inventory - Co máme k dispozici?

### Typický home lab setup

```
Dostupný hardware:
├─ Desktop PC (Q9550 @ 2.83GHz, 8GB RAM)
│  └─ Pros: 4 jádra, slušný výkon, low cost electricity
│
├─ Raspberry Pi 3B (1GB RAM)
│  └─ Pros: 5W spotřeba, always-on capable
│
├─ Raspberry Pi 4 (4GB RAM)
│  └─ Pros: 4× Cortex-A72, USB 3.0, Gigabit Ethernet
│
├─ PlayStation 4 (8-core Jaguar, 8GB GDDR5)
│  └─ Pros: Levný (used), decent CPU
│
├─ Xbox One (8-core Jaguar, 8GB DDR3)
│  └─ Pros: Velmi levný (used), dev mode
│
└─ Možný upgrade: GPU (RTX 3060, RX 6600, atd.)
   └─ Pros: MASSIVE performance boost pro ML
```

---

## Use Case #1: Personal AI Assistant (MyCoder-v2.0)

### Cíl
Běžící AI assistant s multi-provider fallback, dostupný 24/7, low cost.

### Optimální setup

```
┌─────────────────────────────────────────┐
│ Main Server: Q9550 Desktop PC          │
│                                         │
│ ├─ MyCoder-v2.0 API (Flask/FastAPI)    │
│ ├─ Provider Router                      │
│ │  ├─ Claude API (primary)             │
│ │  ├─ Gemini API (fallback)            │
│ │  └─ Ollama Local (offline fallback)  │
│ ├─ Ollama Server (Phi-3 Mini)          │
│ ├─ PostgreSQL (conversation history)   │
│ └─ Redis (cache)                        │
│                                         │
│ Performance:                            │
│ - API queries: <500ms                   │
│ - Ollama inference: ~30 tokens/s        │
│ - Power: ~95W                           │
│ - Uptime: 24/7                          │
└─────────────────────────────────────────┘
          ↓ HTTP API
┌─────────────────────────────────────────┐
│ Raspberry Pi 4: Dashboard Terminal      │
│                                         │
│ ├─ 7" Touchscreen display              │
│ ├─ Voice input (Whisper API)           │
│ ├─ TTS output                           │
│ └─ Web UI (React/Vue)                   │
│                                         │
│ Power: ~5W                              │
└─────────────────────────────────────────┘
          ↓ Sync
┌─────────────────────────────────────────┐
│ Mobile: Android App                     │
│                                         │
│ ├─ Voice dictation (local STT)         │
│ ├─ Text-to-Speech (local TTS)          │
│ ├─ Offline mode (Android SpeechRec)    │
│ └─ Sync with server (when online)      │
└─────────────────────────────────────────┘
```

**Proč tento setup:**

1. **Q9550 jako main server:**
   - ✅ Dost výkonu pro Phi-3 Mini (CPU only)
   - ✅ Lze běžet 24/7 (~$10-15/měsíc elektřina)
   - ✅ Thermal management už implementováno
   - ✅ Fallback když cloud API failne

2. **RPi 4 jako terminal:**
   - ✅ Low power (always-on displej = $1/měsíc)
   - ✅ Dedicated UI (nezdržuje main server)
   - ✅ Voice interface
   - ✅ Offload inference na server

3. **Mobile app:**
   - ✅ Portable
   - ✅ Offline capable
   - ✅ Best UX (už implementováno!)

**Cost breakdown:**
- Hardware: $0 (už máte)
- Electricity: ~$15/měsíc (Q9550 + RPi 4)
- Cloud API: ~$10-30/měsíc (Claude/Gemini jako primary)
- **Total: $25-45/měsíc**

---

## Use Case #2: Budget ML Learning Lab

### Cíl
Setup pro learning ML/LLM development, experimenty, prototyping.

### Optimální setup

**Option A: CPU-only (no budget)**

```
Raspberry Pi 4 (4GB) - $55
├─ OS: Raspberry Pi OS (64-bit)
├─ Python 3.11
├─ PyTorch (CPU-only build)
├─ Transformers library
├─ TinyLlama 1.1B (quantized 4-bit)
└─ Jupyter Notebook (remote access)

Capabilities:
- ✅ Train tiny models (<100M params)
- ✅ Fine-tune TinyLlama (slow but possible)
- ✅ Inference small models (1-2 tok/s)
- ✅ Learn ML concepts
- ❌ Train anything serious
```

**Hands-on projects:**
```python
# Project 1: Sentiment classifier
from transformers import pipeline
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased")
result = classifier("I love machine learning!")

# Project 2: Text generation
from transformers import AutoTokenizer, AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
# ... inference code

# Project 3: Fine-tuning
from transformers import TrainingArguments, Trainer
# Fine-tune on custom dataset (takes hours, but works!)
```

**Option B: Used GPU ($200 budget)**

```
Shopping list:
├─ Used GTX 1660 Super (6GB VRAM) - $120
├─ Or: Used RX 580 (8GB VRAM) - $100
└─ Install in Q9550 PC

Capabilities:
- ✅ Train medium models (up to 1B params)
- ✅ Fine-tune Phi-3 Mini (možné!)
- ✅ Inference: 40-60 tok/s (Phi-3)
- ✅ Run Stable Diffusion
- ✅ Learn CUDA/ROCm programming
```

**Why used GPU is worth it:**
```
CPU-only inference:    2-3 tok/s
GPU inference:         40-60 tok/s
Speedup:              20x faster!

Training time:
CPU: 48 hours
GPU: 2-3 hours
Speedup:              16-24x faster!
```

**Option C: Cloud GPU (pay-per-use)**

```
Providers:
├─ Google Colab (Free tier)
│  ├─ Tesla T4 (free, limited time)
│  ├─ 12GB RAM
│  └─ Good for learning
│
├─ Kaggle Notebooks (Free)
│  ├─ Tesla P100 (free!)
│  ├─ 16GB RAM
│  └─ 30h/week limit
│
├─ Paperspace Gradient (Free + paid)
│  ├─ Free: M4000 (8GB)
│  ├─ Paid: A4000, A100, atd.
│  └─ $0.45/hour (A4000)
│
└─ Vast.ai (cheapest)
   ├─ Rent GPUs from individuals
   ├─ RTX 3090: ~$0.30/hour
   └─ Good for heavy training
```

**Doporučení:**
- **Learning:** Colab/Kaggle free tier (nepotřebujete vlastní HW)
- **Prototyping:** Raspberry Pi 4 (hands-on, vždy dostupné)
- **Serious work:** Used GPU (best long-term value)

---

## Use Case #3: Home Media + Voice Assistant

### Cíl
Kombinace media center + AI assistant + smart home hub.

### Setup

```
┌─────────────────────────────────────────┐
│ Raspberry Pi 4 (4GB)                    │
│ Connected to TV (HDMI)                  │
│                                         │
│ Services:                               │
│ ├─ Kodi (media center)                  │
│ ├─ Home Assistant (smart home)         │
│ ├─ Voice assistant (Whisper + Ollama)  │
│ ├─ TTS engine                           │
│ └─ Web dashboard                        │
│                                         │
│ Workflow:                               │
│ "Hey Pi, play Breaking Bad"             │
│   → Whisper STT (offload na server)     │
│   → LLM parse intent (Phi-3)            │
│   → Kodi API call                       │
│   → TV starts playing                   │
└─────────────────────────────────────────┘
          ↑ Offload heavy tasks
┌─────────────────────────────────────────┐
│ Q9550 Server (background)               │
│                                         │
│ ├─ Whisper.cpp (STT server)            │
│ ├─ Ollama (Phi-3 Mini)                 │
│ └─ API endpoints                        │
└─────────────────────────────────────────┘
```

**Implementation:**

```python
# voice_assistant.py na RPi 4
import requests
import subprocess
import pyttsx3

def record_audio():
    """Record audio from USB mic"""
    subprocess.run(['arecord', '-d', '5', '-f', 'S16_LE', '-r', '16000', 'query.wav'])

def transcribe(audio_file):
    """Send to Whisper server"""
    with open(audio_file, 'rb') as f:
        response = requests.post('http://q9550-server:8080/whisper', files={'file': f})
    return response.json()['text']

def query_llm(text):
    """Send to Ollama server"""
    response = requests.post('http://q9550-server:11434/api/generate', json={
        'model': 'phi3:mini',
        'prompt': f'Parse this voice command and return JSON: {text}'
    })
    return response.json()

def execute_command(intent):
    """Execute based on parsed intent"""
    if intent['action'] == 'play':
        # Call Kodi API
        requests.post('http://localhost:8080/jsonrpc', json={
            'method': 'Player.Open',
            'params': {'item': {'title': intent['media']}}
        })

def speak(text):
    """Text-to-Speech"""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Main loop
while True:
    wait_for_wake_word()  # "Hey Pi"
    record_audio()
    text = transcribe('query.wav')
    intent = query_llm(text)
    execute_command(intent)
    speak("Done!")
```

**Proč tento setup:**
- ✅ RPi 4 = tichý, low power, always-on
- ✅ Q9550 = heavy lifting (Whisper, LLM)
- ✅ Distributed = každý dělá co umí nejlépe
- ✅ Cost effective (~$10/měsíc elektřina)

---

## Use Case #4: Gaming Console Repurposing

### Můžeme použít PS4/Xbox pro ML?

**Short answer: Technicky ano, prakticky ne.**

### PS4 Pro jako ML box

**Hardware:**
- CPU: 8× 2.1 GHz Jaguar
- RAM: 8 GB GDDR5
- GPU: 4.2 TFLOPS (ALE bez Linux driveru = useless)

**Pokud Linux + CPU-only:**

```bash
# Instalace Ollama na PS4 Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama pull tinyllama  # Phi-3 = příliš velký pro 7GB RAM

# Benchmark
time ollama run tinyllama "Hello world"
# Result: 0.8-1.2 tok/s (VELMI pomalé)
```

**Srovnání:**

| Hardware | Tokens/s | Power | Cost (used) |
|----------|----------|-------|-------------|
| PS4 Pro (CPU) | 1.0 | 120W | $200 |
| Q9550 (CPU) | 30 | 95W | $50 |
| RPi 4 (CPU) | 2.5 | 5W | $55 |
| RTX 3060 (GPU) | 100 | 170W | $250 |

**Verdict:**
- ❌ PS4 Pro je HORŠÍ než Q9550
- ❌ Více power consumption
- ❌ Hlučnější (fan noise)
- ❌ Složitější setup (Linux install)
- ✅ Jediná výhoda: GDDR5 RAM (ale nevyužitá bez GPU)

**Doporučení:** **NE**, nepoužívat PS4 pro ML. Lepší použít běžný PC nebo RPi 4.

---

### Xbox One (Developer Mode) jako ML box

**Developer Mode možnosti:**

```csharp
// UWP app - C# ML.NET
using Microsoft.ML;

var mlContext = new MLContext();
var model = mlContext.Model.Load("model.zip", out var schema);
var predictions = model.Transform(testData);

// ALE: Performance throttled, max 2GB RAM, no GPU access
```

**Benchmark (TinyLlama via Python UWP app):**
- Tokens/s: 0.5-0.8 (NEJPOMALEJŠÍ!)
- RAM limit: 2 GB (system kills app nad limitem)
- No GPU: Jen CPU
- Noise: 🔊🔊🔊 (fan 100%)

**Verdict:** ❌ Ještě horší než PS4. Totally impractical.

---

## Use Case #5: NAS + ML Combo Server

### Cíl
Centrální server pro storage + ML inference + home automation.

### Hardware

```
Shopping list (used market):
├─ Dell Optiplex 7050 (i5-7500, 16GB RAM) - $150
├─ 2× 4TB HDD (RAID 1 mirror) - $120
├─ Used GTX 1660 Super (6GB VRAM) - $120
└─ Total: ~$390

Nebo DIY build:
├─ Ryzen 5 3600 (6-core) - $100 used
├─ 16GB DDR4 RAM - $40 used
├─ B450 motherboard - $60 used
├─ 2× 4TB HDD - $120
├─ Used GPU (optional) - $120
└─ Total: ~$440
```

### Services Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # NAS - File sharing
  samba:
    image: dperson/samba
    ports:
      - "445:445"
    volumes:
      - /mnt/storage:/share

  # ML - Ollama server
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  # ML - Whisper API
  whisper:
    image: onerahmet/openai-whisper-asr-webservice
    ports:
      - "9000:9000"
    environment:
      - ASR_MODEL=base
      - ASR_ENGINE=faster_whisper

  # Home Automation
  homeassistant:
    image: homeassistant/home-assistant
    ports:
      - "8123:8123"
    volumes:
      - ha_config:/config

  # Dashboard
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"

  # Database
  postgres:
    image: postgres:15
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  ollama_data:
  ha_config:
  pg_data:
```

**Capabilities:**
- ✅ 8TB storage (RAID 1)
- ✅ ML inference (Phi-3, Whisper)
- ✅ Home automation hub
- ✅ Monitoring (Grafana)
- ✅ Database server
- ✅ 24/7 uptime
- ✅ Low noise (tower case + Noctua fans)

**Power consumption:**
- Idle: 40W
- Load: 120W (s GPU)
- Cost: ~$15-20/měsíc

---

## Cost-Benefit Analysis

### Scenario 1: Pure Cloud (no local hardware)

```
Monthly costs:
├─ ChatGPT Plus (GPT-4): $20
├─ Claude Pro: $20
├─ Google Colab Pro: $10
├─ Whisper API (1h/day): $6
└─ Total: $56/měsíc = $672/rok

Pros:
✅ Zero upfront cost
✅ Zero maintenance
✅ Always latest models
✅ Unlimited scaling

Cons:
❌ Vendor lock-in
❌ No privacy (data v cloudu)
❌ Offline = nefunguje
❌ Cumulative cost (3 roky = $2000+)
```

---

### Scenario 2: Hybrid (cloud + local)

```
Upfront:
├─ Q9550 PC: $50 (už máte)
├─ Used GPU (GTX 1660S): $120
└─ Total: $170

Monthly:
├─ Electricity (Q9550 + GPU): $18
├─ Claude API (occasional): $5
└─ Total: $23/měsíc = $276/rok

Year 1: $170 + $276 = $446
Year 2: $276
Year 3: $276
3-year total: $998

Pros:
✅ Privacy (local inference)
✅ Offline capable
✅ Own your setup
✅ Learning opportunities
✅ Cheaper long-term (3 roky)

Cons:
⚠️ Maintenance required
⚠️ Upfront cost
⚠️ Local models < GPT-4 quality
```

**Break-even point:** 18 měsíců

---

### Scenario 3: Pure Local (full DIY)

```
Upfront:
├─ Used workstation: $300
├─ Used GPU (RTX 3060): $250
├─ 32GB RAM upgrade: $80
└─ Total: $630

Monthly:
├─ Electricity (150W avg): $22
└─ Total: $22/měsíc = $264/rok

Year 1: $630 + $264 = $894
Year 2: $264
Year 3: $264
3-year total: $1422

Pros:
✅ 100% privacy
✅ Fully offline
✅ Best performance/$ long-term
✅ No vendor lock-in
✅ Resale value (HW má value)

Cons:
❌ Highest upfront cost
❌ Most maintenance
❌ Local models ≠ GPT-4
❌ Requires technical skills
```

**Break-even vs cloud:** 2 roky

**Break-even vs hybrid:** Never (ale benefits jsou greater)

---

## Doporučení pro různé profily

### 1. Casual User (občasné použití)

**Profil:**
- Používá AI 1-2x týdně
- Hlavně simple queries
- Nepotřebuje privacy
- Technicky ne-savvy

**Doporučení:**
```
→ ChatGPT Free tier
→ Claude.ai Free tier
→ Google Gemini Free

Cost: $0/měsíc
Effort: Minimal
```

---

### 2. Power User (denní použití)

**Profil:**
- Používá AI každý den
- Coding, writing, research
- Chce best quality
- Budget $20-50/měsíc OK

**Doporučení:**
```
→ ChatGPT Plus ($20)
→ Nebo Claude Pro ($20)
→ Plus: Local Ollama (fallback)

Setup:
├─ Cloud pro critical work
└─ Local pro experimenty

Cost: $20-25/měsíc
```

---

### 3. Developer/Tinkerer (learning ML)

**Profil:**
- Chce se naučit ML/LLM
- Experimentuje s modely
- Budget hardware OK
- Technical skills ✅

**Doporučení:**
```
→ Raspberry Pi 4 nebo used PC
→ + Used GPU ($100-200)
→ Self-hosted Ollama
→ Cloud pouze for heavy training

Setup:
├─ Local: Learning, prototyping
├─ Colab/Kaggle: Heavy training
└─ Prod: Hybrid (local + API fallback)

Upfront: $200-400
Monthly: $15-20
```

---

### 4. Privacy-Conscious (data security)

**Profil:**
- Nepůjčí data cloud providers
- Legal/medical/sensitive work
- Budget není limit
- Technical capable

**Doporučení:**
```
→ Full self-hosted stack
→ Workstation + GPU
→ Air-gapped možné
→ Zero cloud dependency

Hardware:
├─ Workstation: $300-500
├─ GPU (RTX 3060 Ti): $300
├─ Storage: $100-200
└─ Total: $700-1000

Monthly: $20-30 (elektřina)
```

---

### 5. Enthusiast/Home Lab

**Profil:**
- Baví ho tech projekty
- Chce comprehensive setup
- Budget: flexible
- Skill: expert

**Doporučení:**
```
→ Full home lab setup
→ NAS + ML + automation
→ Multiple services
→ Raspberry Pi cluster (možná)

Hardware:
├─ Main server (Ryzen + GPU): $600
├─ NAS drives: $200
├─ RPi 4 (dashboard): $55
├─ Network upgrades: $100
└─ Total: ~$1000

Monthly: $30-40

Benefits:
✅ Complete control
✅ Learning platform
✅ Bragging rights 😄
```

---

## Raspberry Pi Cluster - Je to worth it?

### Concept

```
4× Raspberry Pi 4 (4GB) Cluster
├─ Kubernetes (K3s)
├─ Load balanced services
├─ Distributed ML training (možná?)
└─ Cost: 4 × $55 = $220

Vs.

1× Used Workstation
├─ i5-6500 (4-core @ 3.2GHz)
├─ 16GB RAM
├─ Podobný CPU power
└─ Cost: $150
```

**Benchmark comparison:**

| Task | 4× RPi 4 | i5 Workstation |
|------|----------|----------------|
| Ollama (Phi-3) | 8-10 tok/s | 25-30 tok/s |
| Whisper (base) | 2x realtime | 8x realtime |
| Docker services | Good | Better |
| Power | 20W | 65W |
| **Cost** | **$220** | **$150** |

**Verdict:**
- ❌ RPi cluster: Cool project, ALE worse value/$
- ✅ Workstation: Better performance/cost
- ✅ RPi cluster IF: Learning Kubernetes, distributed systems

**Důvod proč cluster:**
- Learning platform (Kubernetes, Docker Swarm)
- Fun project (looks cool!)
- Redundancy (1 node fail = cluster runs)

**Důvod proč NE cluster:**
- Worse performance/$
- More complexity
- ARM architecture (some software incompatible)

---

## Final Recommendations

### Optimal Setups (2025)

**Budget Tier ($0-100):**
```
Hardware:
├─ Raspberry Pi 4 (4GB) - $55
├─ Or: Used thin client - $50-80
└─ Or: Cloud free tiers - $0

Use: Learning, light inference, dashboard
Performance: 2-3 tok/s (CPU only)
```

**Value Tier ($100-300):**
```
Hardware:
├─ Used PC (i5 gen 6-7) - $100-150
├─ + Used GPU (GTX 1660/RX 580) - $100-120
└─ Total: $200-270

Use: Serious ML work, training, inference
Performance: 40-60 tok/s
Best bang-for-buck!
```

**Enthusiast Tier ($300-600):**
```
Hardware:
├─ Workstation (Ryzen 5 5600) - $200
├─ 32GB RAM - $80
├─ RTX 3060 (12GB) - $280
├─ NVMe SSD - $40
└─ Total: $600

Use: Full home lab, NAS, automation
Performance: 80-100 tok/s
Future-proof
```

**Pro Tier ($600+):**
```
Hardware:
├─ Ryzen 7 5800X3D - $300
├─ 64GB RAM - $160
├─ RTX 4070 Ti nebo RX 7900 XT - $600-700
├─ Enterprise NVMe - $100
└─ Total: $1160+

Use: Production workloads, business
Performance: 120-150 tok/s
Commercial viable
```

---

## Závěr

**Key Takeaways:**

1. **Don't buy PS4/Xbox for ML** - Worse than used PCs
2. **Used GPU = best upgrade** - 20-30x speedup
3. **Cloud has place** - Prototyping, occasional heavy tasks
4. **Hybrid approach wins** - Local + cloud fallback
5. **Raspberry Pi** - Great for dashboards, not for ML
6. **Q9550 is OK** - For CPU inference, but upgrade path exists

**Golden rule:**
> "Right tool for right job. Mix and match based on your use case."

**My personal setup:**
```
├─ Q9550 server (MyCoder API + Ollama)
├─ RPi 4 (dashboard + voice terminal)
├─ Android phone (mobile client)
├─ Cloud APIs (critical tasks)
└─ Future: Used RTX 3060 ($250)
```

**Total cost:** ~$350 hardware + $20/měsíc

**Result:** Full-featured AI assistant, self-hosted, privacy-respecting, offline-capable. 🎉

---

**Konec knihy!** 📚

Doufám že tyto poznámky byly užitečné. Happy hacking! 🔧🤖

---

**Appendix: Další zdroje**

- **Hardware:**
  - r/homelab (Reddit community)
  - r/selfhosted (self-hosting resources)
  - ServeTheHome (server hardware reviews)

- **Software:**
  - Ollama: https://ollama.com
  - Whisper.cpp: https://github.com/ggerganov/whisper.cpp
  - HuggingFace: https://huggingface.co

- **Learning:**
  - Fast.ai (free ML course)
  - Andrej Karpathy's lectures
  - Papers With Code

**Stay curious. Keep learning. Fight corporate svinárny.** 🚀
