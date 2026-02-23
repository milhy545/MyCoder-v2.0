#!/usr/bin/env python3
"""
Rychlý test MyCoder s lokálním Ollama (bez Dockeru)
"""

import sys
import asyncio
import subprocess

def test_ollama_connection():
    """Test jestli běží Ollama lokálně."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def start_ollama_if_needed():
    """Spustí Ollama pokud neběží."""
    if not test_ollama_connection():
        print("🚀 Spouštím Ollama...")
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Počkej chvilku než se spustí
            import time
            for i in range(10):
                time.sleep(1)
                if test_ollama_connection():
                    print("✅ Ollama běží!")
                    return True
                print(f"   Čekám... {i+1}/10")
            return False
        except Exception as e:
            print(f"❌ Nepodařilo se spustit Ollama: {e}")
            return False
    return True

async def test_mycoder_quick():
    """Rychlý test MyCoder komponenty."""
    print("🧪 RYCHLÝ TEST MyCoder")
    print("=" * 40)

    # Test 1: Ollama connection
    print("1️⃣ Test Ollama připojení...")
    if not start_ollama_if_needed():
        print("❌ Ollama není dostupné")
        return False
    print("✅ Ollama připojení OK")

    # Test 2: Import MyCoder komponenty
    print("\n2️⃣ Test importů...")
    try:
        import sys
        sys.path.insert(0, 'src')
        from ollama_integration import OllamaClient, CodeGenerationProvider
        print("✅ Importy OK")
    except ImportError as e:
        print(f"❌ Import selhał: {e}")
        return False

    # Test 3: Základní Ollama test
    print("\n3️⃣ Test Ollama API...")
    try:
        async with OllamaClient() as client:
            if await client.is_available():
                print("✅ Ollama API OK")

                models = await client.list_models()
                print(f"📋 Dostupné modely: {len(models)}")
                for model in models:
                    name = model.get('name', 'unknown')
                    print(f"   • {name}")
            else:
                print("❌ Ollama API nedostupné")
                return False
    except Exception as e:
        print(f"❌ Ollama test selhał: {e}")
        return False

    # Test 4: Code Generation Provider
    print("\n4️⃣ Test Code Generation...")
    try:
        async with OllamaClient() as client:
            provider = CodeGenerationProvider(client)

            if await provider.is_ready():
                model = await provider.get_available_model()
                print(f"✅ Code generation ready s modelem: {model}")

                # Test generation pouze pokud máme model
                if model:
                    print("\n🎯 Testování generování kódu...")
                    result = await provider.generate_code(
                        "Create a simple hello world function",
                        language="python"
                    )

                    if not result.get('error'):
                        content = result.get('content', '')
                        print(f"✅ Kód vygenerován ({len(content)} znaků)")
                        print("📄 Vygenerovaný kód:")
                        print("-" * 30)
                        # Zobraz prvních pár řádků
                        lines = content.split('\n')[:5]
                        for line in lines:
                            print(f"💻 {line}")
                        if len(content.split('\n')) > 5:
                            print("...")
                        print("-" * 30)
                        print(f"🤖 Model: {result.get('model', 'unknown')}")
                        print(f"⏱️  Čas: {result.get('generation_time', 0):.2f}s")
                    else:
                        print(f"❌ Generování selhało: {result.get('content')}")
                        return False
                else:
                    print("⚠️  Žádný model k dispozici pro generování")
            else:
                print("❌ Code generation provider není ready")
                return False
    except Exception as e:
        print(f"❌ Code generation test selhał: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎉 VŠECHNY TESTY PROŠLY!")
    print("🚀 MyCoder je připraven k použití!")
    return True

async def demo_mycoder():
    """Demo MyCoder funkcionality."""
    print("\n" + "="*50)
    print("🎬 MyCoder DEMO - Lokální test bez internetu!")
    print("="*50)

    try:
        import sys
        sys.path.insert(0, 'src')
        from ollama_integration import OllamaClient, CodeGenerationProvider

        async with OllamaClient() as client:
            provider = CodeGenerationProvider(client)

            if await provider.is_ready():
                model = await provider.get_available_model()
                print(f"🤖 Aktivní model: {model}")
                print()

                # Příklady různých úloh
                tasks = [
                    ("Vytvoř funkci pro výpočet faktoriálu", "python"),
                    ("Napiš jednoduchý REST endpoint", "python"),
                    ("Vytvoř funkci pro validaci emailu", "javascript")
                ]

                for i, (task, lang) in enumerate(tasks, 1):
                    print(f"📝 Úloha {i}: {task} ({lang})")

                    result = await provider.generate_code(task, language=lang)

                    if not result.get('error'):
                        content = result.get('content', '')
                        lines = content.split('\n')[:3]  # První 3 řádky

                        print("📄 Výsledek:")
                        for line in lines:
                            if line.strip():
                                print(f"   {line}")
                        print("   ...")
                        print(f"   ⏱️  {result.get('generation_time', 0):.1f}s")
                        print()
                    else:
                        print(f"   ❌ Chyba: {result.get('content')}")
                        print()

                print("🎉 Demo dokončeno! MyCoder funguje offline s DeepSeek! 🚀")

            else:
                print("❌ Žádné modely k dispozici")

    except Exception as e:
        print(f"❌ Demo selhalo: {e}")

def main():
    """Main funkce."""
    print("🤖 MyCoder Lokální Test (bez Dockeru)")
    print("=" * 50)

    try:
        # Základní test
        success = asyncio.run(test_mycoder_quick())

        if success:
            # Pokud test prošel, spusť demo
            asyncio.run(demo_mycoder())
            return 0
        else:
            print("\n❌ Test selhal")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Test přerušen uživatelem")
        return 1
    except Exception as e:
        print(f"\n💥 Neočekávaná chyba: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())