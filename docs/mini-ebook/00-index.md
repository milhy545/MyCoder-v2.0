# Hardware, ML a Svoboda: Příručka pro Hackery a Bastlíře

**Mini Ebook - Technické poznámky o hardware hackingu, strojovém učení a korporátních omezeních**

---

## O této knize

Tato kniha vznikla z brainstormingu o využití dostupného hardware pro ML/LLM úlohy, hackingu herních konzolí a boji proti korporátním omezením. Obsahuje praktické informace, technické detaily a filosofické úvahy o svobodě upravovat vlastní hardware.

**Datum vytvoření:** 2025-11-19
**Téma:** Hardware hacking, MicroLLM, Whisper, PS4/Xbox, GPU politika
**Kontext:** MyCoder-v2.0 projekt s mobilní Android aplikací

---

## Obsah

### [Kapitola 1: Whisper - Deployment a Možnosti](01-whisper-deployment.md)
- OpenAI Whisper API
- Self-hosted Whisper server
- Whisper.cpp pro embedded systémy
- Srovnání výkonu a nákladů
- Doporučení pro různé use-case

### [Kapitola 2: Raspberry Pi Dashboard Koncepty](02-raspberry-pi-dashboards.md)
- Control Center Dashboard
- Home Automation Dashboard
- System Monitor Dashboard
- Media Center Dashboard
- AI Assistant Dashboard
- Development Dashboard
- NVMe na Raspberry Pi 3B

### [Kapitola 3: MicroLLM Modely](03-microllm-models.md)
- Phi-3 Mini (Microsoft)
- Google Gemma
- TinyLlama
- Qwen2-0.5B
- StableLM-Zephyr
- MobileLLM
- Srovnání a benchmarky
- Deployment strategie

### [Kapitola 4: PlayStation 4 - Linux a GPU Hacking](04-ps4-linux-hacking.md)
- PS4Linux instalace
- Exploit chain (mira-project, ps4-linux-loader)
- GPU reverse engineering
- Omezení a možnosti
- AMD GPU na PS4

### [Kapitola 5: Xbox One - Secure Boot a Hacking](05-xbox-one-hacking.md)
- Secure Boot architektura
- UEFI signing a klíče
- Hardware glitching útoky
- Software exploity
- Xbox Linux možnosti
- Proč je Xbox těžší než PS4

### [Kapitola 6: GPU Driver Politika - AMD vs NVIDIA](06-gpu-driver-politics.md)
- Open-source vs proprietární ovladače
- AMD svoboda vs NVIDIA uzamčení
- GCN architektura a dokumentace
- NVIDIA Tegra omezení
- Korporátní "svinárny"
- Právo na modifikaci vlastního hardware

### [Kapitola 7: Hardware Strategie pro ML/LLM](07-hardware-ml-strategies.md)
- Využití dostupného hardware
- Raspberry Pi 3B limity (1GB RAM)
- PS4 Pro potenciál
- Xbox Series S jako ML box?
- Cost-benefit analýza
- DIY vs cloud řešení

---

## Jak číst tuto knihu

Každá kapitola je samostatná a můžete je číst v libovolném pořadí podle vašeho zájmu. Doporučuji ale začít u **Kapitoly 6** o GPU politice, pokud vás zajímá filosofie svobodného hardware.

Pro praktické nasazení začněte u **Kapitoly 1** (Whisper) nebo **Kapitoly 3** (MicroLLM), podle toho, co chcete implementovat.

Pokud vás zajímá hacking konzolí, skočte rovnou na **Kapitoly 4 a 5**.

---

## Varování a právní upozornění

⚠️ **Důležité upozornění:**

- Modifikace firmware konzolí může porušit záruční podmínky
- Reverse engineering může být v některých jurisdikcích omezen
- Informace v této knize jsou určeny pro vzdělávací a výzkumné účely
- Autor nepřebírá odpovědnost za zneužití těchto informací
- Vždy respektujte autorská práva a licence

**ALE:** Máte právo upravovat hardware, který vlastníte. Korporátní uzamčení je morálně sporné.

---

## Použité zdroje a reference

- Linux-libre projekt: https://www.fsfla.org/
- PS4Linux projekt: https://github.com/fail0verflow
- Whisper.cpp: https://github.com/ggerganov/whisper.cpp
- HuggingFace Model Hub: https://huggingface.co/models
- AMD GPU dokumentace: https://www.x.org/wiki/RadeonFeature/
- Raspberry Pi oficiální docs: https://www.raspberrypi.com/documentation/

---

## O autorovi poznámek

Tato kniha vznikla jako záznam technického brainstormingu v rámci vývoje MyCoder-v2.0 projektu - AI development assistant s podporou mobilní Android aplikace s hlasovým ovládáním.

**Technický stack projektu:**
- Python 3.9+ s Poetry
- Android (Kotlin + Jetpack Compose)
- 5-tier API provider systém
- Q9550 thermal management
- RocketChat WebSocket integration

---

**Verze:** 1.0
**Formát:** Markdown (kompatibilní s Pandoc pro Kindle konverzi)
**Licence:** Osobní použití - šiřte svobodně

---

**Začněte číst:** [Kapitola 1 - Whisper Deployment →](01-whisper-deployment.md)
