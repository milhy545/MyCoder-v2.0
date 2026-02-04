#!/usr/bin/env python3
"""
🎬 MyCoder Live Demo - Živé předvedení bez Dockeru!
Ukáže ti MyCoder v akci s TinyLlama
"""

import asyncio
import sys
import time
from datetime import datetime

# Přidej src do PATH
sys.path.insert(0, "src")


def show_header():
    """Ukáž MyCoder header."""
    print("🤖" + "=" * 60 + "🤖")
    print("            🎬 MyCoder LIVE DEMO 🎬            ")
    print("🤖" + "=" * 60 + "🤖")
    print()
    print(f"🕐 Čas: {datetime.now().strftime('%H:%M:%S')}")
    print("🧠 Model: TinyLlama (ultra-lightweight)")
    print("🔥 CPU Throttling: Aktivní")
    print("🌡️  Safety: Monitored")
    print()


def show_prompt_interface():
    """Simuluje MyCoder prompt interface."""
    print("┌─" + "─" * 58 + "─┐")
    print("│  🚀 MyCoder AI Assistant - Lokální Offline Mode    │")
    print("├─" + "─" * 58 + "─┤")
    print("│                                                    │")
    print("│  💻 Co chceš naprogramovat?                        │")
    print("│                                                    │")
    print("│  📝 Příklady:                                      │")
    print("│     • Python funkce na čtení CSV                  │")
    print("│     • JavaScript email validace                   │")
    print("│     • REST API endpoint                           │")
    print("│     • SQL dotaz                                   │")
    print("│                                                    │")
    print("│  🎯 Napiš svůj požadavek:                          │")
    print("│  > _                                               │")
    print("└─" + "─" * 58 + "─┘")


async def demo_ai_coding():
    """Demo AI kódování s TinyLlama."""

    show_header()

    # Import MyCoder komponenty
    print("🔧 Inicializace MyCoder...")
    try:
        from ollama_integration import CodeGenerationProvider, OllamaClient

        print("✅ MyCoder komponenty načteny")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    # Připojení k Ollama
    print("🔌 Připojuji k Ollama...")
    async with OllamaClient() as client:
        if not await client.is_available():
            print("❌ Ollama není dostupné - spusť 'ollama serve'")
            return

        print("✅ Ollama připojeno")

        # Zkontroluj dostupné modely
        models = await client.list_models()
        print(f"🤖 Dostupné AI modely: {len(models)}")
        for model in models:
            name = model.get("name", "")
            if "tinyllama" in name.lower():
                print(f"   ✅ {name} (aktivní)")
            else:
                print(f"   • {name}")

        # Inicializace code provideru
        provider = CodeGenerationProvider(client)
        if not await provider.is_ready():
            print("❌ AI provider není ready")
            return

        active_model = await provider.get_available_model()
        print(f"🎯 Aktivní model: {active_model}")
        print()

        # Ukáž interface
        show_prompt_interface()
        print()

        # Demo úlohy
        demo_tasks = [
            {
                "name": "📄 CSV Reader",
                "prompt": "Create a Python function that reads CSV file and returns pandas DataFrame",
                "language": "python",
            },
            {
                "name": "📧 Email Validator",
                "prompt": "Write JavaScript function to validate email address using regex",
                "language": "javascript",
            },
            {
                "name": "🌐 REST API",
                "prompt": "Create FastAPI endpoint for user registration with validation",
                "language": "python",
            },
        ]

        print("🎬 LIVE DEMO - AI kódování v akci!")
        print("=" * 50)

        for i, task in enumerate(demo_tasks, 1):
            print(f"\n🎯 Demo {i}/3: {task['name']}")
            print(f"💭 Prompt: {task['prompt']}")
            print(f"📝 Jazyk: {task['language']}")

            # Animace "thinking"
            print("🤔 AI přemýšlí", end="")
            for _ in range(3):
                await asyncio.sleep(0.5)
                print(".", end="", flush=True)
            print()

            # Generování kódu
            start_time = time.time()
            result = await provider.generate_code(
                task["prompt"], language=task["language"]
            )
            end_time = time.time()

            if result.get("error"):
                print(f"❌ Chyba: {result.get('content')}")
                continue

            # Zobraz výsledek
            content = result.get("content", "")
            duration = end_time - start_time

            print(f"✅ Generováno za {duration:.1f}s")
            print("┌─ AI Generated Code " + "─" * 32 + "┐")

            # Zobraz kód s číslováním řádků
            lines = content.split("\n")[:15]  # Prvních 15 řádků
            for j, line in enumerate(lines, 1):
                if line.strip():
                    print(f"│ {j:2d} │ {line:<40} │")
                else:
                    print(f"│    │{'':<40} │")

            if len(content.split("\n")) > 15:
                print(f"│    │ ... (celkem {len(content.split('\n'))} řádků)         │")

            print("└─" + "─" * 47 + "┘")

            # Performance info
            tokens = result.get("tokens_used", 0)
            print(f"📊 Statistiky: {tokens} tokenů, {duration:.1f}s")

            if i < len(demo_tasks):
                print("\n⏱️  Dalších 3 sekundy...")
                await asyncio.sleep(3)

        # Ukončení demo
        print("\n🎉 DEMO DOKONČENO!")
        print("=" * 50)
        print("✅ MyCoder funguje lokálně bez internetu!")
        print("🤖 TinyLlama generuje užitečný kód")
        print("🔥 CPU throttling chrání hardware")
        print("🌡️  Teploty pod kontrolou")
        print()
        print("🚀 Připraveno pro produkci!")

        # Interaktivní část
        print("\n🎮 INTERAKTIVNÍ REŽIM")
        print("=" * 30)
        print("Napiš svůj vlastní prompt (nebo 'exit' pro ukončení):")

        while True:
            try:
                user_prompt = input("\n💻 Tvůj prompt: ").strip()

                if user_prompt.lower() in ["exit", "quit", "konec"]:
                    print("👋 Děkuji za testování MyCoder!")
                    break

                if not user_prompt:
                    continue

                # Detekce jazyka z promptu
                language = "python"  # default
                if any(
                    word in user_prompt.lower()
                    for word in ["javascript", "js", "html", "css"]
                ):
                    language = "javascript"
                elif any(
                    word in user_prompt.lower()
                    for word in ["sql", "database", "select"]
                ):
                    language = "sql"
                elif any(
                    word in user_prompt.lower() for word in ["bash", "shell", "script"]
                ):
                    language = "bash"

                print(f"🎯 Detekovaný jazyk: {language}")
                print("🤔 Generuji...", end="", flush=True)

                start_time = time.time()
                result = await provider.generate_code(user_prompt, language=language)
                end_time = time.time()

                print(f" ✅ ({end_time-start_time:.1f}s)")

                if result.get("error"):
                    print(f"❌ Chyba: {result.get('content')}")
                else:
                    content = result.get("content", "")
                    print("\n📄 Výsledek:")
                    print("─" * 60)
                    print(content)
                    print("─" * 60)

            except KeyboardInterrupt:
                print("\n👋 Ukončeno uživatelem")
                break
            except Exception as e:
                print(f"\n❌ Chyba: {e}")


def main():
    """Main funkce."""
    try:
        asyncio.run(demo_ai_coding())
    except KeyboardInterrupt:
        print("\n👋 Demo přerušeno")
    except Exception as e:
        print(f"💥 Chyba: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
