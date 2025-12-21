# Kapitola 6: GPU Driver Politika - AMD vs NVIDIA

## Úvod

Tohle je kapitola, kde se věci stanou osobní. GPU drivery nejsou jen technický problém - jsou to politické rozhodnutí korporací o tom, co můžete a nemůžete dělat s hardware, který VLASTNÍTE. V této kapitole probereme rozdíly mezi AMD a NVIDIA přístupem, proč je open-source důležitý, a proč jsou některé praktiky čisté **svinárny**.

---

## Základní rozdíl: Open vs Closed

### AMD Approach (✅ Dobří kluci)

**Filosofie:**
- **Open-source first**
- Aktivní spolupráce s Linux community
- Dokumentace veřejně dostupná
- Kód v mainstreme Linux kernelu

**Drivers:**

```
AMD GPU Stack (Linux):
├─ AMDGPU (kernel driver)
│  ├─ Open-source (GPL)
│  ├─ In mainline Linux kernel
│  ├─ Full dokumentace
│  └─ Community contributions welcome
│
├─ Mesa (OpenGL/Vulkan)
│  ├─ RadeonSI (OpenGL)
│  ├─ RADV (Vulkan)
│  ├─ Open-source (MIT/Apache)
│  └─ Performance často LEPŠÍ než Windows
│
└─ ROCm (compute/ML)
   ├─ Open-source (mostly)
   ├─ HIP (CUDA competitor)
   └─ TensorFlow/PyTorch support
```

**Výsledek:**
- ✅ AMD GPU funguje out-of-box na Linuxu
- ✅ Žádné proprietary blob
- ✅ Můžete číst source code
- ✅ Můžete hackovat driver
- ✅ Komunita může fixovat bugy

---

### NVIDIA Approach (❌ Špatní kluci)

**Filosofie:**
- **Proprietary everything**
- Closed-source drivers
- Žádná dokumentace
- "Fuck you" attitude k open-source

**Drivers:**

```
NVIDIA GPU Stack (Linux):
├─ Nouveau (open-source driver)
│  ├─ Reverse engineered (NO NVIDIA HELP!)
│  ├─ Missing signed firmware
│  ├─ No power management
│  ├─ Performance: 20-30% vs proprietary
│  └─ ❌ Skoro nepoužitelný
│
└─ nvidia.ko (proprietary blob)
   ├─ Closed-source kernel module
   ├─ Binary blob linkovaný do kernelu
   ├─ Porušuje GPL (legal gray area)
   ├─ Breaks s každým kernel update
   └─ "It just works" (když funguje)
```

**Výsledek:**
- ❌ NVIDIA GPU = pain na Linuxu
- ❌ Musíte instalovat proprietary driver
- ❌ Kernel taint (broken GPL)
- ❌ Časté breaky s updates
- ❌ Žádná community podpora

**Linus Torvalds (2012):**
> "So, NVIDIA, fuck you!" 🖕
>
> *- Linux kernel maintainer*

(Toto opravdu řekl na veřejné konferenci. Hrdina! 😄)

---

## Proč je to důležité?

### Argument #1: Ownership

**Když si koupím GPU, je MÉ.**

- Měl bych mít právo vědět, jak funguje
- Měl bych mít právo upravit driver
- Měl bych mít právo opravit bugy
- Měl bych mít právo použít ho jak chci

**NVIDIA říká:**
- "Ne, je to NÁŠ hardware"
- "Smíte ho používat JEN jak říkáme my"
- "Dokumentaci NEUVIDÍTE"
- "Pokud si troufnete reverse engineerovat, zažalujeme vás"

**AMD říká:**
- "Tady máte dokumentaci"
- "Tady máte source code"
- "Udělejte s tím co chcete"
- "Pokud najdete bug, pošlete patch"

**Která filozofie je správná? AMD. Obviously.**

---

### Argument #2: Security

**Closed-source = security by obscurity**

NVIDIA proprietary blob:
```c
// nvidia.ko
// ??? (closed source)
// Možná obsahuje:
// - Backdoors?
// - Telemetrie?
// - Vulnerabilities?
//
// NEVÍME, protože nemůžeme vidět kód!
```

