# Kapitola 5: Xbox One - Secure Boot a Hacking

## Úvod

Xbox One je "Fort Knox" herních konzolí. Microsoft se z Xbox 360 RGH/JTAG debaklu poučil a vytvořil možná nejbezpečnější consumer device na trhu. V této kapitole probereme, proč je Xbox One tak těžké hacknout, jaké exploity existují, a zda je vůbec možné na něm spustit Linux.

---

## Xbox One Hardware

### Specifikace

**Xbox One (Standard, 2013):**
```
CPU:     AMD Jaguar 8-core @ 1.75 GHz (x86-64)
GPU:     AMD GCN 12 CUs @ 853 MHz (1.31 TFLOPS)
RAM:     8 GB DDR3 (5 GB pro hry, 3 GB pro OS)
         32 MB eSRAM (fast cache pro GPU)
Storage: 500 GB HDD (SATA)
OS:      Windows NT kernel + Hyper-V
```

**Xbox One S (2016):**
```
CPU:     Same @ 1.75 GHz
GPU:     Slightly upclocked @ 914 MHz (1.4 TFLOPS)
RAM:     8 GB DDR3
Storage: 500 GB / 1 TB / 2 TB
Features: 4K video playback, HDR
```

**Xbox One X (2017):**
```
CPU:     AMD Jaguar 8-core @ 2.3 GHz
GPU:     AMD Polaris 40 CUs @ 1172 MHz (6.0 TFLOPS!)
RAM:     12 GB GDDR5 (9 GB games, 3 GB OS)
Storage: 1 TB HDD
Features: Native 4K gaming
```

**Srovnání:**

| Spec | Xbox One | Xbox One X | PC ekvivalent |
|------|----------|------------|---------------|
| CPU | 8× 1.75 GHz | 8× 2.3 GHz | Intel i3-4150 |
| GPU | 1.31 TFLOPS | 6.0 TFLOPS | GTX 750 / GTX 1060 |
| RAM | 8 GB DDR3 | 12 GB GDDR5 | Mid-range PC |
| **Cena (used)** | **~$80** | **~$180** | **$250-350** |

**Hardware kvalita:** Xbox One X za $180 je solid deal!

---

## Xbox One Security Architecture

### Multi-layer security model

Microsoft postavil Xbox One jako fortress:

```
Xbox One Boot Chain
│
├─ Layer 1: Hardware Root of Trust
│  ├─ Southbridge (secure crypto processor)
│  ├─ Fuses (burned at factory, irreversible)
│  ├─ Bootrom (immutable, in silicon)
│  └─ 🔒 RSA-4096 keys
│
├─ Layer 2: Secure Boot Chain
│  ├─ 1BL (First Bootloader) - ROM, unsigned
│  ├─ 2BL (Second Bootloader) - Fuse verified
│  ├─ 3BL → 4BL → 5BL... (chain of trust)
│  └─ Each stage verifies next with RSA signature
│
├─ Layer 3: Hypervisor (Hyper-V)
│  ├─ VM 0: System OS (Windows kernel)
│  ├─ VM 1: Game OS (isolated)
│  └─ VM 2: Shared Resources
│  └─ 🔒 Hypervisor nelze obejít z user mode
│
├─ Layer 4: Kernel Patch Protection (KPP)
│  ├─ Runtime integrity checks
│  ├─ Code signing enforcement
│  └─ Anti-debug, anti-tamper
│
└─ Layer 5: Encrypted filesystem
   ├─ XVD format (Xbox Virtual Disk)
   ├─ AES-256 encryption
   └─ Per-console unique keys
```

**Srovnání se PS4:**

| Feature | Xbox One | PS4 |
|---------|----------|-----|
| Secure Boot | ✅ Multi-stage, fused | ✅ Basic, Sony signed |
| Hypervisor | ✅ Hyper-V (industrial grade) | ❌ None |
| Kernel protection | ✅ KPP (very strong) | ⚠️ Basic ASLR |
| Filesystem crypto | ✅ AES-256 per-console | ⚠️ Weak encryption |
| **Hackability** | **🔒 Very hard** | **🔓 Medium** |

---

## Xbox One vs Xbox 360 Security

### Proč je Xbox One těžší než 360?

**Xbox 360 slabiny:**
- ❌ Bootloader v flash paměti (rewritable)
- ❌ Glitch útoky (JTAG, RGH) fungovaly
- ❌ CPU byl PowerPC (jednodušší glitching)
- ❌ Žádný hypervisor

