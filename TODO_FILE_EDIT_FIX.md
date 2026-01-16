# TODO: Oprava File Edit - MyCoder vs Claude Code

## Problém

MyCoder "drhne" při zápisu souborů, protože:

1. ❌ **NEPOUŽÍVÁ Function Calling API** - Neposílá tool schemas Anthropic/Gemini API
2. ❌ **Primitivní textový parsing** - `_enhance_with_tools` hledá jen "read file", "run command"
3. ❌ **EditTool není integrován** - Existuje v `tools/edit_tool.py`, ale není v `_enhance_with_tools`
4. ❌ **Chybí system prompt** - Model neví, že má používat `/edit` příkazy
5. ❌ **Model generuje celý soubor** místo Search & Replace

**Výsledek:** Model dostane "uprav soubor X" → Snaží se vygenerovat celý nový obsah → Dojdou tokeny/udělá chybu → SELHÁNÍ

**Claude Code funguje jinak:**
- ✅ Posílá tool schemas přímo v API
- ✅ Model odpovídá `tool_use` bloky
- ✅ Vykonává přímo bez parsingu textu
- ✅ Search & Replace pattern (old_string → new_string)

---

## Řešení: 3 možnosti (seřazené podle priority)

### ⭐ Možnost 1: Přidat Function Calling API Support (DOPORUČENO)

**Výhody:**
- Nejspolehlivější řešení
- Modely mají nativní support
- Strukturované tool calls (JSON)
- Stejný přístup jako Claude Code

**Implementace:**

#### Krok 1.1: Přidat tool schema generator do `tool_registry.py`

```python
# V tool_registry.py, přidat metodu do BaseTool:

class BaseTool(ABC):
    # ... existující kód ...

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """Generuje Anthropic Function Calling schema"""
        return {
            "name": self.name,
            "description": self.get_description(),
            "input_schema": self.get_input_schema(),
        }

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Generuje Gemini Function Declaration schema"""
        return {
            "name": self.name,
            "description": self.get_description(),
            "parameters": self.get_input_schema(),
        }

    @abstractmethod
    def get_description(self) -> str:
        """Popis nástroje pro LLM"""
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """JSON Schema pro vstupní parametry"""
        pass
```

#### Krok 1.2: Implementovat schema pro FileEditTool

```python
# V tool_registry.py, FileEditTool:

class FileEditTool(BaseTool):
    # ... existující kód ...

    def get_description(self) -> str:
        return (
            "Edit files using Search & Replace pattern. "
            "Find unique 'old_string' in file and replace with 'new_string'. "
            "ALWAYS read file first using file_read tool!"
        )

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to file"
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to find (must be unique in file)"
                },
                "new_string": {
                    "type": "string",
                    "description": "New text to replace with"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                    "default": False
                }
            },
            "required": ["path", "old_string", "new_string"]
        }
```

#### Krok 1.3: Přidat tool schemas do API volání v `api_providers.py`

```python
# V ClaudeAnthropicProvider.query():

async def query(self, prompt: str, context: Dict[str, Any], **kwargs) -> APIResponse:
    # ... existující kód ...

    # NOVÝ KÓD: Získat tool schemas z registry
    tool_registry = context.get("tool_registry")
    tools = []
    if tool_registry:
        for tool_name in ["file_read", "file_edit", "file_write", "terminal_exec"]:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                tools.append(tool.to_anthropic_schema())

    # Volání Anthropic API S TOOLS
    response = await anthropic_client.messages.create(
        model=self.model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,  # ← PŘIDAT TOHLE
        **api_kwargs
    )

    # ZPRACOVÁNÍ tool_use bloků
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            # Vykonat tool
            result = await tool_registry.execute_tool(
                block.name,
                context,
                **block.input
            )
            tool_results.append({
                "tool_use_id": block.id,
                "result": result.data
            })

    # Pokud byly tool calls, pokračovat v konverzaci
    if tool_results:
        # ... další kolo s tool_results ...
```

#### Krok 1.4: Stejná logika pro GeminiProvider

```python
# V GeminiProvider.query() - podobná implementace jako Anthropic
```

---

### ⚡ Možnost 2: Vylepšený System Prompt (RYCHLÉ ŘEŠENÍ)

**Výhody:**
- Rychlá implementace (1-2 hodiny)
- Funguje i bez Function Calling API
- Dobrý fallback

**Implementace:**

#### Krok 2.1: Přidat system prompt do `enhanced_mycoder_v2.py`

```python
# V enhanced_mycoder_v2.py:

SYSTEM_PROMPT = """You are MyCoder, an AI development assistant.

CRITICAL: When editing files, you MUST use the /edit command with Search & Replace pattern.

## File Operations

### Reading Files
/read <path>

### Editing Files (Search & Replace)
/edit <path> "old_string" "new_string"
- old_string: EXACT text to find (must be unique in file)
- new_string: New text to replace with
- ALWAYS read file first with /read
- NEVER write entire file content
- Use /edit --all to replace all occurrences

### Writing New Files
/write <path>
[content on next lines]

## Examples

❌ WRONG (generates entire file):
User: "Add a print statement to hello.py"
Assistant: "Here's the updated file:
def hello():
    print('Starting')
    return 'Hi'
..."

✅ CORRECT (Search & Replace):
User: "Add a print statement to hello.py"
Assistant: "I'll add a print statement:
/read hello.py
/edit hello.py "def hello():" "def hello():\\n    print('Starting')"

## Rules
1. ALWAYS use /edit for modifications, NEVER write full files
2. Make old_string unique (include surrounding context)
3. Read file first to verify old_string exists
4. If old_string not unique, add more context
"""

# V process_request():
async def process_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
    # ... existující kód ...

    # Přidat system prompt do contextu
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"

    api_response = await self.provider_router.query(
        prompt=full_prompt,  # ← ZMĚNIT TOHLE
        context=context,
        **kwargs
    )
```

