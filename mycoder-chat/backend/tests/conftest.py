"""
Pytest konfigurace a fixtures
"""
import pytest
import sys
from pathlib import Path

# Přidej backend do PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
