#!/usr/bin/env python3
"""
Demonstrace adaptivních režimů MyCoder v2.1.0 podle síťových podmínek
"""

import asyncio
from mycoder import AdaptiveModeManager, OperationalMode

async def network_demo():
    print("🌐 MyCoder v2.1.0 - ADAPTIVNÍ REŽIMY DEMO")
    print("=" * 60)
    
    manager = AdaptiveModeManager()
    
    print(f"🔄 Počáteční režim: {manager.current_mode.value}")
    print("\n📊 Testování síťových podmínek...")
    
    # Simulace testování sítě
    print("🔍 Kontrola internetu...")
    internet_ok = True  # Simulace
    print(f"   Internet: {'✅' if internet_ok else '❌'}")
    
    print("🔍 Kontrola MCP orchestrátoru (192.168.0.58:8020)...")
    orchestrator_ok = False  # Reálně není dostupný
    print(f"   MCP Orchestrator: {'✅' if orchestrator_ok else '❌'}")
    
    print("🔍 Kontrola Claude CLI autentifikace...")
    claude_ok = False  # Není nakonfigurováno
    print(f"   Claude CLI: {'✅' if claude_ok else '❌'}")
    
    print("\n" + "="*60)
    print("🎯 DOSTUPNÉ REŽIMY A JEJICH SCHOPNOSTI:")
    print("="*60)
    
    modes = {
        OperationalMode.FULL: {
            "name": "FULL 💪",
            "description": "Všechny funkce aktivní",
            "requirements": "Internet + MCP + Claude CLI",
            "capabilities": [
                "✅ Claude AI dotazy",
                "✅ MCP orchestrátor (27 nástrojů)",
                "✅ Pokročilá paměť", 
                "✅ Git operace",
                "✅ Databázové operace",
                "✅ Web browsing"
            ]
        },
        OperationalMode.DEGRADED: {
            "name": "DEGRADED ⚡",
            "description": "Základní AI funkce",
            "requirements": "Internet + Claude CLI",
            "capabilities": [
                "✅ Claude AI dotazy",
                "❌ MCP orchestrátor",
                "⚠️  Základní paměť",
                "❌ Pokročilé nástroje"
            ]
        },
        OperationalMode.AUTONOMOUS: {
            "name": "AUTONOMOUS 🤖",
            "description": "Lokální AI processing",
            "requirements": "Pouze lokální systém",
            "capabilities": [
                "❌ Claude AI",
                "❌ MCP orchestrátor", 
                "✅ Lokální template odpovědi",
                "✅ Základní file operace",
                "✅ Systémové nástroje"
            ]
        },
        OperationalMode.RECOVERY: {
            "name": "RECOVERY 🆘",
            "description": "Nouzový režim",
            "requirements": "Minimální funkce",
            "capabilities": [
                "❌ AI funkce",
                "✅ Error reporting",
                "✅ Diagnostika systému",
                "✅ Návod k opravě"
            ]
        }
    }
    
    for mode, info in modes.items():
        print(f"\n{info['name']}")
        print(f"📋 {info['description']}")
        print(f"🔧 Požadavky: {info['requirements']}")
        print("🎯 Schopnosti:")
        for cap in info['capabilities']:
            print(f"   {cap}")
    
    print("\n" + "="*60)
    print("🔄 AUTOMATICKÉ PŘEPÍNÁNÍ REŽIMŮ:")
    print("="*60)
    
    if orchestrator_ok and claude_ok:
        optimal_mode = OperationalMode.FULL
    elif claude_ok:
        optimal_mode = OperationalMode.DEGRADED
    elif internet_ok:
        optimal_mode = OperationalMode.AUTONOMOUS
    else:
        optimal_mode = OperationalMode.RECOVERY
    
    print(f"🎯 Na základě dostupných služeb doporučuji: {optimal_mode.value}")
    print(f"📊 Současný režim: {manager.current_mode.value}")
    
    if optimal_mode != manager.current_mode:
        print(f"🔄 Automatické přepnutí na optimální režim...")
        await manager.transition_to_mode(optimal_mode, "Network conditions optimization")
        print(f"✅ Přepnuto na: {manager.current_mode.value}")
    
    print(f"\n🏆 MyCoder v2.1.0 je nyní v režimu: {manager.current_mode.value}")
    print("💡 V tomto režimu jsou k dispozici funkce uvedené výše.")

if __name__ == "__main__":
    asyncio.run(network_demo())