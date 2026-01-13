# Kapitola 3: MicroLLM Modely

## Úvod

MicroLLM jsou malé jazykové modely (<3B parametrů) optimalizované pro běh na edge zařízeních - telefony, Raspberry Pi, embedded systémy. V této kapitole probereme nejlepší modely, benchmarky a praktické nasazení.

---

## Co jsou MicroLLM?

### Definice

**MicroLLM** = Language Model s <3B parametry, který:
- Běží na CPU (bez GPU)
- Vejde se do <2GB RAM
- Inference <1s na consumer hardware
- Dostatečná kvalita pro specifické úlohy

### Srovnání velikostí

| Kategorie | Parametry | VRAM | Příklad |
|-----------|-----------|------|---------|
| Tiny | <500M | <512MB | MobileLLM-125M |
| Small | 500M-1B | 512MB-1GB | TinyLlama-1.1B |
| **Micro** | **1B-3B** | **1-2GB** | **Phi-3-mini-3.8B** |
| Medium | 3B-10B | 2-8GB | Llama-3.2-8B |
| Large | 10B-30B | 8-24GB | Llama-3.1-13B |
| XL | 30B+ | 24GB+ | Claude, GPT-4 |

---

## Top MicroLLM modely (2024-2025)

### 1. Microsoft Phi-3 Mini (3.8B)

**Specifikace:**
- Parametry: 3.8B
- Context: 4K (extended: 128K)
- Quantization: 4-bit, 8-bit, FP16
- Licence: MIT (commercial use OK)
- Trénink: High-quality synthetic data

**Benchmark výsledky:**

| Task | Phi-3 Mini | Llama-3-8B | GPT-3.5 |
|------|------------|------------|---------|
| MMLU | 68.8% | 65.2% | 70.0% |
| HumanEval (coding) | 58.5% | 62.2% | 48.1% |
| Math (GSM8K) | 82.5% | 79.6% | 57.1% |
| Common sense | 75.4% | 72.9% | 78.2% |

**Závěr:** Phi-3 Mini překonává 2-3x větší modely! 🤯

**Inference speed:**

| Hardware | Quantization | Tokens/s | RAM usage |
|----------|--------------|----------|-----------|
| RPi 4 (4GB) | 4-bit | 2-3 tok/s | 1.2 GB |
| Intel i7-9700K | 8-bit | 25-30 tok/s | 2.8 GB |
| Apple M1 | FP16 | 40-50 tok/s | 7.6 GB |
| RTX 3060 | FP16 | 80-100 tok/s | 7.6 GB |

**⚠️ Raspberry Pi 3B (1GB RAM):**
- Teoreticky možné s 4-bit quantization
- Reálně: **SWAP hell** - super pomalé
- Doporučení: **NE**, příliš málo RAM

**Použití:**

```python
# Ollama
ollama pull phi3:mini
ollama run phi3:mini "Explain quantum computing in Czech"

# llama.cpp
./main -m phi-3-mini-4k-q4_0.gguf -p "Vysvětli kvantové počítání" -n 512
```

**Best for:**
- ✅ Coding assistance
- ✅ Math reasoning
- ✅ Q&A systems
- ✅ Instruction following
- ❌ Creative writing (suchopárný)
- ❌ Long context (4K base)

---

### 2. Google Gemma 2B

**Specifikace:**
- Parametry: 2B (také 7B variant)
- Context: 8K
- Quantization: 4-bit, 8-bit, FP16
- Licence: **Gemma Terms of Use** (commercial OK s podmínkami)
- Trénink: Google's proprietary data

**Benchmark:**

| Task | Gemma-2B | Phi-3 Mini | TinyLlama |
|------|----------|------------|-----------|
| MMLU | 41.8% | 68.8% | 25.3% |
| HumanEval | 22.0% | 58.5% | 11.8% |
| Czech quality | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

**Závěr:** Gemma-2B je slabší než Phi-3, ale má lepší creative writing.

**Inference speed:**

