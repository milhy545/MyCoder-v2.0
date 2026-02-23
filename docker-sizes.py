#!/usr/bin/env python3
"""
Kalkulátor velikostí MyCoder Docker instalace s Ollama modely
"""

def show_docker_sizes():
    print("🐳 MyCoder Docker - VELIKOSTI INSTALACE")
    print("=" * 60)

    # Base components
    components = {
        "Base Ubuntu/Python image": "~400 MB",
        "MyCoder zdrojový kód": "~5 MB",
        "Python závislosti": "~30 MB",
        "Ollama binary": "~150 MB",
    }

    print("🏗️  BASE KOMPONENTY:")
    total_base = 585  # MB
    for component, size in components.items():
        print(f"   📦 {component:<30} {size:>12}")
    print(f"   {'='*44}")
    print(f"   📊 Base celkem: {total_base:>25} MB")

    # Ollama models
    print(f"\n🤖 OLLAMA MODELY:")
    models = {
        # Mistral AI code models (TOP TIER)
        "codestral:22b-v0.1-q4_0": "13.0 GB",      # Best for coding
        "codestral:22b-v0.1-q8_0": "23.0 GB",      # Highest quality
        "mistral:7b-instruct-v0.3-q4_0": "4.1 GB", # General Mistral

        # Meta code models
        "codellama:7b-instruct": "3.8 GB",
        "codellama:7b-instruct-q4_0": "2.0 GB",

        # Specialized code models
        "deepseek-coder:1.3b-base-q4_0": "750 MB",
        "deepseek-coder:6.7b-instruct-q4_0": "3.8 GB",

        # General models
        "llama3.2:3b-instruct-q4_0": "2.0 GB",
        "llama3.2:1b-instruct-q4_0": "1.3 GB",

        # Tiny models for testing
        "tinyllama:1.1b-chat-v1.0": "637 MB",
    }

    print("   Model                           Velikost    Použití")
    print("   " + "="*55)

    model_sizes_gb = {}
    for model, size in models.items():
        use_case = {
            "codestral:22b-v0.1-q4_0": "👑 Nejlepší kód",
            "codestral:22b-v0.1-q8_0": "💎 Premium kód",
            "mistral:7b-instruct-v0.3-q4_0": "🎯 Mistral AI",
            "codellama:7b-instruct": "🦙 Meta kód",
            "codellama:7b-instruct-q4_0": "⚡ Rychlý kód",
            "deepseek-coder:1.3b-base-q4_0": "🔧 Malý kód",
            "deepseek-coder:6.7b-instruct-q4_0": "🧠 Pokročilý kód",
            "llama3.2:3b-instruct-q4_0": "💬 General AI",
            "llama3.2:1b-instruct-q4_0": "⚡ Rychlý AI",
            "tinyllama:1.1b-chat-v1.0": "🧪 Testing"
        }.get(model, "📋 General")

        print(f"   {model:<30} {size:>8} {use_case}")

        # Convert to MB for calculations
        if "GB" in size:
            model_sizes_gb[model] = float(size.split()[0]) * 1000
        else:
            model_sizes_gb[model] = float(size.split()[0])

    # Configuration scenarios with HW requirements
    print(f"\n🎯 INSTALAČNÍ SCÉNÁŘE:")
    scenarios = {
        "Minimum (testing)": {
            "models": ["tinyllama:1.1b-chat-v1.0"],
            "use_case": "Test & development",
            "ram_min": "4 GB",
            "ram_rec": "8 GB",
            "cpu_min": "2 cores",
            "gpu": "Ne"
        },
        "Lightweight": {
            "models": ["deepseek-coder:1.3b-base-q4_0", "llama3.2:1b-instruct-q4_0"],
            "use_case": "Fast coding assistant",
            "ram_min": "8 GB",
            "ram_rec": "16 GB",
            "cpu_min": "4 cores",
            "gpu": "Volitelné"
        },
        "Balanced": {
            "models": ["codellama:7b-instruct-q4_0", "llama3.2:3b-instruct-q4_0"],
            "use_case": "Good performance/size ratio",
            "ram_min": "16 GB",
            "ram_rec": "32 GB",
            "cpu_min": "6 cores",
            "gpu": "Doporučeno"
        },
        "Premium": {
            "models": ["codestral:22b-v0.1-q4_0", "mistral:7b-instruct-v0.3-q4_0"],
            "use_case": "Best Mistral AI coding",
            "ram_min": "32 GB",
            "ram_rec": "64 GB",
            "cpu_min": "8 cores",
            "gpu": "Nutné (8GB+)"
        },
        "Ultimate": {
            "models": ["codestral:22b-v0.1-q8_0", "codestral:22b-v0.1-q4_0"],
            "use_case": "Maximum code quality",
            "ram_min": "64 GB",
            "ram_rec": "128 GB",
            "cpu_min": "16 cores",
            "gpu": "Nutné (16GB+)"
        },
        "Complete": {
            "models": list(models.keys()),
            "use_case": "All models available",
            "ram_min": "128 GB",
            "ram_rec": "256 GB",
            "cpu_min": "24 cores",
            "gpu": "Nutné (24GB+)"
        }
    }

    print("   Scénář        Velikost   RAM min/rec    CPU min    GPU        Použití")
    print("   " + "="*85)

    for scenario, config in scenarios.items():
        total_size = total_base
        for model in config["models"]:
            total_size += model_sizes_gb[model]

        size_str = f"{total_size/1000:.1f} GB" if total_size > 1000 else f"{total_size:.0f} MB"
        ram_str = f"{config['ram_min']}/{config['ram_rec']}"

        print(f"   {scenario:<12} {size_str:>8}   {ram_str:<10} {config['cpu_min']:<8} {config['gpu']:<10} {config['use_case']}")

    print(f"\n💾 DISKOVÝ PROSTOR:")
    print("   🔹 Doporučeno: min. 10 GB volného místa")
    print("   🔹 Optimální: 15-20 GB pro všechny modely")
    print("   🔹 Docker volumes: další 2-5 GB")

    print(f"\n🖥️  HARDWARE REQUIREMENTS DETAIL:")
    print("   💾 RAM: Modely se načítají do RAM - více RAM = rychlejší inference")
    print("   🧠 CPU: Více jader = rychlejší zpracování bez GPU")
    print("   🎮 GPU: Dramaticky zrychluje inference (10-100x)")
    print("   📏 VRAM: GPU paměť musí být větší než velikost modelu")

    print(f"\n🎮 GPU REQUIREMENTS:")
    gpu_requirements = {
        "tinyllama (637 MB)": "Žádné GPU / 2GB VRAM",
        "deepseek-1.3b (750 MB)": "2GB VRAM / GTX 1050",
        "llama3.2-3b (2 GB)": "4GB VRAM / GTX 1660",
        "codellama-7b (3.8 GB)": "8GB VRAM / RTX 3070",
        "codestral-22b (13 GB)": "16GB VRAM / RTX 4090",
        "codestral-22b-q8 (23 GB)": "24GB VRAM / RTX 6000"
    }

    for model, requirement in gpu_requirements.items():
        print(f"   📊 {model:<25} → {requirement}")

    print(f"\n⚡ VÝKONOVÉ TESTY (inference rychlost):")
    print("   💻 CPU only (16 cores):     ~10-50 tokens/sec")
    print("   🎮 RTX 3070 (8GB):          ~50-150 tokens/sec")
    print("   🚀 RTX 4090 (24GB):         ~100-300 tokens/sec")
    print("   🏆 RTX 6000 Ada (48GB):     ~200-500 tokens/sec")

    print(f"\n🚀 DOPORUČENÍ PRO RŮZNÉ HW KONFIGURACE:")
    hw_recommendations = {
        "💻 Laptop (8GB RAM)": {
            "scenario": "Lightweight",
            "size": "2.6 GB",
            "models": "deepseek + llama3.2-1b",
            "performance": "Dobrý pro coding"
        },
        "🖥️  Desktop (16GB RAM)": {
            "scenario": "Balanced",
            "size": "4.6 GB",
            "models": "codellama + llama3.2-3b",
            "performance": "Výborný pro vývoj"
        },
        "🎮 Gaming PC (32GB+RTX)": {
            "scenario": "Premium",
            "size": "17.7 GB",
            "models": "Codestral + Mistral",
            "performance": "Profesionální kódování"
        },
        "🏢 Workstation (64GB+A6000)": {
            "scenario": "Ultimate",
            "size": "36.6 GB",
            "models": "Codestral Q4+Q8",
            "performance": "Maximum kvalita"
        },
        "🏭 Server (128GB+)": {
            "scenario": "Complete",
            "size": "55 GB",
            "models": "Všechny modely",
            "performance": "Production ready"
        }
    }

    print("   Konfigurace              Scénář     Velikost   Modely")
    print("   " + "="*70)
    for hw_config, details in hw_recommendations.items():
        print(f"   {hw_config:<23} {details['scenario']:<10} {details['size']:<10} {details['models']}")
        print(f"   {'':>24} → {details['performance']}")
        print()

    print(f"\n⚡ VÝKON vs VELIKOST:")
    print("   📊 tinyllama (637 MB)     - ⭐⭐☆☆☆ kvalita, ⭐⭐⭐⭐⭐ rychlost")
    print("   📊 deepseek-1.3b (750 MB) - ⭐⭐⭐☆☆ kvalita, ⭐⭐⭐⭐☆ rychlost")
    print("   📊 llama3.2-3b (2 GB)     - ⭐⭐⭐⭐☆ kvalita, ⭐⭐⭐☆☆ rychlost")
    print("   📊 codellama-7b (3.8 GB)  - ⭐⭐⭐⭐⭐ kvalita, ⭐⭐☆☆☆ rychlost")
    print("   📊 codestral-22b (13 GB)  - ⭐⭐⭐⭐⭐ kvalita, ⭐⭐☆☆☆ rychlost")
    print("   👑 CODESTRAL = NEJLEPŠÍ PRO KÓDOVÁNÍ!")

    print(f"\n🏆 CODESTRAL BENEFITS:")
    print("   ✅ Specializovaný na programování")
    print("   ✅ Podporuje 80+ prog. jazyků")
    print("   ✅ Výborná kontextová paměť")
    print("   ✅ Přesné type hints a dokumentace")
    print("   ✅ Pokročilé debugging návrhy")

if __name__ == "__main__":
    show_docker_sizes()