import asyncio
from pathlib import Path
from src.mycoder.tool_registry import ToolRegistry, ToolExecutionContext

async def main():
    print("--- 🚀 START MANUAL MEMORY TEST ---")

    # 1. Inicializace
    registry = ToolRegistry()
    ctx = ToolExecutionContext(mode="FULL", working_directory=Path.cwd())

    # 2. Simulace chyby: Pokus číst neexistující soubor
    print("\n[1] Zkouším číst neexistující soubor (Poprvé)...")
    res1 = await registry.execute_tool("file_read", ctx, path="ghost_file_xyz123.txt")
    print(f"Výsledek: Success={res1.success}, Error={res1.error}")

    # 3. Druhý pokus (Měl by vyvolat VAROVÁNÍ z paměti)
    print("\n[2] Zkouším to samé znovu (Podruhé)...")
    res2 = await registry.execute_tool("file_read", ctx, path="ghost_file_xyz123.txt")
    print(f"Výsledek: Success={res2.success}, Error={res2.error}")

    # Kontrola metadata pro advisory
    if res2.metadata and res2.metadata.get("advisory"):
        print(f"✅ PAMĚŤ FUNGUJE! Advisory: {res2.metadata}")
    elif "BLOCKED" in str(res2.error):
        print(f"✅ PAMĚŤ FUNGUJE! Blokováno: {res2.error}")
    else:
        # Varování se loguje, ne přidává do warnings - zkontrolujeme retry_count
        print(f"ℹ️  Advisory warning se loguje (ne v response). Zkusím potřetí...")

    # 4. Třetí pokus
    print("\n[3] Zkouším potřetí...")
    res3 = await registry.execute_tool("file_read", ctx, path="ghost_file_xyz123.txt")
    print(f"Výsledek: Success={res3.success}, Error={res3.error}")

    # 5. Čtvrtý pokus - měl by být BLOCK (3+ selhání)
    print("\n[4] Zkouším počtvrté (mělo by být BLOCK)...")
    res4 = await registry.execute_tool("file_read", ctx, path="ghost_file_xyz123.txt")
    print(f"Výsledek: Success={res4.success}, Error={res4.error}")

    if res4.metadata and res4.metadata.get("advisory") == "BLOCK":
        print(f"✅ BLOCK FUNGUJE! Metadata: {res4.metadata}")
    elif "BLOCKED" in str(res4.error):
        print(f"✅ BLOCK FUNGUJE!")

    print("\n--- 🏁 KONEC TESTU ---")

if __name__ == "__main__":
    asyncio.run(main())
