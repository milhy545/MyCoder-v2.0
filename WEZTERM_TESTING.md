# WezTerm Testování - Návod pro Claude Code

## 🎯 Účel

WezTerm umožňuje Claude Code ovládat interaktivní terminálové aplikace (jako setup wizard) prostřednictvím CLI API.

## 📋 Předpoklady

- WezTerm nainstalovaný (flatpak nebo nativní)
- Claude Code spuštěný z WezTerm terminálu
- Tento projekt: `/home/milhy777/Develop/MyCoder-v2.0`

## 🚀 Základní workflow

### 1. Spustit wizard v nové záložce

```bash
./test_wizard_wezterm.sh spawn
```

Output:
```
✅ Wizard běží v pane: 7
💾 Pane ID uloženo do .wizard_pane_id
```

### 2. Přečíst co wizard zobrazuje

```bash
./test_wizard_wezterm.sh read
```

nebo s konkrétním pane ID:

```bash
./test_wizard_wezterm.sh read 7
```

### 3. Poslat vstup do wizardu

Poslat Enter (výchozí volba):
```bash
./test_wizard_wezterm.sh send 7
```

Poslat konkrétní odpověď (např. "a" pro ano):
```bash
./test_wizard_wezterm.sh send 7 'a'
```

Poslat číslo (výběr z nabídky):
```bash
./test_wizard_wezterm.sh send 7 '2'
```

### 4. Zavřít wizard

```bash
./test_wizard_wezterm.sh kill
```

nebo konkrétní pane:

```bash
./test_wizard_wezterm.sh kill 7
```

### 5. Zobrazit všechny panes

```bash
./test_wizard_wezterm.sh list
```

## 🔧 Přímo přes WezTerm CLI (flatpak)

Pokud potřebujete přímý přístup:

### Spustit wizard
```bash
PANE_ID=$(flatpak run --command=wezterm org.wezfurlong.wezterm cli spawn \
  --pane-id 0 --cwd "$PWD" -- bash -c \
  'export PATH="$HOME/.local/bin:$PATH"; poetry run dictation setup; sleep 300')
echo "Wizard v pane: $PANE_ID"
```

### Přečíst output
```bash
flatpak run --command=wezterm org.wezfurlong.wezterm cli get-text --pane-id 7 | tail -40
```

### Poslat Enter
```bash
flatpak run --command=wezterm org.wezfurlong.wezterm cli send-text --pane-id 7 $'\n'
```

### Poslat text + Enter
```bash
flatpak run --command=wezterm org.wezfurlong.wezterm cli send-text --pane-id 7 'a'$'\n'
```

### Zavřít pane
```bash
flatpak run --command=wezterm org.wezfurlong.wezterm cli kill-pane --pane-id 7
```

## 📝 Typický testovací scénář

```bash
# 1. Spustit wizard
./test_wizard_wezterm.sh spawn
# → Output: Wizard běží v pane: 7

# 2. Počkat 2s a přečíst první krok
sleep 2 && ./test_wizard_wezterm.sh read

# 3. Vybrat výchozí audio zařízení (Enter)
./test_wizard_wezterm.sh send 7

# 4. Přečíst krok 2
sleep 1 && ./test_wizard_wezterm.sh read

# 5. Spustit test mikrofonu (Enter)
./test_wizard_wezterm.sh send 7

# 6. Počkat 6s na dokončení testu a přečíst výsledky
sleep 6 && ./test_wizard_wezterm.sh read

# 7. Pokračovat (a = ano)
./test_wizard_wezterm.sh send 7 'a'

# ... pokračovat podle potřeby

# Nakonec zavřít
./test_wizard_wezterm.sh kill
```

## 💡 Tipy pro Claude Code

### Read pattern - sledování změn
```bash
# Před odesláním vstupu
./test_wizard_wezterm.sh read 7 > before.txt

# Poslat vstup
./test_wizard_wezterm.sh send 7 'a'

# Počkat na zpracování
sleep 2

# Přečíst nový stav
./test_wizard_wezterm.sh read 7 > after.txt

# Porovnat změny
diff before.txt after.txt
```

### Detekce promptu
```bash
# Zjistit jestli wizard čeká na vstup
./test_wizard_wezterm.sh read 7 | grep -E "(Vyberte|Enter|a/n):" && echo "Čeká na vstup"
```

### Auto-completion celého wizardu
```bash
# Automaticky projít celý wizard s výchozími hodnotami
PANE=$(./test_wizard_wezterm.sh spawn | grep "pane:" | awk '{print $NF}')

for i in {1..10}; do
  sleep 2
  ./test_wizard_wezterm.sh read $PANE | tail -5
  ./test_wizard_wezterm.sh send $PANE  # Poslat Enter
done

./test_wizard_wezterm.sh kill $PANE
```

## 🐛 Řešení problémů

### "no such pane" error
```bash
# Zobrazit aktivní panes
./test_wizard_wezterm.sh list

# Pane už možná skončil - zkontrolovat jestli proces běží
ps aux | grep "dictation setup"
```

### Wizard nereaguje na vstup
```bash
# Zkontrolovat jestli wizard opravdu čeká
./test_wizard_wezterm.sh read | grep -E "(:|\?)" | tail -3

# Možná potřebuje více času
sleep 3 && ./test_wizard_wezterm.sh send 7
```

### Text se vloží ale nezpracuje
```bash
# Použít send-text s explicitním newline
flatpak run --command=wezterm org.wezfurlong.wezterm cli send-text --pane-id 7 "a"$'\n'
```

## 📚 WezTerm CLI Reference

Dokumentace: https://wezterm.org/cli/cli/index.html

Hlavní příkazy:
- `spawn` - Vytvořit nový tab/pane
- `get-text` - Přečíst obsah pane
- `send-text` - Poslat text do pane
- `kill-pane` - Zavřít pane
- `list` - Zobrazit všechny windows/tabs/panes

## 🎓 Lessons Learned

1. **Flatpak wrapping**: WezTerm CLI musí být volán přes `flatpak run --command=wezterm org.wezfurlong.wezterm cli`
2. **Newlines**: Použít `$'\n'` pro Enter, ne jen `\n`
3. **Timing**: Vždy dát sleep mezi příkazy (wizard potřebuje čas na zpracování)
4. **Pane persistence**: Wizard pane zůstává živý jen pokud má co dělat (proto `sleep 300` na konci)
5. **Reading output**: `tail` je váš přítel - wizard má dlouhý output
6. **Auto-read**: `get-text` vrací CELÝ buffer včetně scrollbacku, ne jen viditelnou část

## ✅ Výhody WezTerm testování

- ✅ Můžu testovat interaktivní aplikace
- ✅ Vidím real-time output
- ✅ Můžu posílat vstup programově
- ✅ Můžu spustit více wizardů paralelně
- ✅ Můžu automatizovat celý testovací scénář
- ✅ Lepší než tmux (moderní, lepší API)
