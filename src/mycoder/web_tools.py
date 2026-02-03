"""Web search and fetch tools."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

# Pre-compiled Regex Patterns for Performance
SCRIPT_REGEX = re.compile(r"<script[^>]*>[\s\S]*?</script[^>]*>", flags=re.I)
STYLE_REGEX = re.compile(r"<style[^>]*>[\s\S]*?</style>", flags=re.I)
H1_REGEX = re.compile(r"<h1[^>]*>(.*?)</h1>", flags=re.I)
H2_REGEX = re.compile(r"<h2[^>]*>(.*?)</h2>", flags=re.I)
H3_REGEX = re.compile(r"<h3[^>]*>(.*?)</h3>", flags=re.I)
P_REGEX = re.compile(r"<p[^>]*>(.*?)</p>", flags=re.I | re.S)
BR_REGEX = re.compile(r"<br\s*/?>", flags=re.I)
LI_REGEX = re.compile(r"<li[^>]*>(.*?)</li>", flags=re.I)
LINK_REGEX = re.compile(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', flags=re.I)
CODE_REGEX = re.compile(r"<code[^>]*>(.*?)</code>", flags=re.I)
PRE_REGEX = re.compile(r"<pre[^>]*>(.*?)</pre>", flags=re.I | re.S)
STRONG_REGEX = re.compile(r"<strong[^>]*>(.*?)</strong>", flags=re.I)
EM_REGEX = re.compile(r"<em[^>]*>(.*?)</em>", flags=re.I)
TAG_REGEX = re.compile(r"<[^>]+>")
NEWLINE_REGEX = re.compile(r"\n\s*\n\s*\n")


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

        if not await self._is_safe_url(url):
            return {
                "success": False,
                "error": "Security Error: Access to private/local network blocked (SSRF Protection).",
            }

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

    async def _is_safe_url(self, url: str) -> bool:
        """
        Validate URL against SSRF attacks (block private/local IPs).
        """
        try:
            # Handle scheme if missing (though usually handled by caller/user)
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False

            # Resolve hostname to IP using async resolver
            loop = asyncio.get_running_loop()
            try:
                # getaddrinfo returns list of (family, type, proto, canonname, sockaddr)
                # We check all resolved IPs
                infos = await loop.getaddrinfo(hostname, None)
            except socket.gaierror:
                return False

            if not infos:
                return False

            for info in infos:
                # info[4] is sockaddr, info[4][0] is the IP address
                ip_str = info[4][0]
                try:
                    ip = ipaddress.ip_address(ip_str)
                    # Block private, loopback, and link-local ranges
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        return False
                except ValueError:
                    # Skip invalid IPs
                    continue

            return True
        except Exception:
            # Fail safe on any resolution error
            return False

    def _html_to_markdown(self, html: str) -> str:
        html = SCRIPT_REGEX.sub("", html)
        html = STYLE_REGEX.sub("", html)

        html = H1_REGEX.sub(r"# \1\n", html)
        html = H2_REGEX.sub(r"## \1\n", html)
        html = H3_REGEX.sub(r"### \1\n", html)
        html = P_REGEX.sub(r"\1\n\n", html)
        html = BR_REGEX.sub("\n", html)
        html = LI_REGEX.sub(r"- \1\n", html)
        html = LINK_REGEX.sub(
            r"[\2](\1)",
            html,
        )
        html = CODE_REGEX.sub(r"`\1`", html)
        html = PRE_REGEX.sub(r"```\n\1\n```", html)
        html = STRONG_REGEX.sub(r"**\1**", html)
        html = EM_REGEX.sub(r"*\1*", html)

        html = TAG_REGEX.sub("", html)

        html = NEWLINE_REGEX.sub("\n\n", html)
        html = html.strip()

        return html[:50000]

    async def _process_with_prompt(self, content: str, prompt: str) -> str:
        return f"Content summary for: {prompt}\n\n{content[:5000]}"

    def _cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

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
        except (json.JSONDecodeError, KeyError, ValueError):
            # Ignore corrupted cache entries.
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