AMD open-source:
```c
// amdgpu driver - každý může číst
static int amdgpu_init(struct pci_dev *pdev) {
    // Exactly what it does
    // No secrets
    // Community reviewed
}
```

**Který je bezpečnější?**
- Open-source: Tisíce očí hledají bugy
- Closed-source: Jen NVIDIA ví co tam je

**Closed-source má horší security track record!**

---

### Argument #3: Longevity

**Co se stane když NVIDIA přestane supportovat vaši GPU?**

NVIDIA GTX 600 series (2012):
```
2012 - Release, full support
2016 - Moved to "legacy" driver
2020 - Legacy driver discontinued
2024 - ❌ NO DRIVER for new kernels
```

**Výsledek:**
- $500 GPU funguje 8 let, pak = paperweight
- NVIDIA říká "kupte novou"
- E-waste problém

AMD GCN 1.0 (2012):
```
2012 - Release
2024 - STILL SUPPORTED in mainline Linux
∞    - Bude fungovat forever (open-source)
```

**Výsledek:**
- GPU funguje tak dlouho jak chcete
- Komunita může maintainovat driver i po AMD EOL
- Sustainable

---

### Argument #4: Freedom

**Linux filosofie = svoboda**

- Svoboda spustit program jak chcete
- Svoboda studovat jak funguje
- Svoboda redistribuovat kopie
- Svoboda publikovat vylepšené verze

**NVIDIA proprietary driver:**
- ❌ Nemůžete spustit jak chcete (EULA restrictions)
- ❌ Nemůžete studovat (no source)
- ❌ Nemůžete redistribuovat (copyright)
- ❌ Nemůžete vylepšit (closed)

**AMD open-source driver:**
- ✅ Všechny čtyři svobody respektovány

---

## Konkrétní problémy

### Problém #1: Nvidia + Wayland = Broken

**Wayland** = Moderní display server pro Linux (náhrada za X11)

**Proč NVIDIA nefunguje:**
```
Wayland potřebuje:
├─ GBM (Generic Buffer Management)
│  └─ ❌ NVIDIA odmítá implementovat
│
└─ DRM (Direct Rendering Manager)
   └─ ❌ NVIDIA má vlastní framework (EGLStreams)
```

**NVIDIA postoj:**
- "Nechceme GBM, máme EGLStreams"
- "Pokud chcete podporu, implementujte EGLStreams do Waylandu"
- Celá Wayland komunita: "No fucking way"

**Výsledek:**
- NVIDIA + Wayland = broken po 10+ let
- AMD + Wayland = funguje perfektně
- NVIDIA finally capitulated v roce 2022 (!) a přidali GBM support

**Komentář:**
NVIDIA chtělo diktovat standardy místo adoptovat existující. Výsledek = roky broken experience pro uživatele. **Typická korporátní svinárna.**

---

### Problém #2: Signed Firmware

**Moderní NVIDIA GPU (Maxwell+):**

```
GPU boot sequence:
1. Power on
2. Load firmware from VBIOS
3. Check RSA signature
4. If signature invalid → GPU stays in low-power mode
5. ❌ Open-source driver CAN'T LOAD FIRMWARE
```

**Proč NVIDIA tohle dělá:**
- "Security" (bullshit excuse)
- Real důvod: **Lock-in proprietary driver**

**Důsledek:**
- Nouveau driver bez signed firmware = 10% performance
- NVIDIA odmítá release firmware publicly
- **Uživatelé jsou forced používat proprietary blob**

**AMD dělá:**
- Firmware je open-source
- Dostupný na linux-firmware repo
- Žádné signature checks
- Nouveau-equivalent driver běží plnou rychlostí

---

### Problém #3: CUDA Lock-in

**CUDA** = NVIDIA proprietary compute framework

**Problém:**
- Všechny ML frameworks používají CUDA
- TensorFlow, PyTorch = CUDA only (historicky)
- Academic papers = CUDA code
- Industry = CUDA trained

**Důsledek:**
- **Vendor lock-in** - nemůžete přejít na AMD
- **Monopol** - NVIDIA může diktovat ceny
- **Closed ecosystem** - žádná konkurence

**AMD reakce:**
- **ROCm** = Open-source compute stack
- **HIP** = CUDA-to-ROCm translation layer
- **hipify** = Auto-convert CUDA code