| Hardware | Tokens/s | RAM |
|----------|----------|-----|
| RPi 4 (4GB) | 4-5 tok/s (4-bit) | 800 MB |
| Intel i7 | 35-40 tok/s (8-bit) | 1.5 GB |
| RTX 3060 | 120-150 tok/s (FP16) | 4.2 GB |

**Použití:**

```python
# Ollama
ollama pull gemma:2b
ollama run gemma:2b

# Transformers (Python)
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2b",
    load_in_4bit=True  # 4-bit quantization
)

inputs = tokenizer("Napiš krátkou povídku o robotovi", return_tensors="pt")
outputs = model.generate(**inputs, max_length=200)
print(tokenizer.decode(outputs[0]))
```

**Best for:**
- ✅ Creative writing
- ✅ Chatbots
- ✅ Summarization
- ❌ Math reasoning
- ❌ Code generation

---

### 3. TinyLlama 1.1B

**Specifikace:**
- Parametry: 1.1B
- Context: 2K
- Quantization: 4-bit, 8-bit
- Licence: Apache 2.0 (fully open)
- Trénink: 3 trillion tokens, Llama architecture

**Benchmark:**
- MMLU: 25.3%
- Coding: Slabé (11.8% HumanEval)
- Czech: Funguje, ale s chybami

**Inference speed:**

| Hardware | Tokens/s | RAM |
|----------|----------|-----|
| **RPi 3B (1GB)** | **1-2 tok/s (4-bit)** | **500 MB** |
| RPi 4 (4GB) | 6-8 tok/s | 500 MB |
| Intel i7 | 50-60 tok/s | 800 MB |

**⭐ Jediný model, který reálně běží na RPi 3B!**

**Použití:**

```bash
# llama.cpp (nejrychlejší pro embedded)
./main -m tinyllama-1.1b-chat-v1.0-q4_0.gguf -p "Ahoj, jak se máš?" -n 128

# Ollama
ollama pull tinyllama
ollama run tinyllama
```

**Best for:**
- ✅ Simple Q&A
- ✅ Text completion
- ✅ Embedded systems (RPi 3B!)
- ✅ Learning/experimentation
- ❌ Complex reasoning
- ❌ Professional use

---

### 4. Qwen2-0.5B (Alibaba)

**Specifikace:**
- Parametry: 0.5B (také 1.5B, 7B variants)
- Context: 32K (!)
- Quantization: 4-bit, 8-bit
- Licence: Apache 2.0
- Multilingual: 27 jazyků včetně češtiny

**Benchmark:**
- MMLU: ~38% (0.5B variant)
- Long context: Excelentní (32K)
- Czech quality: ⭐⭐⭐

**Inference speed:**

| Hardware | Tokens/s | RAM |
|----------|----------|-----|
| RPi 3B (1GB) | 3-4 tok/s (4-bit) | 400 MB |
| RPi 4 | 10-12 tok/s | 400 MB |
| Intel i7 | 70-80 tok/s | 600 MB |

**Použití:**

```python
# Transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2-0.5B-Instruct",
    load_in_4bit=True
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-0.5B-Instruct")

prompt = "Vysvětli rozdíl mezi RAM a ROM"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0]))
```

**Best for:**
- ✅ Long context tasks
- ✅ Multilingual applications
- ✅ Ultra low-resource devices
- ✅ Edge AI
- ❌ Complex reasoning
- ❌ Code generation

---

### 5. StableLM-Zephyr 3B

**Specifikace:**
- Parametry: 3B
- Context: 4K
- Quantization: Všechny běžné
- Licence: Apache 2.0
- Fine-tuned for instruction following

**Benchmark:**
- MMLU: 45.2%
- Instruction following: ⭐⭐⭐⭐
- Czech: ⭐⭐⭐

**Inference speed:**

| Hardware | Tokens/s | RAM |
|----------|----------|-----|
| RPi 4 (4GB) | 3-4 tok/s (4-bit) | 1.1 GB |
| Intel i7 | 30-35 tok/s | 2.2 GB |
| RTX 3060 | 90-110 tok/s | 6 GB |

