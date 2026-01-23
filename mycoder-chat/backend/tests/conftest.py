"""
Pytest konfigurace a fixtures
"""

import sys
from pathlib import Path

import pytest

# Přidej backend do PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
