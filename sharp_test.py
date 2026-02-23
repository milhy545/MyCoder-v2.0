#!/usr/bin/env python3
"""
Ostrý test MyCoder v2.1.0 s reálným dotazem na programování
"""

import asyncio
import sys
from pathlib import Path

async def sharp_test():
    print("🔥 MyCoder v2.1.0 - OSTRÝ TEST")
    print("=" * 60)

    try:
        from mycoder import MyCoder, EnhancedMyCoder

        print("📝 Test dotaz: Vytvoř Python funkci pro analýzu log souborů")
        print("-" * 60)

        # Initialize Enhanced MyCoder (nejpokročilejší verze)
        mycoder = EnhancedMyCoder()
        print(f"✅ Enhanced MyCoder inicializován v režimu: {mycoder.mode_manager.current_mode.value}")

        # Reálný programátorský dotaz
        prompt = """
        Vytvoř Python funkci, která:
        1. Načte log soubor
        2. Najde všechny error a warning zprávy
        3. Spočítá statistiky (kolik errorů, warnings)
        4. Vrátí top 5 nejčastějších chyb
        5. Uloží výsledek do JSON souboru
        
        Použij moderní Python s type hints a error handling.
        """

        print("🚀 Odesílám dotaz do MyCoder v2.1.0...")
        print("⏳ Čekám na odpověď...")

        # Pokus o zpracování dotazu
        try:
            result = await mycoder.process_request(
                prompt=prompt,
                files=[Path(".")],  # Current directory context
                max_retries=3
            )

            print("\n" + "="*60)
            print("🎯 ODPOVĚĎ MYCODERA v2.1.0:")
            print("="*60)
            print(result.get('content', 'No content returned'))
            print("\n" + "="*60)

            # Check if we got a valid response
            if result.get('content'):
                print("✅ TEST ÚSPĚŠNÝ - MyCoder v2.1.0 odpověděl!")
                print(f"📊 Status: {result.get('status', 'unknown')}")
                print(f"🔧 Použitý režim: {result.get('mode', 'unknown')}")
            else:
                print("❌ TEST NEÚSPĚŠNÝ - Prázdná odpověď")

        except Exception as e:
            print(f"❌ CHYBA při zpracování dotazu: {e}")
            print("🔄 Zkouším fallback mechanismus...")

            # Test fallback mode
            await mycoder.mode_manager.transition_to_mode(
                mycoder.mode_manager.OperationalMode.RECOVERY,
                "Testing fallback"
            )
            print(f"🆘 Přepnuto do režimu: {mycoder.mode_manager.current_mode.value}")

    except Exception as e:
        print(f"💥 KRITICKÁ CHYBA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(sharp_test())