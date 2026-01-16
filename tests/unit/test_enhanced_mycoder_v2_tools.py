import pytest

from mycoder.api_providers import APIProviderType, APIResponse


@pytest.mark.asyncio
async def test_enhance_with_tools_parses_edit(enhanced_mycoder, temp_dir):
    target = temp_dir / "sample.txt"
    target.write_text("Hello", encoding="utf-8")

    response = APIResponse(
        success=True,
        content='/read sample.txt\n/edit sample.txt "Hello" "Hi"',
        provider=APIProviderType.OLLAMA_LOCAL,
        cost=0.0,
        duration_ms=1,
    )
    context = {"working_directory": temp_dir, "mode": "FULL"}

    enhanced = await enhanced_mycoder._enhance_with_tools(response, context)

    assert enhanced is not None
    assert target.read_text(encoding="utf-8") == "Hi"
    assert "Tool Execution Results" in enhanced.content


@pytest.mark.asyncio
async def test_enhance_with_tools_parses_write_block(enhanced_mycoder, temp_dir):
    response = APIResponse(
        success=True,
        content=(
            "/write new.txt\n"
            "line1\n"
            "line2\n"
            '/edit new.txt "line1" "line1a"'
        ),
        provider=APIProviderType.OLLAMA_LOCAL,
        cost=0.0,
        duration_ms=1,
    )
    context = {"working_directory": temp_dir, "mode": "FULL"}

    enhanced = await enhanced_mycoder._enhance_with_tools(response, context)

    assert enhanced is not None
    assert (temp_dir / "new.txt").read_text(encoding="utf-8") == "line1a\nline2"
