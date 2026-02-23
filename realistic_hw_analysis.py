#!/usr/bin/env python3
"""
Realistická analýza HW požadavků pro běžné servery a PC
"""

def realistic_hw_analysis():
    print("💻 REALISTICKÁ HW ANALÝZA PRO MyCoder")
    print("=" * 60)

    print("🔍 TVŮJ SOUČASNÝ HARDWARE:")
    print("   RAM: Kolik máš aktuálně? (např. 16GB, 32GB)")
    print("   GPU: Jakou máš grafiku? (např. GTX 1060, RTX 3060, integrated)")
    print("   CPU: Kolik jader? (např. 4, 6, 8 cores)")
    print("   Disk: Kolik volného místa? (pro modely)")

    print(f"\n📊 REÁLNÉ POŽADAVKY PRO RŮZNÉ MODELY:")

    # Realistic model requirements with overhead
    models = {
        "tinyllama": {
            "model_size": "637 MB",
            "ram_needed": "2-3 GB",  # Model + system + overhead
            "disk_space": "1 GB",
            "description": "Funguje na čemkoliv",
            "quality": "⭐⭐☆☆☆",
            "realistic": "✅ Funguje i na 4GB RAM PC"
        },
        "deepseek-coder-1.3b": {
            "model_size": "750 MB",
            "ram_needed": "3-4 GB",
            "disk_space": "1 GB",
            "description": "Malý ale použitelný",
            "quality": "⭐⭐⭐☆☆",
            "realistic": "✅ Funguje na 8GB RAM PC"
        },
        "llama3.2-3b": {
            "model_size": "2 GB",
            "ram_needed": "6-8 GB",
            "disk_space": "3 GB",
            "description": "Dobrý kompromis",
            "quality": "⭐⭐⭐⭐☆",
            "realistic": "✅ Funguje na 16GB RAM PC"
        },
        "codellama-7b": {
            "model_size": "3.8 GB",
            "ram_needed": "8-12 GB",
            "disk_space": "5 GB",
            "description": "Solidní kódování",
            "quality": "⭐⭐⭐⭐⭐",
            "realistic": "⚠️  Potřebuje min. 16GB RAM"
        },
        "codestral-22b": {
            "model_size": "13 GB",
            "ram_needed": "24-32 GB",  # Realisticky!
            "disk_space": "15 GB",
            "description": "Premium, ale žere RAM",
            "quality": "⭐⭐⭐⭐⭐",
            "realistic": "❌ Potřebuje 32GB+ RAM reálně"
        }
    }

    print("   Model              Velikost  RAM potřeba  Disk  Kvalita     Realita")
    print("   " + "="*80)

    for model, specs in models.items():
        print(f"   {model:<17} {specs['model_size']:<9} {specs['ram_needed']:<11} {specs['disk_space']:<5} {specs['quality']:<11} {specs['realistic']}")
        print(f"   {'':>18} → {specs['description']}")
        print()

    print(f"💡 PROČ CODESTRAL POTŘEBUJE TOLIK RAM:")
    print("   🔹 Model: 13GB")
    print("   🔹 Ollama overhead: +2-3GB")
    print("   🔹 Docker overhead: +2GB")
    print("   🔹 System rezerva: +4-6GB")
    print("   🔹 Inference buffer: +3-4GB")
    print("   ═══════════════════════════════")
    print("   📊 CELKEM: 24-28GB RAM reálně!")

    print(f"\n🖥️  TVOJE MOŽNOSTI PODLE HW:")

    hw_scenarios = {
        "Starší PC (8GB RAM)": {
            "recommended": "deepseek-coder-1.3b",
            "max_model": "llama3.2-1b",
            "docker_size": "1.5 GB",
            "performance": "Pomalé, ale funkční",
            "coding_quality": "Základní kódování OK"
        },
        "Běžný PC (16GB RAM)": {
            "recommended": "llama3.2-3b + deepseek",
            "max_model": "codellama-7b (s omezením)",
            "docker_size": "4-5 GB",
            "performance": "Dobrá rychlost",
            "coding_quality": "Výborné pro běžný vývoj"
        },
        "Gaming PC (32GB RAM)": {
            "recommended": "codellama-7b + llama3.2-3b",
            "max_model": "codestral-22b (těsně)",
            "docker_size": "18 GB",
            "performance": "Velmi dobrá",
            "coding_quality": "Profesionální úroveň"
        },
        "Server/Workstation (64GB+)": {
            "recommended": "codestral-22b + více modelů",
            "max_model": "Všechny modely",
            "docker_size": "35+ GB",
            "performance": "Excelentní",
            "coding_quality": "Maximum možné"
        }
    }

    print("   HW Konfigurace         Doporučený model        Docker  Výkon")
    print("   " + "="*75)

    for hw, specs in hw_scenarios.items():
        print(f"   {hw:<22} {specs['recommended']:<23} {specs['docker_size']:<7} {specs['performance']}")
        print(f"   {'':>23} Max: {specs['max_model']}")
        print(f"   {'':>23} → {specs['coding_quality']}")
        print()

    print(f"⚡ PRAKTICKÉ DOPORUČENÍ PRO TVŮJ SERVER:")
    print("   🎯 Pokud máš 16GB RAM → Balanced scénář (codellama-7b)")
    print("   🎯 Pokud máš 32GB RAM → Premium možné, ale těsně")
    print("   🎯 Pokud máš 64GB+ RAM → Codestral bez problémů")
    print()
    print("   💰 CENOVĚ EFEKTIVNÍ:")
    print("   ✅ llama3.2-3b (2GB) - velmi dobrý poměr kvality/HW")
    print("   ✅ deepseek-coder-1.3b (750MB) - specializovaný na kód")
    print("   ✅ codellama-7b (3.8GB) - pokud máš dost RAM")
    print()
    print("   ❌ POZOR - CODESTRAL:")
    print("   📊 13GB model + overhead = reálně 24-28GB RAM")
    print("   💸 Drahé na HW požadavky")
    print("   🐌 Pomalé na slabším HW")

    print(f"\n🚀 MOJE KONKRÉTNÍ DOPORUČENÍ:")
    print("   1️⃣  START: deepseek-coder-1.3b (750MB) - funguje všude")
    print("   2️⃣  UPGRADE: llama3.2-3b (2GB) - skvělý poměr")
    print("   3️⃣  PRO: codellama-7b (3.8GB) - pokud máš 16GB+ RAM")
    print("   4️⃣  PREMIUM: codestral-22b (13GB) - jen s 32GB+ RAM")

    print(f"\n💡 PRO TVŮJ SERVER - REALISTICKÉ PLÁNY:")
    server_plans = [
        "📦 Minimum viable: deepseek + tinyllama (1.4GB, 8GB RAM)",
        "🎯 Doporučeno: llama3.2-3b + deepseek (2.8GB, 16GB RAM)",
        "🚀 Premium: codellama-7b + llama3.2 (5.8GB, 24GB RAM)",
        "👑 Ultimate: codestral jen pokud máš 32GB+ RAM"
    ]

    for plan in server_plans:
        print(f"   {plan}")

if __name__ == "__main__":
    realistic_hw_analysis()