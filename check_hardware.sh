#!/bin/bash
# Script pro kontrolu hardware pro Global Dictation

echo "╔════════════════════════════════════════════════╗"
echo "║     Hardware Check - Global Dictation         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# CPU info
echo "🖥️  CPU:"
if command -v lscpu &> /dev/null; then
    CPU_MODEL=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
    CPU_CORES=$(lscpu | grep "^CPU(s):" | cut -d: -f2 | xargs)
    CPU_MHZ=$(lscpu | grep "CPU MHz" | cut -d: -f2 | xargs)

    echo "   Model: $CPU_MODEL"
    echo "   Cores: $CPU_CORES"
    echo "   MHz: $CPU_MHZ"
else
    cat /proc/cpuinfo | grep "model name" | head -1 | cut -d: -f2
fi
echo ""

# RAM info
echo "💾 RAM:"
if command -v free &> /dev/null; then
    TOTAL_RAM=$(free -h | grep Mem | awk '{print $2}')
    AVAIL_RAM=$(free -h | grep Mem | awk '{print $7}')

    echo "   Total: $TOTAL_RAM"
    echo "   Available: $AVAIL_RAM"
fi
echo ""

# Disk space
echo "💿 Disk (pro Whisper modely):"
DISK_AVAIL=$(df -h ~ | tail -1 | awk '{print $4}')
echo "   Available in home: $DISK_AVAIL"
echo ""

# Python version
echo "🐍 Python:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   $PYTHON_VERSION"
else
    echo "   ❌ Python3 není nainstalován"
fi
echo ""

# Hodnocení
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Hodnocení pro Global Dictation:"
echo ""

# Extrahuj RAM v GB (zjednodušeně)
RAM_GB=$(free -g | grep Mem | awk '{print $2}')

# Extrahuj počet jader
CORES=$(nproc 2>/dev/null || echo "1")

echo "Minimální požadavky pro Whisper modely:"
echo ""
echo "┌─────────┬──────────┬───────┬─────────────────┐"
echo "│ Model   │ RAM      │ CPU   │ Rychlost        │"
echo "├─────────┼──────────┼───────┼─────────────────┤"
echo "│ tiny    │ 0.5 GB   │ 1 GHz │ ~1-2s na 10s    │"
echo "│ base    │ 1 GB     │ 2 GHz │ ~3-5s na 10s    │"
echo "│ small   │ 2 GB     │ 2 GHz │ ~8-12s na 10s   │"
echo "│ medium  │ 5 GB     │ 3 GHz │ ~20-30s na 10s  │"
echo "└─────────┴──────────┴───────┴─────────────────┘"
echo ""

echo "Váš hardware:"
echo "   RAM: $RAM_GB GB"
echo "   CPU jádra: $CORES"
echo ""

# Doporučení
if [ "$RAM_GB" -lt 1 ]; then
    echo "⚠️  POZOR: Málo RAM (méně než 1 GB)"
    echo "   Doporučení: Použijte model 'tiny' (může být nepřesný)"
    echo "   Příkaz: poetry run dictation run --provider local --model tiny"
elif [ "$RAM_GB" -lt 2 ]; then
    echo "✅ Dostatečná RAM pro model 'base'"
    echo "   Doporučení: Použijte model 'base' (dobrý kompromis)"
    echo "   Příkaz: poetry run dictation run --provider local --model base"
elif [ "$RAM_GB" -lt 4 ]; then
    echo "✅✅ Dobrá RAM pro model 'small'"
    echo "   Doporučení: Použijte model 'base' nebo 'small'"
    echo "   Příkaz: poetry run dictation run --provider local --model small"
else
    echo "✅✅✅ Výborná RAM pro jakýkoliv model"
    echo "   Doporučení: Můžete použít i 'medium' pro nejlepší přesnost"
    echo "   Příkaz: poetry run dictation run --provider local --model medium"
fi

echo ""

if [ "$CORES" -lt 2 ]; then
    echo "⚠️  POZOR: Pouze 1 CPU jádro"
    echo "   Přepis bude pomalejší, ale mělo by to fungovat"
    echo "   Použijte model 'tiny' nebo 'base'"
else
    echo "✅ Multi-core CPU - mělo by běžet OK"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Obecné doporučení:"
echo ""

if [ "$RAM_GB" -lt 2 ] || [ "$CORES" -lt 2 ]; then
    echo "   🔸 Začněte s modelem 'base'"
    echo "   🔸 Pokud je příliš pomalý, zkuste 'tiny'"
    echo "   🔸 Očekávejte přepis 10s audia za ~5-10 sekund"
    RECOMMENDED_MODEL="base"
else
    echo "   ✅ Můžete použít model 'base' nebo 'small'"
    echo "   ✅ Očekávejte přepis 10s audia za ~3-10 sekund"
    RECOMMENDED_MODEL="base"
fi

echo ""
echo "🚀 Doporučený příkaz pro vaše HW:"
echo ""
echo "   poetry run dictation run --provider local --model $RECOMMENDED_MODEL"
echo ""

# Check disk space for models
echo "💿 Velikost Whisper modelů:"
echo "   tiny:   39 MB"
echo "   base:   74 MB"
echo "   small:  244 MB"
echo "   medium: 769 MB"
echo ""
echo "   Dostupné místo: $DISK_AVAIL"
echo ""