**Použití:**

```bash
ollama pull stablelm-zephyr:3b
ollama run stablelm-zephyr:3b
```

**Best for:**
- ✅ Instruction following
- ✅ Task automation
- ✅ API assistants
- ❌ Math
- ❌ Coding

---

### 6. MobileLLM (Meta Research)

**Specifikace:**
- Parametry: 125M, 350M variants
- Context: 2K
- **Ultra lightweight** - běží na telefonu
- Licence: MIT
- Optimalizováno pro mobile inference

**Benchmark:**
- MMLU: 18.5% (125M)
- Velmi rychlý, ale slabý

**Inference speed:**

| Hardware | Tokens/s | RAM |
|----------|----------|-----|
| Android phone | 20-30 tok/s | 150 MB |
| RPi 3B | 15-20 tok/s | 120 MB |
| RPi 4 | 30-40 tok/s | 120 MB |

**Použití:**

```kotlin
// Android app - direct model loading
import com.facebook.mobilellm.MobileLLM

val model = MobileLLM.load("mobilellm-125m.bin")
val response = model.generate("Hello, how are you?")
```

**Best for:**
- ✅ On-device mobile AI
- ✅ Ultra low-power devices
- ✅ Simple completions
- ❌ Anything complex
- ❌ Professional use

---

## Srovnání modelů - Tabulka

| Model | Params | RAM (4-bit) | RPi 3B? | RPi 4? | Quality | Speed | Best Use |
|-------|--------|-------------|---------|--------|---------|-------|----------|
| **Phi-3 Mini** | 3.8B | 1.2 GB | ❌ | ✅ | ⭐⭐⭐⭐⭐ | Medium | Coding, Math |
| **Gemma 2B** | 2B | 800 MB | ❌ | ✅ | ⭐⭐⭐⭐ | Fast | Creative |
| **TinyLlama** | 1.1B | 500 MB | ✅ | ✅ | ⭐⭐ | Fast | Learning |
| **Qwen2-0.5B** | 0.5B | 400 MB | ✅ | ✅ | ⭐⭐⭐ | Very Fast | Multilingual |
| **StableLM** | 3B | 1.1 GB | ❌ | ✅ | ⭐⭐⭐ | Medium | Instructions |
| **MobileLLM** | 125M | 120 MB | ✅ | ✅ | ⭐ | Ultra Fast | Mobile |

**Legend:**
- ⭐⭐⭐⭐⭐ = GPT-4 tier (relativně)
- ⭐⭐⭐⭐ = Velmi dobrý
- ⭐⭐⭐ = Použitelný
- ⭐⭐ = Slabý
- ⭐ = Toy model

---

## Praktické nasazení

### Ollama - Nejjednodušší způsob

```bash
# Instalace Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull phi3:mini

# Run interaktivně
ollama run phi3:mini

# Run jako API server
ollama serve  # Port 11434

# Curl request
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Vysvětli Docker v češtině",
  "stream": false
}'
```

**Python client:**

```python
import requests

def ask_ollama(prompt, model="phi3:mini"):
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': model,
        'prompt': prompt,
        'stream': False
    })
    return response.json()['response']

# Použití
answer = ask_ollama("Co je to Kubernetes?")
print(answer)
```

---

### llama.cpp - Pro embedded a optimalizaci

**Kompilace:**

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Kompilace (CPU only)
make

# S CUDA (NVIDIA GPU)
make LLAMA_CUDA=1

# S Metal (Apple Silicon)
make LLAMA_METAL=1
```

**Download modelu:**

```bash
# Phi-3 Mini
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# TinyLlama
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_0.gguf
```

**Inference:**

```bash
# Základní usage
./main -m phi-3-mini-4k-instruct-q4.gguf \
       -p "Explain Docker containers" \
       -n 256 \
       -t 4  # 4 threads

# Interaktivní chat
./main -m phi-3-mini-4k-instruct-q4.gguf --interactive

# Server mode
./server -m phi-3-mini-4k-instruct-q4.gguf --port 8080
```

**Python bindings:**

```python
from llama_cpp import Llama

