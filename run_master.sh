#!/bin/bash
# run_master.sh - MyCoder v2.1.0 Master Interface
# Requires: poetry install

echo "Initializing MyCoder v2.1.0 Master Interface..."
# Spusteni pres poetry zajisti, ze mame 'rich' a ostatni deps
poetry run python -m src.cli_interactive
