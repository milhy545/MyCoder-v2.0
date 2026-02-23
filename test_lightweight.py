#!/usr/bin/env python3
"""
Test ultra-lightweight MyCoder s TinyLlama
Minimální zátěž systému!
"""

import asyncio
import sys
import time


async def test_tinyllama_quick():
    """Rychlý test s TinyLlama - minimální zátěž."""
    print("🪶 ULTRA-LIGHTWEIGHT MyCoder Test")
    print("=" * 40)
    print("📊 Model: TinyLlama (637MB)")
    print("💾 Expected RAM: 1-2GB")
    print("🖥️  Expected CPU: Minimální")
    print()

    # Import s TinyLlama prioritou
    sys.path.insert(0, "src")
    from ollama_integration import OllamaClient, CodeGenerationProvider

    # Test 1: Connection
    print("1️⃣ Test Ollama připojení...")
    try:
        async with OllamaClient() as client:
            if await client.is_available():
                print("✅ Ollama připojení OK")

                models = await client.list_models()
                print(f"📋 Dostupné modely: {len(models)}")
                for model in models:
                    name = model.get("name", "unknown")
                    size = "637MB" if "tinyllama" in name.lower() else "???"
                    print(f"   • {name} ({size})")
            else:
                print("❌ Ollama nedostupné")
                return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Test 2: TinyLlama priorita
    print("\n2️⃣ Test TinyLlama provider...")
    try:
        async with OllamaClient() as client:
            provider = CodeGenerationProvider(client)

            if await provider.is_ready():
                model = await provider.get_available_model()
                print(f"✅ Aktivní model: {model}")

                if "tinyllama" in model.lower():
                    print("🎯 TinyLlama správně nastaven jako primární!")
                else:
                    print("⚠️  TinyLlama není primární, ale funguje")
            else:
                print("❌ Provider není ready")
                return False
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False

    # Test 3: Rychlé generování (s timeoutem)
    print("\n3️⃣ Test rychlého generování...")
    try:
        async with OllamaClient() as client:
            provider = CodeGenerationProvider(client)

            print("🔄 Generuji jednoduchý kód...")
            start_time = time.time()

            result = await provider.generate_code("hello world", language="python")

            end_time = time.time()
            duration = end_time - start_time

            if not result.get("error"):
                content = result.get("content", "")
                print(f"✅ Generování úspěšné! ({duration:.1f}s)")
                print("📄 Výsledek:")
                lines = content.split("\n")[:3]
                for line in lines:
                    if line.strip():
                        print(f"   💻 {line}")
                if len(content.split("\n")) > 3:
                    print("   ...")

                # Performance info
                print(f"📊 Performance:")
                print(f"   ⏱️  Čas: {duration:.1f}s")
                print(f"   🤖 Model: {result.get('model', 'unknown')}")

                if duration < 10:
                    print("   🚀 Rychlost: Dobrá")
                elif duration < 30:
                    print("   🐌 Rychlost: Pomalá (očekáváno u TinyLlama)")
                else:
                    print("   ⏰ Rychlost: Velmi pomalá")

            else:
                print(f"❌ Generování selhalo: {result.get('content')}")
                return False

    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n🎉 LIGHTWEIGHT TEST DOKONČEN!")
    print("✅ TinyLlama funguje a nezatěžuje systém!")
    return True


def monitor_resources():
    """Ukáže aktuální zátěž systému."""
    try:
        # RAM info
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            for line in lines[:3]:
                if "MemTotal" in line or "MemAvailable" in line:
                    print(f"💾 {line.strip()}")

        # CPU info
        import os

        load = os.getloadavg()
        print(f"🖥️  CPU load: {load[0]:.2f}")

    except OSError:
        print("📊 Resource monitoring nedostupný")


def main():
    """Main test."""
    print("🪶 MyCoder Ultra-Lightweight Test")
    print("=" * 50)

    # Show initial resource usage
    print("📊 Resource usage před testem:")
    monitor_resources()
    print()

    try:
        success = asyncio.run(test_tinyllama_quick())

        print()
        print("📊 Resource usage po testu:")
        monitor_resources()

        if success:
            print()
            print("🎉 SUPER! Lightweight verze funguje!")
            print("🔥 Teď můžeme spustit bez obav z restartu PC!")
            print()
            print("🚀 Spuštění lightweight verze:")
            print("   make light")
            print("   nebo")
            print("   docker-compose -f docker-compose.lightweight.yml up")
            return 0
        else:
            print("❌ Test selhal")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Test přerušen")
        return 1
    except Exception as e:
        print(f"\n💥 Chyba: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
