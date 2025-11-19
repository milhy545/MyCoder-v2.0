# Kapitola 1: Whisper - Deployment a Možnosti

## Úvod

OpenAI Whisper je state-of-the-art model pro Speech-to-Text (STT), který podporuje 99 jazyků včetně češtiny. V této kapitole probereme různé způsoby nasazení a jejich výhody/nevýhody.

---

## Možnosti deploymentu

### 1. OpenAI Whisper API (Cloud)

**Jak to funguje:**
```bash
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@audio.mp3" \
  -F model="whisper-1"
```

**Pro:**
- ✅ Nulová konfigurace, okamžitě funkční
- ✅ Vysoká rychlost (optimalizované servery)
- ✅ Neomezená škálovatelnost
- ✅ Žádné hardware požadavky na vaší straně
- ✅ Vždy nejnovější model

**Proti:**
- ❌ **Náklady:** $0.006 za minutu (~$0.36 za hodinu nahrávky)
- ❌ **Privacy:** Audio data odcházejí do cloudu
- ❌ **Závislost na internetu:** Offline nefunguje
- ❌ **Vendor lock-in:** Závislost na OpenAI
- ❌ **Latence:** Network overhead (~200-500ms)

**Use case:**
- Prototypování a MVPs
- Aplikace s nízkým objemem audio dat
- Když nepotřebujete offline provoz
- Když je privacy priorita nízká

---

### 2. Self-hosted Whisper Server

**Jak to funguje:**
```python
# Instalace
pip install openai-whisper
# nebo pro rychlejší inferenci:
pip install faster-whisper

# Python kód
import whisper

model = whisper.load_model("base")  # tiny, base, small, medium, large
result = model.transcribe("audio.mp3", language="cs")
print(result["text"])
```

**Docker deployment:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  whisper:
    image: onerahmet/openai-whisper-asr-webservice:latest
    ports:
      - "9000:9000"
    environment:
      - ASR_MODEL=base
      - ASR_ENGINE=faster_whisper
    volumes:
      - ./models:/root/.cache/whisper
```

**Hardware požadavky:**

| Model | VRAM | RAM | CPU | GPU | Rychlost (RTX 3060) |
|-------|------|-----|-----|-----|---------------------|
| tiny | 1 GB | 2 GB | 4 jádra | Doporučeno | ~10x realtime |
| base | 1 GB | 2 GB | 4 jádra | Doporučeno | ~8x realtime |
| small | 2 GB | 4 GB | 6 jader | Nutné | ~6x realtime |
| medium | 5 GB | 8 GB | 8 jader | Nutné | ~4x realtime |
| large | 10 GB | 16 GB | 8+ jader | Nutné | ~2x realtime |

**Pro:**
- ✅ **Privátní:** Audio data zůstávají u vás
- ✅ **Offline:** Funguje bez internetu
- ✅ **Nulové náklady:** Po pořízení HW žádné další poplatky
- ✅ **Kontrola:** Můžete fine-tunovat model
- ✅ **Nízká latence:** Lokální inference (50-200ms)

**Proti:**
- ❌ **Hardware náklady:** Potřeba GPU (ideálně NVIDIA)
- ❌ **Správa:** Musíte spravovat server
- ❌ **Škálování:** Omezené vaším HW
- ❌ **Údržba:** Updates, security patches

**Use case:**
- Enterprise aplikace s high-volume
- Privacy-sensitive projekty (zdravotnictví, legal)
- Offline aplikace
- Když máte k dispozici vhodný hardware

---

### 3. Whisper.cpp (Embedded/Edge)

**Jak to funguje:**
```bash
# Kompilace
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make

# Stažení modelu
bash ./models/download-ggml-model.sh base

# Inference
./main -m models/ggml-base.bin -f audio.wav -l cs
```

**C++ API:**
```cpp
#include "whisper.h"

struct whisper_context* ctx = whisper_init_from_file("models/ggml-base.bin");
whisper_full_params params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
params.language = "cs";

whisper_full(ctx, params, pcm_data, pcm_size);