**ALE:**
- ROCm má slabší support
- Méně mature než CUDA
- NVIDIA má first-mover advantage

**Komentář:**
CUDA je geniální business strategy, ALE anti-competitive. AMD se snaží s ROCm, ale je to uphill battle. Potřebujeme **open standard** (Vulkan Compute? SYCL?)

---

## PS4/Xbox GPU Driver Mystery

### Proč Sony/Microsoft nemají open drivery?

**PlayStation 4:**
- GPU: AMD GCN 1.0 (známá architektura)
- AMD má open-source driver pro GCN
- **Proč není driver pro PS4?**

**Možné důvody:**

**1. Sony NDA (Non-Disclosure Agreement)**
```
AMD + Sony kontrakt:
- AMD poskytne custom GPU design
- Sony platí $$$
- Podmínka: "Žádná public dokumentace"
```

**Důvod:** Sony nechce faciliovat hacking konzole.

**2. Custom hardware**
```
PS4 GPU ≠ Standard GCN
├─ Custom memory controller (GDDR5 + eDRAM)
├─ Custom video encode/decode blocks
├─ Sony proprietary secure processor
└─ Register mappping changes
```

Reverse engineering potřebuje tisíce hodin práce.

**3. AMD nemá incentive**
```
PS4 Linux users: ~1000 lidí
AMD profit z PS4 driver: $0
AMD cost na vývoj: $100k+
ROI (Return on Investment): Negative
```

Business decision: "Why bother?"

---

### Je to AMD nebo Sony chyba?

**Můj názor: 70% Sony, 30% AMD**

**Sony:**
- Aktivně blokuje hacking (understandable, ALE svinárna)
- NDA zakazuje AMD release info
- Mohli by release driver post-EOL (nepudou)

**AMD:**
- Respektuje NDA (legal obligation)
- Ale mohli by pressure Sony na open docs
- Precedent: AMD release Tegra docs? Ne.

**Závěr:**
Je to **korporátní systémový problém**. Sony chrání business model, AMD nechce riskovat vztah s velkým zákazníkem. **Uživatelé = prdele.**

---

## Nintendo Switch Exception

### Proč Switch MÁ driver docs?

**Nintendo Switch:**
- GPU: NVIDIA Tegra X1 (Maxwell architecture)
- Reverse engineered driver: **existuje a funguje!**

**Jak je to možné?**

**1. Tegra je mobile chip**
```
NVIDIA Tegra použití:
├─ Android tablets
├─ NVIDIA Shield TV
├─ Self-driving cars (Tesla, atd.)
└─ Nintendo Switch

→ NVIDIA MUSÍ poskytnout driver pro Android
→ Android = open-source
→ Tegra driver = veřejně dostupný!
```

**2. Nouveau team reverse engineered**
```
├─ Tegra X1 TRM (Technical Reference Manual) leaked
├─ Nouveau team analyzed
├─ Wrote open-source driver
└─ Switch Linux benefits
```

**Výsledek:**
- Switch má fungující open-source GPU driver
- Performance ~80% vs proprietární
- Díky: **Android ecosystem + Nouveau community**

**Ironie:**
NVIDIA nechtělo pomoct, ale Android requirement forced their hand. 😄

---

## Co s tím můžeme dělat?

### Akce pro uživatele:

**1. Hlasujte peněženkou**
```
Pokud kupujete GPU:
├─ Zvažte AMD (support open-source)
├─ Nebo Intel Arc (open driver!)
└─ Avoid NVIDIA pokud možné
```

**2. Support open-source projekty**
```
Projekty které pomáhají:
├─ Nouveau (NVIDIA reverse engineering)
├─ Mesa (AMD/Intel graphics)
├─ Linux kernel
└─ Donate/contribute
```

**3. Raise awareness**
```
- Sdílejte info o problémech
- Review produktů s open-source v úvahu
- Pressure výrobce
```

**4. Right to Repair advocacy**
```
- Support legislativy jako EU Right to Repair
- Lobby za open hardware docs
- Fight against DMCA 1201 (anti-circumvention)
```

---

## GPU Vendor Comparison Table

