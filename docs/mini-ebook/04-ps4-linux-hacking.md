# Kapitola 4: PlayStation 4 - Linux a GPU Hacking

## Úvod

PlayStation 4 je na první pohled herní konzole, ale pod kapotou běží x86-64 architektura s 8-core AMD CPU a slušnou AMD GCN GPU. S trochou hackingu z ní můžete udělat plnohodnotný Linux box. V této kapitole probereme jak na to a jaké jsou reálné možnosti.

---

## PlayStation 4 Hardware

### Specifikace

**PS4 (Standard, 2013):**
```
CPU:     AMD Jaguar 8-core @ 1.6 GHz (x86-64)
GPU:     AMD Radeon HD 7850 equivalent (18 CUs, 1.84 TFLOPS)
RAM:     8 GB GDDR5 (unified, sdílená s GPU)
Storage: 500 GB HDD (2.5" SATA)
OS:      FreeBSD-based "Orbis OS"
```

**PS4 Slim (2016):**
```
CPU:     Same (1.6 GHz)
GPU:     Slightly updated, same performance
RAM:     8 GB GDDR5
Storage: 500 GB / 1 TB
Power:   Lower consumption (~30% úspora)
```

**PS4 Pro (2016):**
```
CPU:     AMD Jaguar 8-core @ 2.1 GHz
GPU:     AMD Polaris-based (36 CUs, 4.20 TFLOPS)
RAM:     8 GB GDDR5 + 1 GB DDR3 (OS buffer)
Storage: 1 TB HDD
```

**Srovnání s běžným PC:**

| Component | PS4 Standard | PS4 Pro | Desktop ekvivalent |
|-----------|--------------|---------|---------------------|
| CPU | 8× 1.6 GHz Jaguar | 8× 2.1 GHz | Intel Core i3-4130 |
| GPU | 18 CUs, 1.84 TF | 36 CUs, 4.2 TF | GTX 750 Ti / RX 570 |
| RAM | 8 GB GDDR5 | 8+1 GB | 8 GB DDR4 + mid GPU |
| **Cena (použitá)** | **~$100** | **~$200** | **$300-400** |

**Závěr:** PS4 Pro za $200 je dobrý deal pro hardware!

---

## PlayStation 4 Software Stack

### Orbis OS (oficiální)

```
PlayStation 4 Boot
├─ Bootloader (Secure Boot)
│  └─ Sony signed only
├─ Kernel (FreeBSD 9.0 based)
│  └─ Heavily modified
├─ System Libraries
│  ├─ libkernel (syscalls)
│  ├─ libc (custom BSD libc)
│  └─ libSceVideoOut, libSceGnmDriver (GPU)
└─ Applications
   ├─ Shell (XMB interface)
   ├─ WebKit (browser)
   └─ Games (ELF binaries)
```

**Klíčové vlastnosti:**
- **FreeBSD 9.0** jádro (open-source based!)
- **Secure Boot** - Sony digitální podpisy
- **ASLR** - Address Space Layout Randomization
- **Sandboxing** - Každá app v jail
- **No root access** - Vše běží jako user

---

## PS4 Hacking - Exploit Chain

### Jak se dostaneme do systému?

**Exploit chain (typický průběh):**

```
1. WebKit Browser Exploit
   ↓
   (Get code execution v browseru)
   ↓
2. Kernel Exploit
   ↓
   (Získáme kernel privileges)
   ↓
3. Dump decryption keys
   ↓
   (Načteme master key z secure processor)
   ↓
4. Load payload (Linux bootloader)
   ↓
   (Nahrajeme kexec + Linux kernel)
   ↓
5. Boot Linux!
```

### Firmware verze a exploity

| FW Version | WebKit Exploit | Kernel Exploit | Linux? | Status |
|------------|----------------|----------------|--------|--------|
| 1.76 | ✅ | ✅ | ✅ | Plně hacknutelné |
| 4.05 | ✅ | ✅ | ✅ | Stabilní, doporučeno |
| 5.05 | ✅ | ✅ | ✅ | Nejpopulárnější |
| 7.02 | ✅ | ✅ | ✅ | Funkční |
| 9.00 | ✅ | ✅ | ✅ | Nejnovější hacknutá |
| 11.00+ | ❌ | ❌ | ❌ | Zatím ne |