llm = Llama(
    model_path="phi-3-mini-4k-instruct-q4.gguf",
    n_ctx=2048,  # Context window
    n_threads=4,  # CPU threads
    n_gpu_layers=0  # 0 = CPU only
)

output = llm(
    "Q: What is Docker? A:",
    max_tokens=200,
    temperature=0.7,
    stop=["Q:", "\n\n"]
)

print(output['choices'][0]['text'])
```

---

### Transformers (HuggingFace) - Pro Python projekty

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Load model
model_name = "microsoft/Phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,  # Half precision
    device_map="auto",  # Auto GPU/CPU selection
    load_in_4bit=True  # 4-bit quantization
)

# Option 1: Direct generation
inputs = tokenizer("Explain quantum physics:", return_tensors="pt")
outputs = model.generate(**inputs, max_length=200)
print(tokenizer.decode(outputs[0]))

# Option 2: Pipeline (easier)
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer
)

result = pipe("Write a poem about coding", max_length=150)
print(result[0]['generated_text'])
```

---

## Quantization - Komprese modelů

### Co je quantization?

Quantization = Snížení precision čísel v modelu:
- **FP32** (32-bit float): Plná precision, huge size
- **FP16** (16-bit float): Half precision, 2× menší
- **INT8** (8-bit integer): 4× menší, mírný quality loss
- **INT4** (4-bit integer): 8× menší, znatelný quality loss

### Comparison pro Phi-3 Mini:

| Quantization | Size | RAM | Quality Loss | Speed |
|--------------|------|-----|--------------|-------|
| FP32 | 14.8 GB | 15 GB | 0% (baseline) | Slowest |
| FP16 | 7.4 GB | 8 GB | <1% | Faster |
| INT8 | 3.7 GB | 4 GB | 2-3% | Fast |
| **INT4** | **1.9 GB** | **2 GB** | **5-8%** | **Fastest** |

**Doporučení:**
- **Desktop/Server:** FP16 (best quality/speed balance)
- **Raspberry Pi 4:** INT4 (nutnost kvůli RAM)
- **Raspberry Pi 3B:** INT4 (stále těsné)
- **Production:** INT8 (dobrý kompromis)

### Jak vytvořit quantized model:

```bash
# llama.cpp quantization tool
./quantize phi-3-mini-fp16.gguf phi-3-mini-q4_0.gguf Q4_0

# Options:
# Q4_0 - 4-bit, nejmenší
# Q5_0 - 5-bit, lepší kvalita
# Q8_0 - 8-bit, production quality
```

---

## MicroLLM na Raspberry Pi - Praktický guide

### Raspberry Pi 3B (1GB RAM) - Reálné možnosti

**Jediné funkční modely:**
1. ✅ **TinyLlama 1.1B (4-bit)** - 500MB RAM, 1-2 tok/s
2. ✅ **Qwen2-0.5B (4-bit)** - 400MB RAM, 3-4 tok/s
3. ✅ **MobileLLM-125M** - 120MB RAM, 15-20 tok/s (ale slabý)

**Setup:**

```bash
# Na Raspberry Pi 3B
sudo apt update
sudo apt install build-essential git

# Instalace llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j4  # Všechna 4 jádra

# Download TinyLlama
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_0.gguf

# Test
./main -m tinyllama-1.1b-chat-v1.0.Q4_0.gguf -p "Hello, world!" -n 50 -t 4
```

**Benchmark výsledek (reálný test):**
```
Prompt: "Explain Docker in simple terms"
Time: 38 seconds for 50 tokens
Tokens/s: 1.3
RAM usage: 520 MB
CPU: 100% on all cores
Temperature: 65°C
```

**Závěr:** Funguje, ale VELMI pomalu. Use case = batch processing, ne chat.

---

### Raspberry Pi 4 (4GB RAM) - Plně funkční

**Doporučené modely:**
1. ⭐ **Phi-3 Mini (4-bit)** - Nejlepší kvalita
2. ⭐ **Gemma 2B (4-bit)** - Rychlejší, creative
3. ✅ **TinyLlama** - Ultra rychlý fallback

