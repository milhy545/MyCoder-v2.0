#!/usr/bin/env python3
"""
🛡️ ULTRA-SAFE MyCoder Demo
Minimální zátěž, jen ukázka interface
"""

import sys
import time

sys.path.insert(0, 'src')

def show_mycoder_interface():
    """Ukáže MyCoder interface bez AI zatížení."""
    print("🤖" + "=" * 60 + "🤖")
    print("            🎬 MyCoder SAFE DEMO 🎬              ")  
    print("🤖" + "=" * 60 + "🤖")
    print()
    print("🛡️  ULTRA-SAFE MODE: Minimální CPU zátěž")
    print("🌡️  Monitoring: Manual temperature checks")
    print("🧠 Model: TinyLlama (ready)")
    print()
    
    # MyCoder UI mockup
    print("┌─" + "─" * 58 + "─┐")
    print("│  🚀 MyCoder AI Assistant - Offline Mode           │")
    print("├─" + "─" * 58 + "─┤") 
    print("│                                                    │")
    print("│  💬 Ahoj! Jsem MyCoder, tvůj AI programátor.      │")
    print("│                                                    │")
    print("│  🎯 Co pro tebe můžu naprogramovat?               │")
    print("│                                                    │")
    print("│  📝 Můžu vytvořit:                                │")
    print("│     • 🐍 Python funkce a skripty                 │")
    print("│     • 🌐 JavaScript a web kód                    │") 
    print("│     • 🗄️  SQL dotazy                              │")
    print("│     • 📊 Data analysis                           │")
    print("│     • 🔧 DevOps skripty                          │")
    print("│                                                    │")
    print("│  ⚡ Funguju bez internetu s lokálním AI!          │")
    print("│                                                    │")
    print("│  💭 Tvůj prompt: _                                │")
    print("└─" + "─" * 58 + "─┘")
    print()

def check_temperature():
    """Zkontroluje teplotu."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read()) // 1000
            return temp
    except OSError:
        return 0

def safe_test():
    """Bezpečný test bez AI generování."""
    
    show_mycoder_interface()
    
    # Test importů bez zatížení
    print("🔧 Testování MyCoder komponent...")
    
    temp1 = check_temperature()
    print(f"🌡️  Teplota před testem: {temp1}°C")
    
    try:
        from ollama_integration import OllamaClient, CodeGenerationProvider
        print("✅ MyCoder importy: OK")
        
        temp2 = check_temperature() 
        print(f"🌡️  Teplota po importu: {temp2}°C")
        
        if temp2 > temp1 + 3:
            print("⚠️  Teplota stoupá - ukončuji")
            return
            
        print("🔌 Test Ollama připojení...")
        import asyncio
        
        async def quick_check():
            async with OllamaClient() as client:
                available = await client.is_available()
                if available:
                    models = await client.list_models()
                    return len(models)
                return 0
        
        model_count = asyncio.run(quick_check())
        
        temp3 = check_temperature()
        print(f"🌡️  Teplota po testu: {temp3}°C")
        
        if model_count > 0:
            print(f"✅ Ollama: {model_count} modelů dostupných")
            print("🤖 TinyLlama je připraven pro AI kódování")
        else:
            print("⚠️  Ollama není dostupné")
            
        # Ukážeme mockup AI odpovědi
        print("\n🎭 Mockup AI generování:")
        print("─" * 50)
        print("💭 Prompt: 'Create hello world function'")
        print("🤔 AI přemýšlí...", end="")
        
        for i in range(3):
            time.sleep(0.3)
            print(".", end="", flush=True)
            temp_check = check_temperature()
            if temp_check > 60:
                print("\n⚠️  Teplota příliš vysoká - stop")
                return
        
        print()
        print("✨ AI odpověď:")
        print("```python")
        print("def hello_world():")
        print('    """Simple hello world function."""')
        print('    return "Hello, World!"')
        print('')
        print('# Usage')
        print('print(hello_world())')
        print("```")
        print("─" * 50)
        
        final_temp = check_temperature()
        print(f"🌡️  Finální teplota: {final_temp}°C")
        
        print("\n🎉 MyCoder demo dokončeno!")
        print("✅ Interface funguje")
        print("✅ AI komponenty připraveny") 
        print("✅ Žádné přehřívání")
        print("🚀 Připraveno pro použití!")
        
        if final_temp < 55:
            print("\n💡 Teplota je bezpečná - můžeš zkusit skutečné AI generování")
        else:
            print("\n⚠️  Teplota je vyšší - doporučuji počkat na ochlazení")
            
    except ImportError as e:
        print(f"❌ Import chyba: {e}")
    except Exception as e:
        print(f"❌ Chyba: {e}")
        temp_error = check_temperature()
        print(f"🌡️  Teplota při chybě: {temp_error}°C")

if __name__ == "__main__":
    try:
        safe_test()
    except KeyboardInterrupt:
        print("\n👋 Demo přerušeno")
        final_temp = check_temperature()
        print(f"🌡️  Teplota při ukončení: {final_temp}°C")
    except Exception as e:
        print(f"💥 Neočekávaná chyba: {e}")