**⚠️ Důležité:**
- PS4 na FW 11.00+ zatím není hacknutelná
- Pokud chcete hackovat, **NIKDY** neupgradujte FW!
- Použitá PS4 často mají starší FW (4.05, 5.05)

---

## PS4Linux - Instalace

### Projekt: ps4-linux

**GitHub:** https://github.com/fail0verflow/ps4-linux

**Co je potřeba:**
1. PS4 na hacknutelné FW (4.05, 5.05, 7.02, 9.00)
2. USB flash disk (FAT32, 8GB+)
3. Ethernet kabel (WiFi nefunguje v Linuxu!)
4. Patience a technical skills

### Krok 1: Jailbreak PS4

```bash
# Na PC - setup exploit server
git clone https://github.com/Al-Azif/ps4-exploit-host
cd ps4-exploit-host
python3 exploit_host.py

# Server běží na http://your-pc-ip:8080
```

**Na PS4:**
1. Nastavit network → Manual → DNS: `your-pc-ip`
2. Otevřít Browser → Jít na `http://your-pc-ip:8080`
3. Spustit exploit (např. Mira + HEN)
4. Čekat ~30 sekund
5. PS4 získá root přístup

**⚠️ Exploit je temporary!**
- Zmizí po restartu PS4
- Musíte spustit znovu po každém zapnutí
- Proto se tomu říká "jailbreak" ne "CFW"

### Krok 2: Load Linux bootloader

```bash
# Download ps4-linux loader
wget https://github.com/fail0verflow/ps4-linux/releases/download/v1/ps4-linux-loader.bin

# Připojit PS4 přes FTP (po jailbreaku)
ftp ps4-ip-address

# Upload loader
put ps4-linux-loader.bin /data/

# Execute loader (přes web exploit UI)
# → Spustí kexec a nahrauje Linux kernel
```

### Krok 3: Boot Linux

**USB flash disk struktura:**
```
USB:/
├─ bzImage          (Linux kernel pro PS4)
├─ initramfs.cpio.gz (Initial ramdisk)
└─ rootfs/          (Root filesystem - Ubuntu/Debian/Arch)
```

**Download pre-built image:**
```bash
# Fedora pro PS4 (nejstabilnější)
wget https://fail0verflow.com/ps4/ps4-fedora-5.05.img.xz
xz -d ps4-fedora-5.05.img.xz

# Zapsat na USB
sudo dd if=ps4-fedora-5.05.img of=/dev/sdX bs=4M status=progress
sync
```

**První boot:**
1. Vložit USB do PS4
2. Spustit ps4-linux-loader
3. Čekat 1-2 minuty
4. Linux by měl nabootovat na obrazovce!

**Default credentials:**
- Username: `ps4`
- Password: `ps4`

---

## PS4 Linux - Co funguje a co ne

### ✅ Co funguje:

1. **CPU (8 cores)**
   - Plně funkční
   - Všech 8 jader dostupných
   - x86-64 instrukce (AVX podporováno)
   - Thermal throttling funguje

2. **RAM (8 GB)**
   - ~7 GB dostupných (1 GB rezervováno pro systém)
   - GDDR5 = velmi rychlá
   - Lze použít jako RAMdisk

3. **Storage**
   - SATA HDD/SSD plně funguje
   - Můžete vyměnit za větší
   - Doporučuji SSD upgrade ($30 za 240GB)

4. **Ethernet**
   - Gigabit Ethernet funguje
   - ssh, http, všechno OK

5. **USB porty**
   - Všechny 3 USB porty fungují
   - Klávesnice + myš OK
   - External storage OK

6. **Audio**
   - HDMI audio funguje
   - Optical out funguje

7. **Bluetooth**
   - Funguje (s omezením)
   - DualShock 4 controller lze připojit

### ❌ Co NEFUNGUJE:

1. **GPU acceleration** 💔
   - Největší problém!
   - AMD GPU driver chybí
   - Grafika jen framebuffer (software rendering)
   - **Žádné OpenGL, Vulkan, CUDA**
   - Žádné ML acceleration

2. **WiFi**
   - Nefunguje vůbec
   - Musíte použít Ethernet

3. **Suspend/Resume**
   - Nelze uspat systém
   - Jen shutdown/reboot