**Setup s Ollama (jednodušší):**

```bash
# Instalace Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull phi3:mini
ollama pull gemma:2b
ollama pull tinyllama

# Test
ollama run phi3:mini "Vysvětli Docker v češtině"
```

**Benchmark výsledek:**
```
Model: Phi-3 Mini (4-bit)
Tokens/s: 2.5-3.0
RAM usage: 1.4 GB
CPU: 85% average
Quality: ⭐⭐⭐⭐ (velmi dobrá)
```

**Production setup - API server:**

```python
# api_server.py
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    prompt = request.json['prompt']
    model = request.json.get('model', 'phi3:mini')

    # Call Ollama via subprocess
    result = subprocess.run(
        ['ollama', 'run', model, prompt],
        capture_output=True,
        text=True
    )

    return jsonify({'response': result.stdout})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Systemd service pro autostart:**

```ini
# /etc/systemd/system/llm-api.service
[Unit]
Description=MicroLLM API Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/llm-api
ExecStart=/usr/bin/python3 /home/pi/llm-api/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable llm-api
sudo systemctl start llm-api
```

---

## Integrace s MyCoder-v2.0

### Ollama jako fallback provider

```python
# src/mycoder/api_providers.py (doplněk)

class OllamaLocalProvider(BaseProvider):
    """MicroLLM via Ollama on localhost"""

    def __init__(self, config):
        self.base_url = config.get('ollama_url', 'http://localhost:11434')
        self.model = config.get('ollama_model', 'phi3:mini')
        self.timeout = config.get('timeout', 60)

    async def query(self, prompt, **kwargs):
        """Query Ollama API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['response']
                else:
                    raise Exception(f"Ollama error: {response.status}")

    def check_health(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f'{self.base_url}/api/tags')
            return response.status_code == 200
        except:
            return False
```

**Přidání do 5-tier fallback:**

```python
# Enhanced provider chain
PROVIDER_PRIORITY = [
    'claude_anthropic',  # 1. Claude API (platený, kvalitní)
    'claude_oauth',      # 2. Claude CLI (zdarma, kvalitní)
    'gemini',            # 3. Google Gemini (zdarma, dobrý)
    'ollama_remote',     # 4. Ollama na serveru (self-hosted)
    'ollama_local'       # 5. MicroLLM lokálně (offline fallback)
]
```

**Use case:** Když všechny cloud providery failnou → použij lokální MicroLLM.

---

## Závěr - Které modely použít?

### Decision tree

```
Máš GPU?
├─ ANO → Používej větší modely (Llama 3.2 8B, atd.)
│
└─ NE → Máš 4GB+ RAM?
       ├─ ANO → Phi-3 Mini (3.8B, 4-bit)
       │         Nejlepší kvalita pro CPU inference
       │
       └─ NE → Máš alespoň 1GB RAM?
              ├─ ANO → TinyLlama (1.1B, 4-bit)
              │         RPi 3B compatible
              │
              └─ NE → MobileLLM (125M)
                      Ultra lightweight, ale slabý
```

### Moje TOP 3 doporučení:

**🥇 #1: Phi-3 Mini (3.8B)**
- Nejlepší kvalita v micro kategorii
- Překonává 2-3x větší modely
- Výborný coding a math
- Potřebuje 2GB+ RAM (4-bit)
- **Use case:** Desktop, RPi 4, server

**🥈 #2: Qwen2-0.5B**
- Ultra lightweight (400MB)
- Long context (32K tokens!)
- Multilingual
- Rychlý i na RPi 3B
- **Use case:** Embedded, IoT, simple tasks

**🥉 #3: Gemma 2B**
- Dobrý balance size/quality
- Creative writing
- Google backing
- 800MB RAM (4-bit)
- **Use case:** Chatbots, content generation

---

**Next:** [Kapitola 4 - PlayStation 4 Linux a GPU Hacking →](04-ps4-linux-hacking.md)
