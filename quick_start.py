#!/usr/bin/env python3
"""
🚀 MyCoder v2.0 - Quick Start
Spusť tento script pro okamžité vyzkoušení MyCoder v2.0
"""

import asyncio
import sys
from pathlib import Path

def print_header():
    print("🤖 MyCoder v2.0 - QUICK START")
    print("=" * 50)
    print("Vítej v MyCoder v2.0! Zkusme základní funkce...")
    print()

async def quick_demo():
    try:
        # Import test
        print("📦 1. Test importů...")
        from mycoder import MyCoder, EnhancedMyCoder, AdaptiveModeManager, OperationalMode
        print("   ✅ Všechny moduly nalezeny")
        
        # Initialization test  
        print("\n🚀 2. Inicializace MyCoder...")
        mycoder = MyCoder()
        print(f"   ✅ MyCoder inicializován v režimu: {mycoder.mode_manager.current_mode.value}")
        
        # Mode detection test
        print("\n🔍 3. Detekce dostupných služeb...")
        manager = AdaptiveModeManager()
        print(f"   📊 Současný režim: {manager.current_mode.value}")
        print("   📋 Dostupné režimy:", [mode.value for mode in OperationalMode])
        
        # Simple request test
        print("\n💻 4. Test jednoduchého dotazu...")
        prompt = "Vytvoř jednoduchou Python funkci pro hello world"
        
        result = await mycoder.process_request(prompt)
        
        if result.get('content'):
            print("   ✅ Dotaz zpracován úspěšně!")
            print("   📄 Odpověď:")
            print("   " + "-" * 40)
            # Show first few lines of response
            content = result['content']
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            if len(content.split('\n')) > 10:
                print("   ... (zkráceno)")
        else:
            print("   ⚠️  Žádná odpověď (normální v offline režimu)")
        
        print(f"\n   🔧 Použitý režim: {manager.current_mode.value}")
        
        # Enhanced MyCoder test
        print("\n⚡ 5. Test Enhanced MyCoder...")
        enhanced = EnhancedMyCoder()
        print("   ✅ Enhanced MyCoder připraven")
        print(f"   🎯 Režim: {enhanced.mode_manager.current_mode.value}")
        
        print("\n" + "=" * 50)
        print("🎉 QUICK START DOKONČEN!")
        print("=" * 50)
        
        print("\n📚 CO DĚLAT DÁLE:")
        print("   • python test_integration.py  - Kompletní test")
        print("   • python network_demo.py      - Demo režimů") 
        print("   • python generated_log_analyzer.py - Příklad kódu")
        
        print("\n💡 POUŽITÍ V KÓDU:")
        print("   from mycoder import MyCoder")
        print("   mycoder = MyCoder()")
        print("   result = await mycoder.process_request('tvůj dotaz')")
        
        print("\n🔧 CLI POUŽITÍ:")
        print("   poetry run mycoder --help")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import chyba: {e}")
        print("\n🔧 ŘEŠENÍ:")
        print("   1. Ujisti se, že jsi v poetry shell:")
        print("      poetry shell")
        print("   2. Nebo použij:")
        print("      poetry run python quick_start.py")
        return False
        
    except Exception as e:
        print(f"❌ Neočekávaná chyba: {e}")
        print("\n📞 PODPORA:")
        print("   • Zkontroluj install_guide.md")
        print("   • GitHub: https://github.com/milhy545/MyCoder-v2.0")
        return False

def main():
    print_header()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.10-3.13 je vyžadován")
        sys.exit(1)
    
    # Run demo
    success = asyncio.run(quick_demo())
    
    if success:
        print("\n✅ MyCoder v2.0 je připraven k použití!")
        print("🚀 Happy coding! 🤖")
    else:
        print("\n❌ Problém s instalací. Zkontroluj dokumentaci.")
        sys.exit(1)

if __name__ == "__main__":
    main()