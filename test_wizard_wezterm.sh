#!/bin/bash
# Helper script pro testování wizardu přes WezTerm CLI
# Umožňuje Claude Code ovládat interaktivní session

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  WezTerm Wizard Tester${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""

# Detect if running in WezTerm
if [ -z "$WEZTERM_PANE" ]; then
    echo -e "${YELLOW}⚠️  Nejste ve WezTerm session!${NC}"
    echo ""
    echo "Tento script funguje pouze když:"
    echo "  1. Máte WezTerm nainstalovaný (flatpak nebo nativní)"
    echo "  2. Spustíte ho z WezTerm terminálu"
    echo ""
    echo "Pokračuji pomocí flatpak příkazu..."
    WEZTERM_CMD="flatpak run --command=wezterm org.wezfurlong.wezterm cli"
else
    echo -e "${GREEN}✅ WezTerm session detekována (pane: $WEZTERM_PANE)${NC}"
    WEZTERM_CMD="wezterm cli"
fi

echo ""

# Function to spawn wizard
spawn_wizard() {
    echo -e "${BLUE}🚀 Spouštím wizard v nové záložce...${NC}"

    PANE_ID=$($WEZTERM_CMD spawn --pane-id 0 --cwd "$PWD" -- bash -c \
        'export PATH="$HOME/.local/bin:$PATH"; poetry run dictation setup; echo "=== WIZARD COMPLETED ==="; sleep 300')

    echo -e "${GREEN}✅ Wizard běží v pane: $PANE_ID${NC}"
    echo ""
    echo "Použití:"
    echo "  ./test_wizard_wezterm.sh read $PANE_ID    - Přečíst output"
    echo "  ./test_wizard_wezterm.sh send $PANE_ID 'a' - Poslat odpověď"
    echo "  ./test_wizard_wezterm.sh kill $PANE_ID    - Zavřít wizard"
    echo ""

    # Save pane ID for easy access
    echo "$PANE_ID" > .wizard_pane_id
    echo -e "${BLUE}💾 Pane ID uloženo do .wizard_pane_id${NC}"

    return 0
}

# Function to read wizard output
read_output() {
    local PANE_ID=${1:-.wizard_pane_id}

    if [ -f "$PANE_ID" ]; then
        PANE_ID=$(cat "$PANE_ID")
    fi

    echo -e "${BLUE}📖 Čtu output z pane $PANE_ID...${NC}"
    echo ""

    $WEZTERM_CMD get-text --pane-id "$PANE_ID" | tail -40
}

# Function to send input to wizard
send_input() {
    local PANE_ID=$1
    local TEXT=${2:-$'\n'}  # Default: Enter key

    if [ -f "$PANE_ID" ]; then
        PANE_ID=$(cat "$PANE_ID")
    fi

    echo -e "${BLUE}✍️  Posílám do pane $PANE_ID: \"$TEXT\"${NC}"

    # Send text (without --no-paste to allow newlines)
    $WEZTERM_CMD send-text --pane-id "$PANE_ID" "$TEXT"

    echo -e "${GREEN}✅ Odesláno${NC}"
}

# Function to kill wizard pane
kill_wizard() {
    local PANE_ID=${1:-.wizard_pane_id}

    if [ -f "$PANE_ID" ]; then
        PANE_ID=$(cat "$PANE_ID")
        rm -f .wizard_pane_id
    fi

    echo -e "${BLUE}🗑️  Zavírám pane $PANE_ID...${NC}"

    $WEZTERM_CMD kill-pane --pane-id "$PANE_ID" 2>&1 || echo "Pane již neexistuje"

    echo -e "${GREEN}✅ Hotovo${NC}"
}

# Function to list all panes
list_panes() {
    echo -e "${BLUE}📋 WezTerm panes:${NC}"
    echo ""

    $WEZTERM_CMD list
}

# Main command dispatcher
case "${1:-spawn}" in
    spawn)
        spawn_wizard
        ;;
    read)
        read_output "${2:-.wizard_pane_id}"
        ;;
    send)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Chyba: Musíte zadat pane ID${NC}"
            echo "Použití: $0 send <PANE_ID> [text]"
            exit 1
        fi
        send_input "$2" "${3:-$'\n'}"
        ;;
    kill)
        kill_wizard "${2:-.wizard_pane_id}"
        ;;
    list)
        list_panes
        ;;
    help|--help|-h)
        echo "Použití: $0 [COMMAND] [ARGS]"
        echo ""
        echo "Příkazy:"
        echo "  spawn           - Spustit wizard v nové WezTerm záložce"
        echo "  read [PANE_ID]  - Přečíst output z wizardu (default: uložené ID)"
        echo "  send PANE_ID [TEXT] - Poslat text do wizardu (default: Enter)"
        echo "  kill [PANE_ID]  - Zavřít wizard záložku"
        echo "  list            - Zobrazit všechny WezTerm panes"
        echo "  help            - Zobrazit tuto nápovědu"
        echo ""
        echo "Příklady:"
        echo "  $0 spawn                    # Spustit wizard"
        echo "  $0 read                     # Přečíst co je na obrazovce"
        echo "  $0 send 5                   # Poslat Enter do pane 5"
        echo "  $0 send 5 'a'               # Poslat 'a' + Enter"
        echo "  $0 kill                     # Zavřít poslední wizard"
        ;;
    *)
        echo -e "${RED}❌ Neznámý příkaz: $1${NC}"
        echo "Použijte '$0 help' pro nápovědu"
        exit 1
        ;;
esac