#### Krok 2.2: Vylepšit `_enhance_with_tools` pro parsování /edit příkazů

```python
# V enhanced_mycoder_v2.py:

async def _enhance_with_tools(
    self, api_response: APIResponse, context: Dict[str, Any]
) -> Optional[APIResponse]:
    """Parse and execute tool commands from response"""

    content = api_response.content
    lines = content.split('\n')

    tool_results = []
    tool_context = ToolExecutionContext(
        mode=context.get("mode", "FULL"),
        working_directory=context.get("working_directory"),
    )

    # Parse všechny tool příkazy
    for line in lines:
        line = line.strip()

        # /edit parsing
        if line.startswith('/edit '):
            try:
                import shlex
                parts = shlex.split(line[6:])  # Bez "/edit "
                if len(parts) >= 3:
                    path, old_str, new_str = parts[0], parts[1], parts[2]
                    replace_all = '--all' in parts

                    result = await self.tool_registry.execute_tool(
                        "file_edit",
                        tool_context,
                        path=path,
                        old_string=old_str,
                        new_string=new_str,
                        replace_all=replace_all
                    )
                    tool_results.append(f"✓ Edited {path}: {result.data}")
            except Exception as e:
                tool_results.append(f"✗ Edit failed: {e}")

        # /read parsing
        elif line.startswith('/read '):
            path = line[6:].strip()
            result = await self.tool_registry.execute_tool(
                "file_read", tool_context, path=path
            )
            if result.success:
                tool_results.append(f"File: {path}\n{result.data}")

        # /write parsing
        # ... podobně ...

    if tool_results:
        enhanced_content = content + "\n\n## Tool Execution Results:\n" + "\n".join(tool_results)
        return APIResponse(
            success=True,
            content=enhanced_content,
            provider=api_response.provider,
            # ... metadata ...
        )

    return None
```

---

### 🔧 Možnost 3: Hybrid (System Prompt + Parsování /edit z CLI)

**Implementace:**

- Použij Možnost 2 (system prompt)
- V `cli_interactive.py` parsuj `/edit` příkazy přímo
- Pokud uživatel napíše `/edit`, vykonej EditTool přímo

---

## Priority Implementace

### Phase 1: Rychlá oprava (1-2 dny)
- [ ] Implementovat Možnost 2 (System Prompt + Enhanced Parsing)
- [ ] Otestovat s Claude/Gemini/Ollama
- [ ] Přidat unit testy pro parsing `/edit` příkazů

### Phase 2: Dlouhodobé řešení (1 týden)
- [ ] Implementovat Možnost 1 (Function Calling API)
- [ ] Přidat `to_anthropic_schema()` a `to_gemini_schema()` do všech tools
- [ ] Implementovat tool_use loop v providers
- [ ] Přidat integration testy pro tool calls

### Phase 3: Dokumentace a příklady
- [ ] Aktualizovat CLAUDE.md s příklady použití /edit
- [ ] Přidat příklady do README.md
- [ ] Vytvořit test suite pro file editing

---

## Testování

### Test Case 1: Jednoduchá úprava
```python
# Před úpravou (hello.py):
def hello():
    pass

# Prompt:
"Add a return statement to hello() that returns 'Hi'"

# Očekávaný příkaz:
/edit hello.py "    pass" "    return 'Hi'"

# Po úpravě:
def hello():
    return 'Hi'
```

### Test Case 2: Úprava s kontextem
```python
# Prompt:
"Change the greeting in main() to 'Hello World'"

# Očekávaný příkaz (s kontextem):
/edit main.py "print('Hello')" "print('Hello World')"
```

### Test Case 3: Chybné použití
```python
# Prompt:
"Fix all typos in config.py"

# ❌ Model nesmí:
- Vygenerovat celý nový config.py
- Použít file_write místo file_edit

# ✅ Model musí:
- Přečíst config.py pomocí /read
- Použít /edit pro každou opravu samostatně
```

---

## Příklady pro AGENTS.md

Až budeš implementovat, přidej do AGENTS.md:

```markdown
## Recent Changes
- 2026-01-16: Codex - Implementoval Function Calling API support pro file_edit tool
- 2026-01-16: Codex - Přidal system prompt s Search & Replace instrukcemi
- 2026-01-16: Codex - Vylepšil _enhance_with_tools pro parsování /edit příkazů
```

---

## Reference

- Claude Code Edit tool: https://docs.anthropic.com/claude/docs/tool-use
- Anthropic Function Calling: https://docs.anthropic.com/claude/docs/tool-use
- Gemini Function Declarations: https://ai.google.dev/gemini-api/docs/function-calling

---

**Priorita:** 🔥 VYSOKÁ - Toto je klíčový rozdíl mezi MyCoder a Claude Code

**Odhadovaný čas:**
- Možnost 2 (Quick Fix): 2-4 hodiny
- Možnost 1 (Function Calling): 1-2 dny
- Celá implementace včetně testů: 1 týden
