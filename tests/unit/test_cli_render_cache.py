import sys
import os
import functools
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    from rich.console import Group
except ImportError:
    pytest.skip("Rich not installed", allow_module_level=True)

from mycoder.cli_interactive import _cached_render_ai_content

def test_cache_identity():
    """Verify that the cache returns the exact same object for identical inputs."""
    content = "This is a test message with **markdown**."
    r1 = _cached_render_ai_content(content, False)
    r2 = _cached_render_ai_content(content, False)

    assert r1 is r2, "Cache should return the exact same object instance"

def test_rendering_logic():
    """Verify that rendering produces a Group with expected content."""
    content = "Hello **World**"
    result = _cached_render_ai_content(content, False)
    assert isinstance(result, Group)
    # rich objects are hard to inspect deeply without rendering,
    # but we can check if it didn't crash and returned a Group.

def test_thinking_block_parsing():
    """Verify thinking blocks are parsed correctly."""
    content = "<thinking>Thought process</thinking>Final answer"
    result = _cached_render_ai_content(content, True) # Show thinking
    assert isinstance(result, Group)
    # Should contain at least one Panel (for thinking) and one Text/Markdown (for answer)
    # We can inspect renderables if we access internal structure, but Group stores them in .renderables
    assert len(result.renderables) >= 2
