#!/usr/bin/env python3
"""
Demo: MyCoder v2.1.0 generování kódu v AUTONOMOUS režimu
"""

import asyncio

from mycoder import MyCoder


async def code_demo():
    print("💻 MyCoder v2.1.0 - GENEROVÁNÍ KÓDU DEMO")
    print("=" * 60)

    mycoder = MyCoder()

    # Přepnutí do AUTONOMOUS režimu (simulace offline práce)
    from mycoder.adaptive_modes import OperationalMode

    await mycoder.mode_manager.transition_to_mode(
        OperationalMode.AUTONOMOUS, "Demo code generation"
    )

    print(f"🤖 Režim: {mycoder.mode_manager.current_mode.value}")
    print("📝 Dotaz: Vytvoř Python funkci pro analýzu log souborů")

    # V AUTONOMOUS režimu MyCoder použije templates a patterns
    result = await mycoder.process_request(
        "Vytvoř Python funkci pro analýzu log souborů s error handling a type hints"
    )

    print("\n" + "=" * 60)
    print("🎯 VYGENEROVANÝ KÓD:")
    print("=" * 60)
    print(result.get("content", "No content"))

    # Ukázka dalších schopností
    print("\n" + "=" * 60)
    print("🔧 DALŠÍ SCHOPNOSTI V AUTONOMOUS REŽIMU:")
    print("=" * 60)

    capabilities = [
        "✅ Template-based kód generování",
        "✅ Python pattern recognition",
        "✅ Základní refactoring návrhy",
        "✅ File operace a čtení kódu",
        "✅ Syntax checking",
        "✅ Dokumentace templates",
        "✅ Error handling patterns",
        "✅ Best practices doporučení",
    ]

    for cap in capabilities:
        print(f"   {cap}")

    print(f"\n💡 V režimu {mycoder.mode_manager.current_mode.value} pracuje MyCoder:")
    print("   • Bez internetu a cloud služeb")
    print("   • S lokálními templates a patterns")
    print("   • S built-in knowledge base")
    print("   • Rychle a spolehlivě offline")


if __name__ == "__main__":
    asyncio.run(code_demo())