| Aspect | AMD | NVIDIA | Intel Arc |
|--------|-----|--------|-----------|
| **Linux driver** | ✅ Open (AMDGPU) | ❌ Proprietary | ✅ Open (i915) |
| **Dokumentace** | ✅ Public | ❌ NDA only | ✅ Public |
| **Kernel mainline** | ✅ Yes | ❌ Out-of-tree | ✅ Yes |
| **Community** | ✅ Active | ⚠️ Reverse eng | ✅ Growing |
| **Windows perf** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Linux perf** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **ML/AI** | ⭐⭐⭐ (ROCm) | ⭐⭐⭐⭐⭐ (CUDA) | ⭐⭐ (new) |
| **Price/perf** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Ethics** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |

**Doporučení:**
- **Linux user:** AMD (nebo Intel Arc)
- **Windows + ML:** NVIDIA (bohužel nutnost)
- **Gaming:** AMD nebo NVIDIA (podle ceny)
- **Ethical choice:** AMD

---

## Osobní názor

### Proč mě to štve

**1. Vlastním hardware, ale nemohu ho plně používat**
```
Koupil jsem $500 GPU
→ Ale nemohu vidět jak funguje
→ Nemohu opravit driver bugy
→ Nemohu přidat features
→ Jsem DEPENDENT na korporaci
```

**2. Plánované obsolescence**
```
GPU má 10+ let fyzické životnosti
→ Ale driver support = 5-7 let
→ Forced upgrades
→ E-waste
→ Environment damage
```

**3. Monopolistické praktiky**
```
NVIDIA CUDA lock-in
→ Akademie/industry dependent
→ Nelze přejít na konkurenci
→ NVIDIA diktuje ceny
→ No free market competition
```

**4. Anti-repair kultur**
```
Korporace říkají: "Nemůžete opravit"
→ "Kupte nové"
→ Profit maximalizace
→ User rights = irrelevant
```

### Je to legální? Ano. Je to morální? **NE.**

---

## Filosofický závěr

### Right to Repair = Fundamental Freedom

**Analogie:**
```
Když koupíte auto:
├─ Můžete ho opravit sami
├─ Můžete použít third-party díly
├─ Můžete modifikovat
└─ Je to VAŠE

Proč GPU je jiné?
└─ Není! Korporace lžou.
```

**"Intellectual Property" argument:**
```
Korporace: "Je to NÁŠ intellectual property!"
Realita: IP chrání software/design, ne právo UŽÍT hardware
```

**"Security" argument:**
```
Korporace: "Closed-source = security!"
Realita: Security by obscurity NEFUNGUJE
          Open-source má LEPŠÍ security track record
```

**"Anti-piracy" argument:**
```
Korporace: "Open drivers = piracy!"
Realita: Piracy způsobuje closed ecosystem
          Open != piracy enabling
```

### Bottom line:

**Máte PRÁVO:**
- ✅ Znát jak funguje hardware který vlastníte
- ✅ Opravit co je vaše
- ✅ Modifikovat své zařízení
- ✅ Reverse engineerovat pro interoperabilitu

**Korporace nemají PRÁVO:**
- ❌ Diktovat jak použijete hardware
- ❌ Blokovat repairs a modifications
- ❌ Force obsolescence
- ❌ Zamykat ekosystém

---

## Call to Action

**Co MUSÍME udělat:**

1. **Legislative action**
   - Support Right to Repair bills
   - Demand open documentation
   - Fight DMCA overreach

2. **Market pressure**
   - Buy open-source friendly hardware
   - Review s ethical considerations
   - Boycott anti-consumer practices

3. **Community building**
   - Contribute k open-source projects
   - Share knowledge
   - Help reverse engineering efforts

4. **Education**
   - Teach others proč je to důležité
   - Raise awareness
   - Political activism

---

## Závěr

**GPU driver politika není jen tech issue - je to fight o základní freedoms.**

**AMD není perfektní, ale jsou MUCH BETTER než NVIDIA.**

**NVIDIA je příklad všeho co je špatně v moderní tech industry:**
- Proprietary lock-in
- Planned obsolescence
- Anti-competitive practices
- Disrespect pro user rights

**Support open-source. Demand freedom. Fight korporátní svinárny.**

**Your hardware. Your rules. Your freedom.** 🔓

---

**Next:** [Kapitola 7 - Hardware Strategie pro ML/LLM →](07-hardware-ml-strategies.md)