4. **Hardware video decode**
   - Video playback = software only
   - Pomalé pro 4K

### Proč GPU nefunguje?

**Důvody:**

1. **Proprietární AMD firmware**
   - PS4 GPU má custom firmware od Sony
   - AMD odmítá uvolnit driver
   - Reverse engineering velmi složitý

2. **Secure processor**
   - GPU má secure crypto processor
   - Zamčený Sony klíči
   - Nelze obejít bez dekompilace

3. **Dokumentace chybí**
   - Sony neudělala public docs
   - GCN architektura je známá, ale PS4 varianta je custom

**Probíhá reverse engineering:**
- Projekt: **AMDGPU driver for PS4**
- Progress: ~30% (základní inicializace)
- ETA: Roky, pokud vůbec

---

## PS4 jako Linux box - Praktické použití

### Use case #1: Basic desktop

```bash
# Po bootu do Fedora
sudo dnf update
sudo dnf install @xfce-desktop
startxfce4
```

**Výkon:**
- ✅ Web browsing - OK (software rendering)
- ✅ Code editing - OK
- ✅ Terminal work - Výborné
- ❌ Video playback - Laguje (720p max)
- ❌ Gaming - NOPE (bez GPU)

**Rating:** 3/10 - Lepší koupit použitý laptop

---

### Use case #2: Server / NAS

```bash
# Instalace serveru
sudo dnf install docker nginx postgresql

# Docker container stack
docker run -d -p 80:80 nginx
docker run -d -p 5432:5432 postgres
```

**Výhody:**
- ✅ 8 CPU cores
- ✅ 7 GB RAM
- ✅ Gigabit Ethernet
- ✅ Tichý provoz (PS4 Slim)
- ✅ Nízká spotřeba (~50-80W)

**Nevýhody:**
- ❌ HDD je pomalý (5400 RPM)
- ❌ Jen 2 SATA porty (internal + USB?)
- ❌ Noise (PS4 Standard/Pro = hlučné)

**Rating:** 6/10 - OK pro home server, ale RPi 4 je lepší deal

---

### Use case #3: ML/LLM Inference (CPU only)

```bash
# Instalace Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull phi3:mini

# Test
time ollama run phi3:mini "Explain Docker" --verbose
```

**Benchmark (Phi-3 Mini, 4-bit):**
```
Hardware: PS4 Pro (8× 2.1 GHz Jaguar)
Tokens/s: 0.8-1.2 (VELMI pomalé!)
RAM usage: 2.5 GB
CPU usage: 100% (všech 8 jader)
Temperature: 75°C (thermal throttling)
```

**Srovnání:**

| Hardware | Tokens/s | Power | Noise |
|----------|----------|-------|-------|
| PS4 Pro | 1.0 | 120W | 🔊🔊🔊 (hlučné) |
| Intel i7-9700K | 30 | 95W | 🔊🔊 (tichý) |
| RPi 4 (4GB) | 2.5 | 5W | 🔇 (silent) |
| RTX 3060 | 100 | 170W | 🔊🔊 (medium) |

**Závěr:**
- PS4 je HORŠÍ než běžný desktop pro CPU inference
- Jaguar CPU je slabé (mobile-grade)
- Bez GPU je to waste

**Rating:** 2/10 - Nedoporučuji pro ML

---

### Use case #4: Retro gaming emulator (bez GPU = fail)

```bash
# Retroarch instalace
sudo dnf install retroarch

# Emulátory
retroarch  # NES, SNES, Genesis...
```

**Výsledek:**
- ❌ Bez GPU nelze renderovat rychle
- ❌ Dokonce i SNES emulace laguje
- ❌ PS1 emulace = unplayable

**Ironicky:** PS4 nemůže emulovat PS1 v Linuxu, protože chybí GPU driver 😂

**Rating:** 1/10 - Nesmysl

---

## GPU Reverse Engineering - Současný stav

### Proč je to tak těžké?

**1. Komplexní HW architektura:**
```
PS4 GPU (Liverpool APU)
├─ GCN 1.0 Compute Units (18× na PS4, 36× na Pro)
├─ Command Processor (submit GPU jobs)
├─ Shader Engines (execute shaders)
├─ ROP/ROB units (render output)
├─ Video Encode/Decode (VCE/UVD)
└─ Secure Processor (crypto, DRM)
    └─ 🔒 Sony locked!
```