**Xbox One improvements:**
- ✅ Bootrom v silicon (nelze přepsat)
- ✅ Fuses burned (hardware immutable)
- ✅ Glitch protection (timing checks, redundancy)
- ✅ Hyper-V hypervisor (impossible to escape)
- ✅ Runtime integrity checks

**Výsledek:** Xbox 360 RGH = 2-3 hodiny práce. Xbox One = roky výzkumu, stále ne plně hacknutý.

---

## Xbox One Exploity - Současný stav

### 1. UWP App Exploits (Developer Mode)

**Co to je:**
- Xbox One má "Developer Mode" (legální!)
- Lze nainstalovat via Microsoft DevCenter ($20/rok)
- Umožňuje běh vlastních UWP apps

**Co lze udělat:**
```
Developer Mode:
├─ Instalace RetroArch (emulátory!)
├─ Homebrew apps (Python, web servery)
├─ File managers
└─ Media players (Kodi, Plex)
```

**Limitations:**
- ❌ Nelze escapnout sandbox
- ❌ Žádný kernel access
- ❌ Žádné hardware control
- ❌ Performance omezení (GPU throttled)
- ✅ ALE legální (Microsoft supported)

**Použití:**
```bash
# Na PC - instalace Visual Studio
# Vytvoření UWP projektu
# Deployment na Xbox přes Device Portal

# Xbox nastavení:
Settings → System → Console info → Developer mode → Switch and restart
```

**Rating:** ⭐⭐⭐ - Cool pro homebrew, ale ne "jailbreak"

---

### 2. Meltdown/Spectre útoky

**Teorie:**
- Xbox One CPU je x86-64 (vulnerable k Spectre/Meltdown)
- Teoreticky lze číst kernel memory

**Realita:**
- ✅ Spectre funguje na Xbox One
- ✅ Lze číst hypervisor memory
- ❌ ALE nelze využít pro code execution
- ❌ Microsoft patchoval via microcode update

**Status:** Research-only, ne praktický exploit

---

### 3. Collateral Damage (2020)

**Co to bylo:**
- Exploit chain objevený security researchers
- Kombinace WebKit + kernel bug
- Umožnil KERNEL CODE EXECUTION! 🎉

**Verze:**
- Fungoval na Xbox One firmware ~6689-6692
- Microsoft OKAMŽITĚ patchoval

**Proč to nefunguje dnes:**
- ❌ Exploit je fixed
- ❌ Xbox One force update (nelze zůstat na staré FW)
- ❌ Exploit nebyl nikdy public release

**Závěr:** Dokázal se kernel exploit, ale trvalo 7 let a byl okamžitě zabit.

---

### 4. Hardware Glitching (JTAG/RGH style)

**Teorie:**
- Xbox 360 RGH fungoval via CPU reset glitch
- Můžeme zkusit totéž na Xbox One?

**Pokusy:**
```
Glitch targets tested:
├─ CPU voltage glitching → ❌ Failed (protection)
├─ Clock glitching → ❌ Failed (redundant timers)
├─ SPI bus glitching → ❌ Failed (Southbridge crypto check)
├─ eFUSE bypass → ❌ Impossible (one-time programmable)
└─ Bootrom dump → ⚠️ Partial success (read-only)
```

**Proč nefunguje:**
1. **Redundant checks** - Bootrom kontroluje hash 3x
2. **Timing windows** - Glitch musí být v nano-sekundách
3. **Fuses** - Burned hardware state (nelze resetovat)
4. **Southbridge** - Dedicated crypto chip (nelze obejít)

**Status:** Komunita zkoušela 10+ let, **no success**.

---

### 5. NAND/eMMC Dump & Modify

**Teorie:**
- Dump NAND flash
- Modify bootloader
- Re-flash
- Profit?

**Realita:**
```bash
# Dump NAND (možné s hardmod)
flashrom -p buspirate_spi -r xbox_nand.bin

# Analyze bootloader
hexdump -C xbox_nand.bin | grep "bootloader_signature"

# Try to modify
# → RSA signature check FAILS
# → Console brick
```

**Proč nefunguje:**
- ✅ NAND lze dumpnout
- ❌ ALE bootloader je RSA-4096 signed
- ❌ Microsoft private key UNKNOWN
- ❌ Modifikovaný bootloader = instant brick

**Status:** Dead end.

---

## Xbox Linux - Je to možné?

### Short answer: **NE** (zatím)

**Proč ne:**

1. **Secure Boot nelze obejít**
   - Každý stage bootloaderu je signed
   - Microsoft private key není public
   - Forge signature = matematicky nemožné (RSA-4096)

