#!/usr/bin/env python3
"""
Ukáže přesné cesty instalace MyCoder v2.1.0
"""

import os
from pathlib import Path

def show_installation_paths():
    print("📁 MyCoder v2.1.0 - INSTALAČNÍ CESTY")
    print("=" * 60)
    
    home = Path.home()
    
    print("🏠 HLAVNÍ INSTALACE:")
    print(f"   📂 Projekt:        {home}/MyCoder-v2.0/")
    print(f"   📂 Zdrojový kód:   {home}/MyCoder-v2.0/src/mycoder/")
    print(f"   📂 Testy:          {home}/MyCoder-v2.0/tests/")
    print(f"   📂 Dokumentace:    {home}/MyCoder-v2.0/docs/")
    print(f"   📂 Příklady:       {home}/MyCoder-v2.0/examples/")
    
    print("\n⚙️  POETRY VIRTUAL ENVIRONMENT:")
    print(f"   📂 .venv:          {home}/MyCoder-v2.0/.venv/")
    print(f"   📂 Python balíky:  {home}/MyCoder-v2.0/.venv/lib/python3.x/site-packages/")
    print(f"   📂 Executable:     {home}/MyCoder-v2.0/.venv/bin/")
    
    print("\n🔧 KONFIGURACE A CACHE:")
    print(f"   📂 Poetry cache:   {home}/.cache/pypoetry/")
    print(f"   📂 Pip cache:      {home}/.cache/pip/")
    
    print("\n🎯 MYCODER SPECIFICKÉ SOUBORY:")
    print(f"   📄 Aliasy:         {home}/.mycoder_aliases")
    print(f"   📄 Shell config:   {home}/.bashrc nebo {home}/.zshrc")
    
    print("\n📦 ZÁVISLOSTI (claude-cli-auth):")
    print(f"   📂 Git cache:      {home}/.cache/pypoetry/artifacts/")
    print(f"   📂 Installed pkg:  {home}/MyCoder-v2.0/.venv/lib/python3.x/site-packages/claude_cli_auth/")
    
    print("\n🗃️  RUNTIME DATA (pokud se vytvoří):")
    potential_dirs = [
        "~/.mycoder/",
        "~/.config/mycoder/", 
        "~/.local/share/mycoder/",
        "~/MyCoder-v2.0/logs/",
        "~/MyCoder-v2.0/cache/"
    ]
    
    for dir_path in potential_dirs:
        expanded = Path(dir_path).expanduser()
        print(f"   📂 {dir_path:<20} {'✅ existuje' if expanded.exists() else '⏳ vytvoří se při použití'}")
    
    print("\n💾 TEMPORÁRNÍ SOUBORY:")
    temp_files = [
        "~/MyCoder-v2.0/sample.log",
        "~/MyCoder-v2.0/log_analysis_results.json",
        "~/MyCoder-v2.0/__pycache__/",
        "~/MyCoder-v2.0/.pytest_cache/"
    ]
    
    for file_path in temp_files:
        expanded = Path(file_path).expanduser()
        print(f"   📄 {file_path:<30} {'✅' if expanded.exists() else '⏳'}")

def check_current_installation():
    print("\n" + "=" * 60)
    print("🔍 KONTROLA SOUČASNÉ INSTALACE:")
    print("=" * 60)
    
    home = Path.home()
    mycoder_dir = home / "MyCoder-v2.0"
    
    if mycoder_dir.exists():
        print(f"✅ MyCoder v2.1.0 nalezen v: {mycoder_dir}")
        
        # Check key files
        key_files = [
            "pyproject.toml",
            "src/mycoder/__init__.py", 
            "install_mycoder.sh",
            "quick_start.py",
            ".venv/pyvenv.cfg"
        ]
        
        print("\n📋 Klíčové soubory:")
        for file_path in key_files:
            full_path = mycoder_dir / file_path
            status = "✅" if full_path.exists() else "❌"
            print(f"   {status} {file_path}")
            
        # Check if in PATH/aliases
        aliases_file = home / ".mycoder_aliases"
        if aliases_file.exists():
            print(f"\n✅ Aliasy konfigurovány: {aliases_file}")
        else:
            print(f"\n⏳ Aliasy nebyly vytvořeny")
            
    else:
        print(f"❌ MyCoder v2.1.0 není nainstalován v: {mycoder_dir}")
        print("\n🚀 INSTALACE:")
        print("   curl -sSL https://raw.githubusercontent.com/milhy545/MyCoder-v2.0/main/install_mycoder.sh | bash")

def show_disk_usage():
    print("\n" + "=" * 60)
    print("💿 ODHADOVANÁ VELIKOST INSTALACE:")
    print("=" * 60)
    
    components = {
        "MyCoder v2.1.0 zdrojový kód": "~2 MB",
        "Poetry virtual environment": "~50-100 MB", 
        "Python závislosti": "~20-30 MB",
        "claude-cli-auth modul": "~1 MB",
        "Dokumentace a příklady": "~1 MB",
        "Cache a temporary files": "~5-10 MB"
    }
    
    total_min = 79  # MB
    total_max = 144 # MB
    
    for component, size in components.items():
        print(f"   📦 {component:<30} {size:>15}")
    
    print(f"\n💾 CELKOVÁ VELIKOST: ~{total_min}-{total_max} MB")
    print("   (závisí na cache a temporary files)")

if __name__ == "__main__":
    show_installation_paths()
    check_current_installation() 
    show_disk_usage()