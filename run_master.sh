#!/bin/bash
# run_master.sh - MyCoder v2.0 Interactive CLI Launcher

# 1. Zkontroluj, zda je nainstalovaný 'rich'
if ! python3 -c "import rich" &> /dev/null; then
    echo "Instaluji chybějící závislost: rich..."
    pip install rich > /dev/null 2>&1
fi

# 2. Nastav základní ENV proměnné
if [ -z "$INCEPTION_API_KEY" ]; then
    echo "WARN: INCEPTION_API_KEY není nastaven. Mercury funkce budou omezené."
fi

echo "Initializing Cyberpunk Interface..."
python3 -m src.cli_interactive
