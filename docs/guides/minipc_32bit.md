# MiniPC 32-bit Profile (Intel Atom)

This profile targets older 32-bit systems (e.g., Intel Atom N280, 2GB RAM) while keeping **all basic features** intact and minimizing losses in extended functionality.

## Goals

- Preserve core chat and provider fallback behavior.
- Avoid local inference and heavy optional dependencies.
- Reduce memory/CPU overhead with conservative defaults.

## Recommended Installation

```bash
# From repo root
poetry install --extras http

# Do NOT install speech extras on 32-bit systems
# poetry install --extras speech  (skip)
```

## Configuration

Use the pre-tuned config and copy it to the default location:

```bash
cp mycoder_config_minipc_32bit.json mycoder_config.json
```

Key settings in the profile:
- `claude_oauth` enabled, `gemini` enabled as fallback.
- `ollama_local` disabled (32-bit CPU is too slow).
- `ollama_remote_urls` empty (fill only if you have a remote Ollama host).
- `thermal` disabled (Q9550-only sensors).
- `max_concurrent_requests` set to 2.

## Optional Remote Ollama

If you run Ollama on another machine, set:

```json
{
  "ollama_remote_urls": ["http://remote-ollama:11434"]
}
```

## Runtime Tips

```bash
export MYCODER_THERMAL_ENABLED=false
export MYCODER_PREFERRED_PROVIDER=claude_oauth
```

## Basic Features Preserved

- Interactive CLI
- Multi-provider fallback
- Session management
- Tool registry (local tools)

## Extended Features (Minimized)

- Local Ollama inference disabled by default
- MCP integration off by default
- Speech recognition not installed

## Testing (32-bit Safe)

```bash
poetry run pytest tests/unit -v -m "not thermal"
```