**2. Firmware signing:**
- GPU potřebuje signed firmware
- Sony má private key
- Bez FW = GPU nepovede ani init

**3. Memory management:**
- GDDR5 je shared mezi CPU a GPU
- Custom memory controller
- Documentace = 0

**4. Register mapping:**
- Tisíce GPU registers
- Každý musí být reverse engineered
- Trial & error = risk bricking

### Probíhající projekty:

**1. fail0verflow team:**
```
Progress:
✅ GPU PCI device detection
✅ Basic register dumps
✅ Power management reverse engineered
🔄 Command submission WIP
❌ Shader compilation - blocked
❌ OpenGL/Vulkan - roky daleko
```

**2. AMDGPU-PS4 fork:**
```
Goal: Port Linux AMDGPU driver na PS4
Status: Very early alpha
Problems:
- Firmware loading fails
- Reset sequence unknown
- Interrupt handling broken
```

**ETA funkčního GPU driveru:**
- Optimisticky: 2-3 roky
- Realisticky: 5+ let
- Pesimisticky: Nikdy (AMD/Sony nepomohou)

---

## Je PS4 Linux worth it?

### Pros:
- ✅ Cheap hardware ($100-200)
- ✅ 8 CPU cores (dobré pro multithreaded)
- ✅ 8 GB GDDR5 RAM
- ✅ Learning experience (fun projekt)
- ✅ Můžete říct "mám PS4 s Linuxem" 😎

### Cons:
- ❌ **Žádné GPU** = největší dealbreaker
- ❌ CPU je slabé (Jaguar = 2013 mobile arch)
- ❌ Musíte mít hacknutelnou FW verzi
- ❌ Exploit po každém restartu
- ❌ Lepší koupit used PC za stejnou cenu

### Verdict:

**Pro hacking/learning:** ⭐⭐⭐⭐ (zábavný projekt)

**Pro production use:** ⭐ (nedoporučuji)

**Pro ML/LLM:** ⭐ (horší než běžný PC)

**Pro desktop:** ⭐⭐ (funguje, ale k ničemu)

---

## Alternativa: PS4 Pro jako "součástkový zdroj"

**Kreativní myšlenka:**

Místo běhu Linuxu na PS4, co vzít komponenty z mrtvé PS4 a použít jinde?

**Co lze vytěžit:**

1. **HDD/SSD** (2.5" SATA)
   - Použít v PC, NAS, external enclosure
   - Value: $20-40

2. **Power supply** (PS4 Slim/Pro)
   - 12V DC output
   - Lze použít pro custom projekty
   - Value: $15

3. **Cooling fan**
   - Brushless fan, quiet
   - Použít pro cooling jiných projektů
   - Value: $10

4. **Bluetooth/WiFi modul**
   - Standard mini-PCIe card
   - Funguje v PC!
   - Value: $5

5. **CPU + GPU APU** (Liverpool chip)
   - **NELZE použít** - BGA package, proprietary
   - Value: $0 (e-waste)

**Závěr:** Když máte mrtvou PS4 → vytěžte disky a PSU, zbytek = recyklace

---

## Conclusion: PS4 Linux v roce 2025

**Realita:**
- PS4 Linux **existuje** a **funguje**
- ALE bez GPU je to severely limited
- CPU je slabé na moderní workloads
- Lepší použít běžný PC nebo ARM board (RPi 4, Orange Pi)

**Kdy má smysl:**
- ✅ Už PS4 vlastníte a chcete experimentovat
- ✅ Learning projekt (reverse engineering, kernel hacking)
- ✅ Bragging rights 😄

**Kdy NEMÁ smysl:**
- ❌ Kupovat PS4 speciálně pro Linux
- ❌ Jakýkoli production use
- ❌ ML/LLM inference
- ❌ Gaming (ironic!)

**Můj názor:**
PS4 Linux je **cool experiment**, ale ne practical solution. Pokud chcete levný Linux box → kupte použitý ThinkPad za $150 nebo Orange Pi 5 za $80.

**Rating:**
- **Fun factor:** 9/10
- **Practicality:** 3/10
- **Value for money:** 4/10

---

**Next:** [Kapitola 5 - Xbox One: Secure Boot a Hacking →](05-xbox-one-hacking.md)
