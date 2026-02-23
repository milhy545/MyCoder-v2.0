#!/usr/bin/env python3
"""
Interaktivní kalkulátor HW požadavků pro MyCoder
"""

def hw_calculator():
    print("🧮 MyCoder HW KALKULÁTOR")
    print("=" * 50)

    try:
        # Get user's hardware
        print("Zadej svůj hardware:")
        ram_gb = int(input("💾 RAM v GB (např. 16): "))
        cpu_cores = int(input("🧠 CPU cores (např. 8): "))
        has_gpu = input("🎮 Máš GPU? (y/n): ").lower().startswith('y')

        if has_gpu:
            gpu_vram = int(input("📊 GPU VRAM v GB (např. 8): "))
        else:
            gpu_vram = 0

        disk_gb = int(input("💿 Volný disk prostor v GB (např. 50): "))

        print("\n" + "="*50)
        print(f"📋 TVŮJ HARDWARE:")
        print(f"   RAM: {ram_gb} GB")
        print(f"   CPU: {cpu_cores} cores")
        print(f"   GPU: {'Ano' if has_gpu else 'Ne'}{f' ({gpu_vram}GB VRAM)' if has_gpu else ''}")
        print(f"   Disk: {disk_gb} GB volných")

        # Analyze what's possible
        print("\n🎯 ANALÝZA MOŽNOSTÍ:")

        models = [
            {
                "name": "tinyllama",
                "size_gb": 0.637,
                "ram_needed": 3,
                "vram_min": 0,
                "disk": 1,
                "quality": "⭐⭐☆☆☆",
                "description": "Základní testing"
            },
            {
                "name": "deepseek-coder-1.3b",
                "size_gb": 0.75,
                "ram_needed": 4,
                "vram_min": 2,
                "disk": 1,
                "quality": "⭐⭐⭐☆☆",
                "description": "Malý kódový asistent"
            },
            {
                "name": "llama3.2-3b",
                "size_gb": 2,
                "ram_needed": 7,
                "vram_min": 4,
                "disk": 3,
                "quality": "⭐⭐⭐⭐☆",
                "description": "Skvělý kompromis"
            },
            {
                "name": "codellama-7b",
                "size_gb": 3.8,
                "ram_needed": 10,
                "vram_min": 8,
                "disk": 5,
                "quality": "⭐⭐⭐⭐⭐",
                "description": "Výborné kódování"
            },
            {
                "name": "codestral-22b",
                "size_gb": 13,
                "ram_needed": 26,
                "vram_min": 16,
                "disk": 15,
                "quality": "⭐⭐⭐⭐⭐",
                "description": "Premium kódování"
            }
        ]

        print("   Model                RAM OK  GPU OK  Disk OK  Kvalita     Doporučení")
        print("   " + "="*75)

        best_models = []

        for model in models:
            ram_ok = ram_gb >= model["ram_needed"]
            gpu_ok = (not has_gpu and model["vram_min"] == 0) or (gpu_vram >= model["vram_min"])
            disk_ok = disk_gb >= model["disk"]

            ram_icon = "✅" if ram_ok else "❌"
            gpu_icon = "✅" if gpu_ok else ("⚠️" if model["vram_min"] <= 4 else "❌")
            disk_icon = "✅" if disk_ok else "❌"

            overall_ok = ram_ok and (gpu_ok or not has_gpu or model["vram_min"] == 0) and disk_ok

            if overall_ok:
                best_models.append(model)
                recommendation = "👍 FUNGUJE"
            elif ram_ok and disk_ok:
                recommendation = "⚠️  Pomalé (bez GPU)"
            else:
                recommendation = "❌ Nedoporučeno"

            print(f"   {model['name']:<18} {ram_icon}      {gpu_icon}      {disk_icon}      {model['quality']:<11} {recommendation}")

        # Best recommendation
        print(f"\n🏆 NEJLEPŠÍ VOLBA PRO TVŮJ HW:")
        if best_models:
            best = max(best_models, key=lambda x: x["size_gb"])
            print(f"   🎯 {best['name']}")
            print(f"   📊 {best['description']}")
            print(f"   💾 Zabere {best['size_gb']} GB + overhead")
            print(f"   🚀 Kvalita: {best['quality']}")
        else:
            print("   ⚠️  Žádný model nevyhovuje tvému HW")
            print("   💡 Doporučuji upgrade RAM nebo použij cloud")

        # Docker recommendation
        print(f"\n🐳 DOCKER DOPORUČENÍ:")
        if ram_gb >= 32:
            docker_scenario = "Premium (Codestral možný)"
            docker_size = "18 GB"
        elif ram_gb >= 16:
            docker_scenario = "Balanced (CodeLlama)"
            docker_size = "5 GB"
        elif ram_gb >= 8:
            docker_scenario = "Lightweight (DeepSeek)"
            docker_size = "3 GB"
        else:
            docker_scenario = "Minimum (TinyLlama)"
            docker_size = "1 GB"

        print(f"   📦 Scénář: {docker_scenario}")
        print(f"   💿 Docker velikost: {docker_size}")

        # Installation command
        print(f"\n🚀 INSTALAČNÍ PŘÍKAZ:")
        if ram_gb >= 16:
            print("   ./docker-build.sh full")
        else:
            print("   ./docker-build.sh quick")
        print("   docker-compose up")

        # Performance estimate
        print(f"\n⚡ OČEKÁVANÝ VÝKON:")
        if has_gpu and gpu_vram >= 8:
            performance = "Velmi rychlý (50-200 tokens/sec)"
        elif has_gpu and gpu_vram >= 4:
            performance = "Rychlý (30-100 tokens/sec)"
        elif cpu_cores >= 8:
            performance = "Střední (10-30 tokens/sec)"
        elif cpu_cores >= 4:
            performance = "Pomalý (5-15 tokens/sec)"
        else:
            performance = "Velmi pomalý (2-8 tokens/sec)"

        print(f"   📈 {performance}")

        # Upgrade suggestions
        if ram_gb < 32:
            print(f"\n💡 NÁVRHY NA UPGRADE:")
            if ram_gb < 16:
                print(f"   🔴 KRITICKÝ: Upgrade na 16GB RAM (+{16-ram_gb}GB)")
            elif ram_gb < 32:
                print(f"   🟡 DOPORUČENO: Upgrade na 32GB RAM (+{32-ram_gb}GB)")

            if not has_gpu:
                print("   🎮 GPU: RTX 3060/4060 (8GB) dramaticky zrychlí")
            elif gpu_vram < 8:
                print(f"   🎮 GPU upgrade: Na 8GB+ VRAM (+{8-gpu_vram}GB)")

    except ValueError:
        print("❌ Neplatný vstup. Zadej čísla.")
    except KeyboardInterrupt:
        print("\n👋 Ukončeno uživatelem")

if __name__ == "__main__":
    hw_calculator()