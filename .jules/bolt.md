# Bolt's Journal

## 2024-05-22 - [Project Initialization]
**Learning:** This is a fresh Bolt journal for the MyCoder project.
**Action:** Document all future performance findings here.

## 2024-05-22 - [Regex Pre-compilation in TUI Loop]
**Learning:** The `InteractiveCLI` class in `src/mycoder/cli_interactive.py` re-compiles regexes inside the `_render_chat_panel` method, which is called by the `rich.Live` loop 4 times per second. This is a classic unnecessary CPU cycle waste in an event loop.
**Action:** Moving regex compilation to the module level ensures they are compiled only once. This applies to `_strip_markdown` as well.

## 2024-05-22 - [Regex Pre-compilation in CommandParser]
**Learning:** `CommandParser` was compiling regex patterns inside the `parse()` loop for every command check. While Python's `re` module has a cache, explicit pre-compilation in `__init__` is more robust and measurably faster (~50% reduction in parsing time per call).
**Action:** Pre-compile all constant regex patterns in the class `__init__` method.

## 2024-05-22 - [Regex Pre-compilation in WebFetcher]
**Learning:** `_html_to_markdown` in `WebFetcher` was relying on `re.sub()`'s internal cache for 14 different patterns called sequentially. Explicit pre-compilation avoids cache lookups and flag processing overhead.
**Action:** Extracted regex patterns to module-level constants. Measured ~3.5% performance improvement in synthetic benchmark.

## 2024-05-23 - [Module-Level Regex Compilation for CommandParser]
**Learning:** Instantiating `CommandParser` rebuilt the regex dictionary every time, which is inefficient when used in utility functions like `execute_command_quick` or `parse_command`.
**Action:** Moved regex compilation to module-level `COMPILED_PATTERNS` so they are compiled only once at import time, making `CommandParser` instantiation practically free.

## 2024-10-24 - [Regex in IO Utilities]
**Learning:** Even in IO-bound tools like `WebFetcher`, compiling 15+ regex patterns inside a method (`_html_to_markdown`) creates unnecessary overhead. While the network latency dominates, the CPU cost of recompiling patterns for every parsed page is non-zero and sloppy.
**Action:** Extract all static regex patterns to module-level constants, especially for utility functions likely to be called in loops (e.g., scraping multiple pages).

## 2025-02-15 - [Regex Pre-compilation in WebFetcher]
**Learning:** `WebFetcher._html_to_markdown` was recompiling multiple regexes on every call, which is inefficient for a frequently used utility.
**Action:** Moved regex patterns to module-level constants (`_REGEX_SCRIPT`, `_REGEX_STYLE`, etc.) to improve performance and code readability. Benchmarking showed a small but measurable improvement (~2% for 100 iterations of a large payload).

## 2025-05-22 - [HTML to Markdown Regex Hoisting]
**Learning:** `WebFetcher._html_to_markdown` in `src/mycoder/web_tools.py` was re-compiling ~14 complex regex patterns every time a page was fetched and converted. While Python caches compiled regexes, the function overhead of checking the cache and re-parsing flags for 14 patterns per call adds up in high-throughput scraping scenarios.
**Action:** Hoisted all regex patterns to module-level `RE_*` constants. This also improved code readability by removing repetitive `flags=re.I` arguments.

## 2026-01-23 - [Regex Pre-compilation in WebFetcher]
**Learning:** `WebFetcher._html_to_markdown` was re-compiling 15+ regex patterns every time it processed HTML content. Even with Python's regex cache, this adds overhead, especially for batch processing.
**Action:** Moved regex patterns to module-level constants and pre-compiled them. Benchmarks show ~4-6% performance improvement on processing large HTML blocks.

## 2026-01-23 - [Caching Rich Renderables in TUI]
**Learning:** The `InteractiveCLI` main loop (via `rich.Live`) re-renders the entire chat history 4 times per second. Parsing Markdown (and especially splitting by regex for thinking blocks) for every message every frame is extremely expensive (O(N) CPU usage).
**Action:** Extract rendering logic for static content (like AI history) into module-level functions decorated with `@functools.lru_cache`. This reduces CPU usage by ~99% for historical messages.

## 2026-06-15 - [Caching System Metrics in TUI]
**Learning:** Retrieving system metrics via `psutil` (especially `sensors_temperatures()`) inside the TUI render loop (4Hz) introduces significant overhead (up to 12ms per frame) and potential jitter due to file I/O on `/proc` and `/sys`.
**Action:** Implemented a 2-second cache for system metrics in `ActivityPanel` and `ExecutionMonitor`. Benchmarks show `get_system_metrics` time reduced from ~0.6ms to ~0.03ms (19x speedup) and eliminates I/O blocks in the UI thread.

## 2026-10-27 - [Blocking DNS in Async WebFetcher]
**Learning:** `WebFetcher._is_safe_url` was using synchronous `socket.gethostbyname` to validate IPs for SSRF protection. This function blocks the entire `asyncio` event loop during DNS resolution (which can take seconds), freezing the TUI or API handling.
**Action:** Replaced with `await loop.getaddrinfo` in an `async` method to ensure non-blocking resolution. Always check for synchronous I/O calls (socket, file) inside `async` methods.
