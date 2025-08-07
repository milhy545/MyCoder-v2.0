#!/bin/bash

# 🗑️ MyCoder v2.0 - Odinstalační script
# Použití: ./uninstall_mycoder.sh

set -e

echo "🗑️  MyCoder v2.0 - ODINSTALACE"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

INSTALL_DIR="$HOME/MyCoder-v2.0"
ALIAS_SCRIPT="$HOME/.mycoder_aliases"

# Check if installed
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "MyCoder v2.0 není nainstalován v $INSTALL_DIR"
    exit 1
fi

echo "📍 Nalezena instalace v: $INSTALL_DIR"

# Show what will be removed
echo
echo "🗂️  CO BUDE ODSTRANĚNO:"
echo "   📂 Hlavní projekt:    $INSTALL_DIR"
echo "   📂 Virtual environment: $INSTALL_DIR/.venv/"
echo "   📄 Aliasy:            $ALIAS_SCRIPT"
echo "   📄 Shell konfig:      odkazy z ~/.bashrc nebo ~/.zshrc"

# Calculate size
if command -v du &> /dev/null; then
    INSTALL_SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1 || echo "neznámá")
    echo "   💾 Velikost:          $INSTALL_SIZE"
fi

echo
print_warning "Tato akce je NEVRATNÁ!"
read -p "Pokračovat v odinstalaci? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Odinstalace zrušena"
    exit 0
fi

echo
echo "🧹 ODINSTALOVÁNÍ..."

# Remove main directory
if [ -d "$INSTALL_DIR" ]; then
    print_status "Odstraňuji hlavní projekt..."
    rm -rf "$INSTALL_DIR"
    print_status "Projekt odstraněn: $INSTALL_DIR"
fi

# Remove aliases file
if [ -f "$ALIAS_SCRIPT" ]; then
    print_status "Odstraňuji aliasy..."
    rm -f "$ALIAS_SCRIPT"
    print_status "Aliasy odstraněny: $ALIAS_SCRIPT"
fi

# Remove from shell profiles
for SHELL_PROFILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$SHELL_PROFILE" ]; then
        if grep -q "source $ALIAS_SCRIPT" "$SHELL_PROFILE"; then
            print_status "Odstraňuji z $SHELL_PROFILE..."
            # Create backup
            cp "$SHELL_PROFILE" "$SHELL_PROFILE.bak.$(date +%s)"
            # Remove the line
            grep -v "source $ALIAS_SCRIPT" "$SHELL_PROFILE" > "${SHELL_PROFILE}.tmp" && mv "${SHELL_PROFILE}.tmp" "$SHELL_PROFILE"
            print_status "Odkaz odstraněn z $SHELL_PROFILE"
        fi
    fi
done

# Optional: Clean Poetry cache  
echo
read -p "Odstranit také Poetry cache? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v poetry &> /dev/null; then
        print_status "Čistím Poetry cache..."
        poetry cache clear . --all 2>/dev/null || true
        print_status "Poetry cache vyčištěn"
    fi
fi

# Optional: Clean pip cache
read -p "Odstranit také pip cache? (y/N): " -n 1 -r  
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v pip3 &> /dev/null; then
        print_status "Čistím pip cache..."
        pip3 cache purge 2>/dev/null || true
        print_status "Pip cache vyčištěn"
    fi
fi

echo
echo "🎉 ODINSTALACE DOKONČENA!"
echo "========================"
print_status "MyCoder v2.0 byl úspěšně odstraněn"
print_status "Aliasy a shell konfigurace vyčištěny"

echo
echo "⚠️  POZNÁMKY:"
echo "   • Restart terminálu pro načtení změn"  
echo "   • Poetry a Python zůstávají nainstalovány"
echo "   • Backup shell konfigu: ~/.bashrc.bak.* nebo ~/.zshrc.bak.*"

echo
print_status "Systém je čistý! 🧹"