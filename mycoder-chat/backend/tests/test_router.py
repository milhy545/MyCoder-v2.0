"""
Unit testy pro Mini-Orchestrator
"""
import pytest
from router import MiniOrchestrator


@pytest.fixture
def orchestrator():
    return MiniOrchestrator()


class TestCodeTaskRouting:
    """Testy pro code-related úkoly"""

    def test_refactor_task(self, orchestrator):
        result = orchestrator.route_request("Refactor authentication module")
        assert result['target'] == 'has'
        assert result['service'] == 'filesystem-mcp'
        assert result['mode'] == 'refactor'
        assert result['model'] == 'claude'

    def test_debug_task(self, orchestrator):
        result = orchestrator.route_request("Debug error in auth.py")
        assert result['target'] == 'has'
        assert result['mode'] == 'debug'
        assert result['model'] == 'claude'

    def test_review_task(self, orchestrator):
        result = orchestrator.route_request("Review this code for security issues")
        assert result['mode'] == 'review'

    def test_file_extension_detection(self, orchestrator):
        result = orchestrator.route_request("Check main.py for errors")
        assert result['service'] == 'filesystem-mcp'


class TestResearchTaskRouting:
    """Testy pro research úkoly"""

    def test_research_what_is(self, orchestrator):
        result = orchestrator.route_request("What is GraphRAG?")
        assert result['target'] == 'has'
        assert result['service'] == 'research-mcp'
        assert result['model'] == 'gpt4'

    def test_research_latest(self, orchestrator):
        result = orchestrator.route_request("Latest news in AI")
        assert result['service'] == 'research-mcp'

    def test_czech_research(self, orchestrator):
        result = orchestrator.route_request("Najdi informace o LangChain")
        assert result['service'] == 'research-mcp'


class TestHeavyTaskRouting:
    """Testy pro heavy tasks (LLM Server)"""

    def test_transcription_task(self, orchestrator):
        result = orchestrator.route_request("Transcribe audio.mp3")
        assert result['target'] == 'llm_server'
        assert result['service'] == 'transcriber-mcp'
        assert result['mode'] == 'transcribe'

    def test_translation_task(self, orchestrator):
        result = orchestrator.route_request("Translate to English")
        assert result['target'] == 'llm_server'
        assert result['service'] == 'translation'

    def test_czech_translation(self, orchestrator):
        result = orchestrator.route_request("Přelož tento text do angličtiny")
        assert result['service'] == 'translation'


class TestMemoryRouting:
    """Testy pro memory search"""

    def test_memory_search_past(self, orchestrator):
        result = orchestrator.route_request("Co jsme řešili včera?")
        assert result['target'] == 'has'
        assert result['service'] == 'cldmemory-mcp'
        assert result['mode'] == 'search'

    def test_memory_search_english(self, orchestrator):
        result = orchestrator.route_request("What did we discuss last week?")
        assert result['service'] == 'cldmemory-mcp'


class TestHomeAutomation:
    """Testy pro home automation"""

    def test_home_assistant_light(self, orchestrator):
        result = orchestrator.route_request("Zapni světlo v obýváku")
        assert result['target'] == 'has'
        assert result['service'] == 'home-assistant'

    def test_home_assistant_english(self, orchestrator):
        result = orchestrator.route_request("Turn on the lights")
        assert result['service'] == 'home-assistant'


class TestDefaultRouting:
    """Test pro default/fallback routing"""

    def test_general_chat(self, orchestrator):
        result = orchestrator.route_request("Hello, how are you?")
        assert result['target'] == 'has'
        assert result['service'] == 'zen-coordinator'
        assert result['mode'] == 'chat'
        assert result['model'] == 'auto'

    def test_unclear_intent(self, orchestrator):
        result = orchestrator.route_request("Hmm, nevím co dělat")
        assert result['service'] == 'zen-coordinator'
