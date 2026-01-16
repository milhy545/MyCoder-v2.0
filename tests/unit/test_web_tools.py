from pathlib import Path

import pytest

from mycoder.web_tools import WebFetcher, WebSearcher


def test_html_to_markdown_simple() -> None:
    fetcher = WebFetcher()
    html = "<h1>Title</h1><p>Hello <strong>world</strong>.</p>"

    result = fetcher._html_to_markdown(html)

    assert "# Title" in result
    assert "Hello **world**." in result


def test_cache_roundtrip(tmp_path: Path) -> None:
    fetcher = WebFetcher(cache_dir=tmp_path, cache_ttl_minutes=60)
    url = "https://example.com"
    content = "cached content"

    fetcher._cache(url, content)
    cached = fetcher._get_cached(url)

    assert cached == content


@pytest.mark.asyncio
async def test_web_searcher_placeholder_result() -> None:
    searcher = WebSearcher()

    results = await searcher.search("test query")

    assert results
    assert results[0].url == "https://example.com"
