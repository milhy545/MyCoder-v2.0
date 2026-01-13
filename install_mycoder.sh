#!/bin/bash

# 🤖 MyCoder v2.1.0 - Automatický instalátor
# Použití: curl -sSL https://raw.githubusercontent.com/milhy545/MyCoder-v2.0/main/install_mycoder.sh | bash

set -e

echo "🤖 MyCoder v2.1.0 - Automatická instalace"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on supported OS
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "Nepodporovaný OS. Podporujeme Linux a macOS."
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 není nainstalován. Nainstaluj Python 3.10-3.13"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION nalezen, ale vyžadujeme $REQUIRED_VERSION+"
    exit 1
fi

print_status "Python $PYTHON_VERSION ✓"

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git není nainstalován. Nainstaluj git."
    exit 1
fi

print_status "Git nalezen ✓"

# Install Poetry if not present
if ! command -v poetry &> /dev/null; then
    print_warning "Poetry není nainstalován. Instaluji Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v poetry &> /dev/null; then
        print_error "Instalace Poetry selhala. Nainstaluj ručně: https://python-poetry.org/docs/#installation"
        exit 1
    fi
fi

print_status "Poetry nalezen ✓"

# Create installation directory
INSTALL_DIR="$HOME/MyCoder"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "MyCoder již existuje v $INSTALL_DIR"
    read -p "Chceš přeinstalovat? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        print_status "Stará instalace odstraněna"
    else
        print_status "Používám existující instalaci"
    fi
fi

# Clone MyCoder v2.1.0
if [ ! -d "$INSTALL_DIR" ]; then
    print_status "Stahuji MyCoder v2.1.0..."
    git clone https://github.com/milhy545/MyCoder-v2.0.git "$INSTALL_DIR"
fi

# Navigate to directory
cd "$INSTALL_DIR"

# Install dependencies
print_status "Instaluji závislosti..."
poetry install

# Test installation
print_status "Testuji instalaci..."
if poetry run python -c "from mycoder import MyCoder; print('Import test passed')" &> /dev/null; then
    print_status "Instalace úspěšná!"
else
    print_error "Test importu selhal"
    exit 1
fi

# Create convenient aliases
ALIAS_SCRIPT="$HOME/.mycoder_aliases"
cat > "$ALIAS_SCRIPT" << 'EOF'
#!/bin/bash
# MyCoder v2.1.0 aliases

alias mycoder-shell="cd ~/MyCoder-v2.0 && poetry shell"
alias mycoder-test="cd ~/MyCoder-v2.0 && poetry run python test_integration.py"
alias mycoder-demo="cd ~/MyCoder-v2.0 && poetry run python network_demo.py"

# Function to run MyCoder directly
mycoder-run() {
    cd ~/MyCoder-v2.0 && poetry run python -c "
import asyncio
from mycoder import MyCoder

async def main():
    mycoder = MyCoder()
    result = await mycoder.process_request('$1')
    print('Odpověď:', result.get('content', 'No response'))

asyncio.run(main())
"
}
EOF

# Add aliases to shell profile
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
fi

if [ -n "$SHELL_PROFILE" ]; then
    if ! grep -q "source $ALIAS_SCRIPT" "$SHELL_PROFILE"; then
        echo "source $ALIAS_SCRIPT" >> "$SHELL_PROFILE"
        print_status "Aliasy přidány do $SHELL_PROFILE"
    fi
fi

echo
echo "🎉 INSTALACE DOKONČENA!"
echo "======================"
print_status "MyCoder v2.1.0 nainstalován do: $INSTALL_DIR"
print_status "Aliasy vytvořeny v: $ALIAS_SCRIPT"

echo
echo "📁 INSTALAČNÍ CESTY:"
echo "   📂 Hlavní projekt:    $INSTALL_DIR"
echo "   📂 Zdrojový kód:      $INSTALL_DIR/src/mycoder/"
echo "   📂 Virtual env:       $INSTALL_DIR/.venv/"
echo "   📂 Python balíky:     $INSTALL_DIR/.venv/lib/python*/site-packages/"
echo "   📄 Aliasy:            $ALIAS_SCRIPT"
echo "   📄 Shell konfig:      $SHELL_PROFILE"
echo
echo "💾 VELIKOST INSTALACE:"
INSTALL_SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1 || echo "~80MB")
echo "   📊 Celková velikost:  $INSTALL_SIZE"
echo
echo "🚀 SPUŠTĚNÍ:"
echo "   cd ~/MyCoder-v2.0 && poetry shell"
echo "   python test_integration.py"
echo
echo "📱 ALIASY (po restartu terminálu):"
echo "   mycoder-shell    # Vstup do prostředí"
echo "   mycoder-test     # Spusť testy"
echo "   mycoder-demo     # Ukázka režimů"
echo "   mycoder-run 'tvůj dotaz'  # Přímý dotaz"
echo
echo "📚 DOKUMENTACE:"
echo "   cat ~/MyCoder-v2.0/install_guide.md"
echo
print_status "Ready to code! 🤖"