2. **Hypervisor blokuje vše**
   - I kdybyste získali kernel exploit...
   - Hypervisor běží v ring -1 (pod kernelem)
   - Nelze načíst unsigned kernel

3. **Hardware lockdown**
   - eFUSE burned (nelze změnit boot mode)
   - Southbridge kontroluje signature před boot
   - Žádný "dev boot" mode

### Teoretické cesty:

**Cesta 1: Leak Microsoft signing keys**
- Pravděpodobnost: 0.01%
- Potřeba: Insider leak nebo NSA-level hack
- Důsledek: Microsoft by okamžitě revokoval a update force

**Cesta 2: Find hypervisor escape**
- Pravděpodobnost: 5%
- Potřeba: 0-day v Hyper-V
- Problém: Microsoft platí $250k+ za Hyper-V bugs (bug bounty)
- Realita: Pokud existuje, už je prodaný NSA/Zerodium

**Cesta 3: Hardware modification (chip-off attack)**
- Pravděpodobnost: 10%
- Potřeba: Decap Southbridge chip, extract keys via electron microscope
- Cena: $50k+ equipment
- Realita: Možná, ale impraktické

**Cesta 4: Quantum computing (break RSA-4096)**
- Pravděpodobnost: 0% (příštích 10 let)
- Potřeba: 4099-qubit quantum computer (neexistuje)
- Realita: Sci-fi

---

## Developer Mode - Co můžete udělat

### Legální "homebrew" cesta

**Setup:**

```bash
# 1. Registrace jako developer
https://partner.microsoft.com/en-us/dashboard/registration/developer
# Cena: $19/rok (individuální) nebo $99/rok (company)

# 2. Aktivace Developer Mode na Xbox
Settings → System → Console info → Developer mode
# Download "Dev Mode Activation" app
# Enter code z webu

# 3. Restart do Dev Mode
# Xbox se restartuje do Developer Mode

# 4. Device Portal
# Otevřít http://xbox-ip:11443
# Username: devkit, Password: (vygenerovaný)
```

**Co lze instalovat:**

1. **RetroArch** (emulátory)
   ```
   - NES, SNES, Genesis, GBA
   - PS1, N64 (s omezením)
   - Arcade (MAME)
   ```

2. **Kodi** (media center)
   ```
   - Video playback
   - Music library
   - Network streaming
   ```

3. **Python/Node.js apps**
   ```python
   # Simple Flask web server na Xboxu
   from flask import Flask
   app = Flask(__name__)

   @app.route('/')
   def hello():
       return "Hello from Xbox One!"

   app.run(host='0.0.0.0', port=8080)
   ```

4. **Custom UWP apps**
   ```csharp
   // C# UWP app
   // Compile in Visual Studio
   // Deploy přes Device Portal
   ```

**Limitations:**
- GPU je throttled (nižší performance)
- Omezená RAM (2 GB max pro app)
- Nelze měnit systém
- Performance worse než Retail mode

---

## Xbox Series S/X - Ještě těžší

**Nová generace = ještě víc security:**

```
Xbox Series X|S improvements:
├─ Custom Zen 2 CPU (faster, modernější architecture)
├─ RDNA 2 GPU (hardware ray tracing)
├─ Hardware TPM 2.0 (trusted platform module)
├─ Pluton security processor (Microsoft designed)
├─ Encrypted NVMe SSD (nelze dumpnout snadno)
└─ DirectStorage API (bypass some kernel layers)
```

**Pluton processor:**
- Dedicated security chip (jako Apple T2)
- Handles all crypto operations
- Boot chain verification in hardware
- **Physically separate** od main CPU

**Závěr:** Xbox Series = ještě neproniknutelnější než One.

---

## Srovnání: PS4 vs Xbox One Hackability

| Aspect | PlayStation 4 | Xbox One |
|--------|---------------|----------|
| **Secure Boot** | Sony signed | Microsoft RSA-4096 |
| **Kernel exploits** | ✅ Multiple found | ⚠️ Very rare (1-2) |
| **Persistence** | ✅ Works offline | ❌ Temporary |
| **Linux support** | ✅ ps4-linux works | ❌ Impossible |
| **GPU drivers** | ❌ No AMD driver | ❌ No driver |
| **Community** | ⭐⭐⭐⭐ (fail0verflow) | ⭐⭐ (smaller) |
| **Hackability** | **⭐⭐⭐⭐** | **⭐** |

**Proč je PS4 snazší:**
1. FreeBSD base (open-source kernel known)
2. Slabší secure boot
3. Žádný hypervisor
4. Offline mode (nelze force update)