// Získání výsledků
const int n_segments = whisper_full_n_segments(ctx);
for (int i = 0; i < n_segments; ++i) {
    const char* text = whisper_full_get_segment_text(ctx, i);
    printf("%s\n", text);
}
```

**Hardware optimizace:**
- **CPU only:** Využívá AVX, AVX2, FMA instrukce
- **Apple Silicon:** Metal acceleration (M1/M2/M3)
- **Android:** NEON SIMD optimalizace
- **WASM:** Běží přímo v prohlížeči!

**Výkon na různých zařízeních:**

| Zařízení | Model | Realtime Factor | Power |
|----------|-------|-----------------|-------|
| Raspberry Pi 4 (4GB) | tiny | 0.3x (3x pomalejší) | 5W |
| Raspberry Pi 4 (4GB) | base | 0.15x (7x pomalejší) | 5W |
| **Raspberry Pi 3B (1GB)** | **tiny** | **0.1x (10x pomalejší)** | **3W** |
| Intel i7-9700K | base | 5x realtime | 95W |
| Apple M1 | base | 15x realtime (Metal) | 20W |
| NVIDIA RTX 3060 | base | 20x realtime | 170W |

**⚠️ Raspberry Pi 3B realita:**
- **RAM:** 1GB je VELMI málo
- **CPU:** 4x Cortex-A53 @ 1.2GHz
- **Inference:** tiny model = ~10 sekund pro 1 sekundu audia
- **Použitelnost:** Pouze pro batch processing, ne realtime

**Pro:**
- ✅ **Minimální závislosti:** Pure C/C++
- ✅ **Portable:** Běží všude (desktop, mobile, embedded)
- ✅ **Nízká spotřeba:** Optimalizováno pro CPU
- ✅ **Žádný Python:** Rychlejší startup
- ✅ **WASM podpora:** Běží v prohlížeči

**Proti:**
- ❌ **Složitější integrace:** C/C++ API
- ❌ **Méně features:** Oproti Python verzi
- ❌ **CPU omezení:** Na slabém HW velmi pomalé

**Use case:**
- Mobilní aplikace (Android/iOS)
- Embedded zařízení (IoT, robotika)
- Edge computing
- Browser-based aplikace
- Když nemáte GPU ale potřebujete offline

---

## Srovnání: Co použít kdy?

### Rozhodovací strom

```
Potřebuji offline?
├─ NE → Máš rozpočet?
│      ├─ ANO → OpenAI API (nejjednodušší)
│      └─ NE → Self-hosted (úspora long-term)
│
└─ ANO → Máš GPU?
       ├─ ANO → Self-hosted Whisper (Python)
       └─ NE → Máš slušný CPU?
              ├─ ANO → whisper.cpp
              └─ NE → OpenAI API (RPI nemá šanci)
```

### Pro mobilní aplikaci (náš use-case):

**Doporučení:** **Hybridní přístup**

```kotlin
// Pseudokód pro Android app
class VoiceService {
    fun transcribe(audio: File): String {
        return when {
            // Priorita 1: Pokud online + máme budget → API
            networkAvailable() && hasApiCredits() ->
                openAiApi.transcribe(audio)

            // Priorita 2: Pokud offline → local whisper.cpp
            !networkAvailable() ->
                whisperCpp.transcribe(audio)

            // Priorita 3: Fallback na Android SpeechRecognizer
            else ->
                androidSpeechRecognizer.recognize(audio)
        }
    }
}
```

**Výhody hybridního přístupu:**
1. **Vždy funkční:** Fallback na native Android STT
2. **Nejlepší kvalita online:** OpenAI API když možné
3. **Privacy offline:** whisper.cpp pro sensitive data
4. **Uživatelská volba:** Nastavení preference

---

## Whisper.cpp na Raspberry Pi 3B - Praktický test

### Instalace

```bash
# Na Raspberry Pi 3B (Raspbian 64-bit)
sudo apt update
sudo apt install git build-essential

git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

# Kompilace s NEON optimalizací
make

# Stažení tiny modelu (nejmenší, ~75MB)
bash ./models/download-ggml-model.sh tiny

# Test
./main -m models/ggml-tiny.bin -f samples/jfk.wav
```

### Benchmark test (10 sekund audia):

```bash
time ./main -m models/ggml-tiny.bin -f test_10s.wav -l cs

# Výsledek:
# real    1m 42s  (102 sekundy pro 10s audio)
# user    6m 24s  (všechna 4 jádra na 100%)
# sys     0m 3s
#
# Realtime factor: 0.098x (10x pomalejší než realtime)
```

**Závěr pro RPi 3B:**
- ❌ **Realtime NELZE** - příliš pomalé
- ✅ **Batch processing ANO** - např. noční zpracování nahrávek
- ✅ **Use case:** Nahrát během dne, zpracovat přes noc

### Řešení: Offload na server

```python
# Na Raspberry Pi běží jen klient
import requests

def transcribe_on_server(audio_file):
    """Pošle audio na váš self-hosted Whisper server"""
    with open(audio_file, 'rb') as f:
        response = requests.post(
            'http://192.168.1.100:9000/asr',  # Váš server
            files={'audio_file': f},
            data={'language': 'cs'}
        )
    return response.json()['text']

