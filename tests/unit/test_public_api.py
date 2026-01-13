"""Public API surface tests for the mycoder package."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import mycoder


def test_public_api_exports():
    """Core symbols should be available in the top-level package."""
    for name in [
        "MyCoder",
        "EnhancedMyCoder",
        "EnhancedMyCoderV2",
        "AdaptiveModeManager",
        "OperationalMode",
        "APIProviderRouter",
    ]:
        assert hasattr(mycoder, name)
        assert name in mycoder.__all__


def test_version_matches_expected():
    """Package version should stay in sync with release versioning."""
    assert mycoder.__version__ == "2.1.0"