**Proč je Xbox One těžší:**
1. Windows NT kernel (proprietary, complex)
2. Hyper-V hypervisor (extra layer)
3. Hardware fuses (irreversible)
4. Force updates (nelze zůstat na staré FW)

---

## Je Xbox One worth it pro hacking?

### Pros:
- ✅ Developer Mode je legální homebrew
- ✅ Levný hardware ($80-180)
- ✅ Dobrý jako media center (Kodi)
- ✅ Retro gaming (emulátory)

### Cons:
- ❌ **Žádný kernel access** (nelze hacknout properly)
- ❌ Developer Mode má performance limits
- ❌ Nelze spustit Linux
- ❌ GPU throttled v Dev Mode
- ❌ $20/rok subscription

### Verdict:

**Pro retro gaming / media center:** ⭐⭐⭐⭐ (Developer Mode OK)

**Pro hacking / learning:** ⭐⭐ (frustrující, limitovaný)

**Pro Linux:** ⭐ (nemožné)

**Pro ML/LLM:** ⭐ (stejný CPU jako PS4, bez GPU access)

---

## Future outlook

### Bude Xbox One někdy hacknutý?

**Scénáře:**

**Scénář A: Microsoft leak**
```
Pravděpodobnost: 5%
Scenario: Insider leak signing keys
Result: Temporary hack, než Microsoft revokuje
```

**Scénář B: Hardware exploit**
```
Pravděpodobnost: 15%
Scenario: Sophisticated chip-level attack
Investment: $50k+ equipment
Accessibility: Only research labs
```

**Scénář C: 0-day hypervisor escape**
```
Pravděpodobnost: 10%
Scenario: Critical Hyper-V bug
Problem: Microsoft bug bounty ($250k+)
Reality: Bugs prodávány, ne publikovány
```

**Scénář D: Quantum computing**
```
Pravděpodobnost: 0% (next 10 years)
Scenario: Break RSA-4096
Tech needed: 4099+ qubit QC
Reality: Not happening soon
```

**Realistický odhad:**
- Xbox One nikdy nebude plně hacknutý jako Xbox 360
- Developer Mode zůstane maximum
- Xbox Series? Ještě méně pravděpodobné

---

## Osobní názor: Microsoft vs Hacking Community

### Etická debata

**Microsoft perspektiva:**
- "Chráníme intellectual property"
- "Zabráníme piracy"
- "Secure ecosystem pro developers"

**Hacker perspektiva:**
- "Je to MŮJHARDWARE, měl bych s ním dělat co chci"
- "Right to repair a modify"
- "Homebrew ≠ Piracy"

**Má pravda:**
✅ **Souhlasím s hackery**

Důvody:
1. **Ownership** - Když si koupím zařízení, je MÉ
2. **Homebrew** - Legitimní use (emulátory, custom apps)
3. **Preservation** - Když MS shutne servery, console = brick?
4. **Learning** - Security research je valuable skill
5. **e-Waste** - Locked hardware končí na skládce

**ALE:**
- Chápu anti-piracy snahy
- DRM má své místo (protect developers)
- Balance mezi security a freedom je těžký

**Ideální svět:**
- Secure boot pro retail mode (protect ecosystem)
- **Unlock option po EOL** (End of Life)
- Official dev mode (už existuje, dobře MS!)

---

## Conclusion

**Xbox One hacking realita:**
- Je to **nejtěžší consumer device** na hacknutí
- Microsoft udělal security práci VELMI dobře
- Developer Mode je maximum co dostanete
- Linux? Zapomeňte.

**Pro comparison:**
- **PS4**: Hackable, Linux runs ⭐⭐⭐⭐
- **Xbox One**: Developer Mode only ⭐⭐
- **Nintendo Switch**: Fully hacked (Tegra exploit) ⭐⭐⭐⭐⭐
- **Xbox 360**: RGH = easy hack ⭐⭐⭐⭐⭐

**Doporučení:**
- Pokud chcete hacknout konzoli → kupte PS4 nebo Switch
- Xbox One → použijte Developer Mode nebo kupte PC
- Pokud chcete Linux → PS4, nebo rovnou laptop/desktop

**Final rating:**
- **Security quality:** 10/10 (Microsoft odvedl skvělou práci)
- **Hackability:** 2/10 (skoro nemožné)
- **Homebrew (Dev Mode):** 7/10 (legální a funkční)

---

**Next:** [Kapitola 6 - GPU Driver Politika: AMD vs NVIDIA →](06-gpu-driver-politics.md)
