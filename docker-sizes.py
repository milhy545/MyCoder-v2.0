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
    
    # Configuration scenarios  
    print(f"\n🎯 INSTALAČNÍ SCÉNÁŘE:")
    scenarios = {
        "Minimum (testing)": {
            "models": ["tinyllama:1.1b-chat-v1.0"],
            "use_case": "Test & development"
        },
        "Lightweight": {
            "models": ["deepseek-coder:1.3b-base-q4_0", "llama3.2:1b-instruct-q4_0"],
            "use_case": "Fast coding assistant"
        },
        "Balanced": {
            "models": ["codellama:7b-instruct-q4_0", "llama3.2:3b-instruct-q4_0"],
            "use_case": "Good performance/size ratio"
        },
        "Premium": {
            "models": ["codestral:22b-v0.1-q4_0", "mistral:7b-instruct-v0.3-q4_0"],
            "use_case": "Best Mistral AI coding"
        },
        "Ultimate": {
            "models": ["codestral:22b-v0.1-q8_0", "codestral:22b-v0.1-q4_0"],
            "use_case": "Maximum code quality"
        },
        "Complete": {
            "models": list(models.keys()),
            "use_case": "All models available"
        }
    }
    
    print("   Scénář        Velikost     Modely                    Použití")
    print("   " + "="*75)
    
    for scenario, config in scenarios.items():
        total_size = total_base
        for model in config["models"]:
            total_size += model_sizes_gb[model]
        
        size_str = f"{total_size/1000:.1f} GB" if total_size > 1000 else f"{total_size:.0f} MB"
        model_count = len(config["models"])
        
        print(f"   {scenario:<12} {size_str:>8} {model_count:>2} models            {config['use_case']}")
    
    print(f"\n💾 DISKOVÝ PROSTOR:")
    print("   🔹 Doporučeno: min. 10 GB volného místa") 
    print("   🔹 Optimální: 15-20 GB pro všechny modely")
    print("   🔹 Docker volumes: další 2-5 GB")
    
    print(f"\n🚀 DOPORUČENÍ PRO RŮZNÉ POUŽITÍ:")
    recommendations = {
        "Vývojář (laptop)": "Lightweight - 2.6 GB",
        "Kódování (desktop)": "Balanced - 4.6 GB", 
        "Mistral fan": "Premium - 17.7 GB",
        "AI research": "Ultimate - 36.6 GB",
        "Production server": "Complete - všechny modely"
    }
    
    for use_case, recommendation in recommendations.items():
        print(f"   👤 {use_case:<20} → {recommendation}")
    
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