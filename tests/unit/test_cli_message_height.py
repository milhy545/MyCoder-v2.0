import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from mycoder.cli_interactive import _calculate_message_height


def test_basic_height_calculation():
    """Verify height calculation for simple user messages."""
    content = "Hello world"
    role = "user"
    width = 100

    # 1 header + 1 content + 1 separator + 1 buffer = 4 (minimum for user msg?)
    # Logic:
    # lines = 1 (header)
    # newline_count = 0
    # effective_width = 96
    # char_based_lines = 1
    # content_lines = 1
    # user_multiplier: 1 * 1.1 + 1 = 2
    # lines += 2 (so 3)
    # lines += 1 (separator) -> 4
    # lines += 1 (buffer) -> 5

    lines = _calculate_message_height(content, role, width)
    assert lines >= 5


def test_ai_message_overhead():
    """Verify AI messages get extra buffer for markdown."""
    content = "Simple answer"
    width = 100

    user_lines = _calculate_message_height(content, "user", width)
    ai_lines = _calculate_message_height(content, "ai", width)

    assert ai_lines > user_lines


def test_long_content_wrapping():
    """Verify that long content increases height estimate."""
    content = "a" * 200
    width = 50  # effective ~46 -> ~5 lines

    short_content = "a" * 10

    long_lines = _calculate_message_height(content, "user", width)
    short_lines = _calculate_message_height(short_content, "user", width)

    assert long_lines > short_lines


def test_newline_counting():
    """Verify that newlines are counted correctly."""
    content_single = "line1 line2 line3"
    content_multi = "line1\nline2\nline3"
    width = 100

    lines_single = _calculate_message_height(content_single, "user", width)
    lines_multi = _calculate_message_height(content_multi, "user", width)

    assert lines_multi > lines_single


def test_caching_performance():
    """Verify that caching returns the same result efficiently."""
    content = "Cached content" * 10
    role = "ai"
    width = 80

    # Reset cache stats
    _calculate_message_height.cache_clear()

    # First call - cache miss
    res1 = _calculate_message_height(content, role, width)
    info1 = _calculate_message_height.cache_info()
    assert info1.misses == 1
    assert info1.hits == 0

    # Second call - cache hit
    res2 = _calculate_message_height(content, role, width)
    info2 = _calculate_message_height.cache_info()
    assert info2.misses == 1
    assert info2.hits == 1
    assert res1 == res2

    # Third call with different width - cache miss
    res3 = _calculate_message_height(content, role, width + 10)
    info3 = _calculate_message_height.cache_info()
    assert info3.misses == 2
    assert info3.hits == 1
    assert res3 >= 1