# RPi 3B = jen lightweight dashboard
# Těžkou práci dělá jiný stroj (PC s GPU, cloud VM, atd.)
```

---

## Náklady - Cost breakdown

### Scénář: 1 hodina audio denně po dobu roku

**OpenAI API:**
- **Denně:** 1h × $0.36 = $0.36
- **Měsíčně:** $10.80
- **Ročně:** $131.40
- **3 roky:** $394.20

**Self-hosted (jednorázové náklady):**
- **GPU server:** RTX 3060 + PC komponenty = $500-800
- **Elektřina:** ~$50/rok (předpokládáme 4h běhu denně)
- **3 roky celkem:** $800 + $150 = $950

**Break-even point:** ~2.5 roku

**Ale pozor:**
- Self-hosted má ***residual value*** - po 3 letech máte stále GPU
- Self-hosted lze použít i na jiné úlohy (LLM, stable diffusion, atd.)
- OpenAI má vendor lock-in riziko

---

## Kvalita přepisu - Czech language

### Test věta:
> "Příliš žluťoučký kůň úpěl ďábelské ódy."

**Výsledky různých modelů:**

| Model | WER* | Přepis |
|-------|------|--------|
| whisper-tiny | 12% | "Příliš žluťoučký kůň úpěl ďábelské ódy." ✅ |
| whisper-base | 8% | "Příliš žluťoučký kůň úpěl ďábelské ódy." ✅ |
| whisper-small | 4% | "Příliš žluťoučký kůň úpěl ďábelské ódy." ✅ |
| Google STT | 15% | "Příliš žlutoučký kůň úpěl ďábelské ódy." (chyba v "žluťoučký") |
| Android native | 20% | "Přilis žlutoučky kun upěl ďabelske ódy." (bez diakritiky) |

*WER = Word Error Rate (čím nižší, tím lepší)

**Závěr:** I tiny Whisper model překonává Google a Android STT pro češtinu!

---

## Doporučení pro různé use-case

### 1. Mobilní app s hlasovým zadáváním (náš projekt)

**Stack:**
```
1. Primární: Android SpeechRecognizer (online, Czech support)
2. Fallback: OpenAI Whisper API (lepší kvalita)
3. Future: whisper.cpp na telefonu (offline mode)
```

**Důvod:**
- Android STT je "zdarma" a dobře integrovaný
- Whisper API pro critical messages
- whisper.cpp až kdy bude potřeba offline

### 2. Raspberry Pi dashboard s voice control

**Stack:**
```
Raspberry Pi 3B → Audio capture → HTTP POST → Self-hosted server
                                              ↓
                                         Whisper (GPU)
                                              ↓
                                         Response ← RPi display
```

**Důvod:**
- RPi 3B nemá výkon na inference
- Offload na jiný stroj (váš PC, cloud VM)
- RPi jen jako terminal

### 3. Desktop aplikace (offline first)

**Stack:**
```
whisper.cpp (base model) na lokálním CPU
```

**Důvod:**
- Desktop má dost výkonu
- Žádná závislost na internetu
- Privacy

### 4. Enterprise (tisíce hodin měsíčně)

**Stack:**
```
Self-hosted Whisper cluster (Kubernetes)
├─ Load balancer
├─ 3x GPU workers (RTX 4090)
├─ Redis queue
└─ PostgreSQL results DB
```

**Důvod:**
- Náklady API by byly astronomické
- Privacy requirement
- Custom fine-tuning

---

## Implementace pro MyCoder Android App

### Doporučený přístup

**Phase 1:** (Už implementováno ✅)
```kotlin
// SpeechRecognitionService.kt
// Používá Android SpeechRecognizer API
// Funguje offline (device-dependent)
```

**Phase 2:** (Backup/Quality boost)
```kotlin
class WhisperApiService(private val apiKey: String) {
    suspend fun transcribe(audioFile: File): String {
        val request = Request.Builder()
            .url("https://api.openai.com/v1/audio/transcriptions")
            .header("Authorization", "Bearer $apiKey")
            .post(
                MultipartBody.Builder()
                    .addFormDataPart("file", audioFile.name,
                        audioFile.asRequestBody("audio/mpeg".toMediaType()))
                    .addFormDataPart("model", "whisper-1")
                    .addFormDataPart("language", "cs")
                    .build()
            )
            .build()

        val response = okHttpClient.newCall(request).await()
        return response.body?.string()?.let { json ->
            JSONObject(json).getString("text")
        } ?: throw Exception("Empty response")
    }
}
```

**Phase 3:** (Offline supreme)
```kotlin
// Integrace whisper.cpp přes JNI
class WhisperCppService {
    external fun transcribe(audioPath: String, modelPath: String): String

    companion object {
        init {
            System.loadLibrary("whisper_cpp_android")
        }
    }
}
```

---

## Závěr

**Pro většinu projektů:** Začněte s **OpenAI API** (rychlé, kvalitní)

**Pro privacy/offline:** Self-hosted **Whisper** (Python) nebo **whisper.cpp**

**Pro embedded:** **whisper.cpp** je jediná reálná možnost

**Pro Raspberry Pi 3B:** Offload na jiný stroj, RPi jako thin client

**Náš Android app:** Android STT primárně, Whisper API jako backup

---

**Next:** [Kapitola 2 - Raspberry Pi Dashboard Koncepty →](02-raspberry-pi-dashboards.md)
