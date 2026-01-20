# Bolt's Journal

## 2024-05-22 - [Project Initialization]
**Learning:** This is a fresh Bolt journal for the MyCoder project.
**Action:** Document all future performance findings here.

## 2024-05-22 - [Regex Pre-compilation in TUI Loop]
**Learning:** The `InteractiveCLI` class in `src/mycoder/cli_interactive.py` re-compiles regexes inside the `_render_chat_panel` method, which is called by the `rich.Live` loop 4 times per second. This is a classic unnecessary CPU cycle waste in an event loop.
**Action:** Moving regex compilation to the module level ensures they are compiled only once. This applies to `_strip_markdown` as well.
