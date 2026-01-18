"""Web search and fetch tools."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass
class WebContent:
    url: str
    content: str
    fetched_at: str
    content_type: str


class WebFetcher:
    """Fetch and process web content."""

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_minutes: int = 15):
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch(self, url: str, prompt: str = "") -> Dict[str, Any]:
        cached = self._get_cached(url)
        if cached:
            return {"success": True, "content": cached, "cached": True}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                if url.startswith("http://"):
                    url = "https://" + url[7:]

                async with session.get(url) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"HTTP {response.status}"}

                    content_type = response.headers.get("content-type", "")
                    if "text/html" in content_type:
                        html = await response.text()
                        content = self._html_to_markdown(html)
                    else:
                        content = await response.text()

                    self._cache(url, content)

                    if prompt:
                        content = await self._process_with_prompt(content, prompt)

                    return {
                        "success": True,
                        "content": content,
                        "url": str(response.url),
                        "cached": False,
                    }

        except aiohttp.ClientError as exc:
            return {"success": False, "error": str(exc)}

    def _html_to_markdown(self, html: str) -> str:
        import re

        html = re.sub(r"<script[^>]*>[\s\S]*?</script[^>]*>", "", html, flags=re.I)
        html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.I)

        html = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", html, flags=re.I)
        html = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", html, flags=re.I)
        html = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", html, flags=re.I)
        html = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", html, flags=re.I | re.S)
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
        html = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html, flags=re.I)
        html = re.sub(
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            r"[\2](\1)",
            html,
            flags=re.I,
        )
        html = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.I)
        html = re.sub(
            r"<pre[^>]*>(.*?)</pre>", r"```\n\1\n```", html, flags=re.I | re.S
        )
        html = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", html, flags=re.I)
        html = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", html, flags=re.I)

        html = re.sub(r"<[^>]+>", "", html)

        html = re.sub(r"\n\s*\n\s*\n", "\n\n", html)
        html = html.strip()

        return html[:50000]

    async def _process_with_prompt(self, content: str, prompt: str) -> str:
        return f"Content summary for: {prompt}\n\n{content[:5000]}"

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached(self, url: str) -> Optional[str]:
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{self._cache_key(url)}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data["fetched_at"])
            if datetime.now() - cached_at < self.cache_ttl:
                return data["content"]
        except Exception:
            pass

        return None

    def _cache(self, url: str, content: str) -> None:
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{self._cache_key(url)}.json"
        data = {
            "url": url,
            "content": content,
            "fetched_at": datetime.now().isoformat(),
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")


class WebSearcher:
    """Web search using available search APIs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        if not query:
            return []

        return [
            SearchResult(
                title=f"Search result for: {query}",
                url="https://example.com",
                snippet="Web search requires API configuration.",
            )
        ]
