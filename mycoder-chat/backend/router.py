"""
Mini-Orchestrator - Routing logic pro různé typy requestů
"""
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MiniOrchestrator:
    """Routing logika pro různé typy requests"""

    # Patterns pro detekci typu úkolu
    PATTERNS = {
        'code': [
            r'\b(refactor|code|function|class|debug|fix|implement|create)\b',
            r'\b(write|generate|build).*(code|function|script|program)\b',
            r'\.(py|js|go|rs|java|cpp|ts|jsx|tsx|vue|rb|php)\b',  # zmínka souborů
            r'\b(git|commit|pull request|merge|branch)\b'
        ],
        'research': [
            r'\b(find|search|what is|explain|research|zjisti|najdi)\b',
            r'\b(latest|news|update|novinky).*(on|about|o|v)\b',
            r'\b(how to|jak|proč|why)\b'
        ],
        'transcribe': [
            r'\b(transcribe|transcript|přepis|audio|speech|nahrávka)\b',
            r'\.(mp3|wav|m4a|ogg|flac|aac)\b'
        ],
        'translate': [
            r'\b(translate|přelož|translation|překlad)\b',
            r'\b(from|to|z|do).*(english|czech|german|french|čeština|angličtina)\b'
        ],
        'memory': [
            r'\b(remember|pamatuj|co jsme|what did we|vzpomeň)\b',
            r'\b(minulý|yesterday|last week|včera|předtím|předešlý)\b',
            r'\b(context|conversation|diskuze|konverzace).*(včera|předtím|minule)\b'
        ],
        'home': [
            r'\b(light|světlo|lamp|lampa|teplota|temperature|humidity|vlhkost)\b',
            r'\b(turn on|turn off|zapni|vypni|ztlum|zesil)\b',
            r'\b(home assistant|homeassistant|ha)\b'
        ],
        'image': [
            r'\b(image|obrázek|foto|picture|visualization|vizualizace|diagram)\b',
            r'\b(generate|vytvoř|vygeneruj).*(image|obrázek|diagram)\b',
            r'\.(jpg|jpeg|png|gif|svg|webp)\b'
        ]
    }

    def __init__(self):
        self.total_requests = 0
        self.routing_stats = {}

    def route_request(self, user_message: str) -> Dict[str, Any]:
        """
        Rozhodne kam a jak poslat request

        Returns:
            {
                'target': 'has' | 'llm_server',
                'service': 'filesystem-mcp' | 'transcriber-mcp' | ...,
                'mode': 'chat' | 'analyze' | 'debug' | ...,
                'model': 'claude' | 'gpt4' | 'local' | 'auto'
            }
        """
        self.total_requests += 1
        msg_lower = user_message.lower()

        # 1. HEAVY TASKS → LLM Server
        if self._match_patterns(msg_lower, self.PATTERNS['transcribe']):
            logger.info("Detected: TRANSCRIPTION task")
            return self._track_routing({
                'target': 'llm_server',
                'service': 'transcriber-mcp',
                'mode': 'transcribe',
                'model': 'whisper-large'
            })

        if self._match_patterns(msg_lower, self.PATTERNS['translate']):
            logger.info("Detected: TRANSLATION task")
            return self._track_routing({
                'target': 'llm_server',
                'service': 'translation',
                'mode': 'translate',
                'model': 'local'  # nebo 'gpt4' pro lepší kvalitu
            })

        # 2. CODE TASKS → HAS s Claude/GPT-4
        if self._match_patterns(msg_lower, self.PATTERNS['code']):
            logger.info("Detected: CODE task")

            # Rozpoznat intent: debug vs refactor vs review vs generate
            if any(word in msg_lower for word in ['debug', 'fix', 'error', 'bug', 'problém']):
                mode = 'debug'
            elif any(word in msg_lower for word in ['refactor', 'improve', 'vylepši', 'optimalizuj']):
                mode = 'refactor'
            elif any(word in msg_lower for word in ['review', 'check', 'zkontroluj', 'posouď']):
                mode = 'review'
            elif any(word in msg_lower for word in ['test', 'testuj', 'unittest']):
                mode = 'test'
            else:
                mode = 'chat'  # default pro code

            return self._track_routing({
                'target': 'has',
                'service': 'filesystem-mcp',
                'mode': mode,
                'model': 'claude'  # Claude je best pro code
            })

        # 3. RESEARCH → HAS research-mcp
        if self._match_patterns(msg_lower, self.PATTERNS['research']):
            logger.info("Detected: RESEARCH task")
            return self._track_routing({
                'target': 'has',
                'service': 'research-mcp',
                'mode': 'chat',
                'model': 'gpt4'  # GPT-4 dobrý pro research
            })

        # 4. MEMORY SEARCH → HAS cldmemory-mcp
        if self._match_patterns(msg_lower, self.PATTERNS['memory']):
            logger.info("Detected: MEMORY SEARCH task")
            return self._track_routing({
                'target': 'has',
                'service': 'cldmemory-mcp',
                'mode': 'search',
                'model': None  # memory search nepotřebuje LLM přímo
            })

        # 5. HOME AUTOMATION → Home Assistant
        if self._match_patterns(msg_lower, self.PATTERNS['home']):
            logger.info("Detected: HOME AUTOMATION task")
            return self._track_routing({
                'target': 'has',
                'service': 'home-assistant',
                'mode': 'command',
                'model': None
            })

        # 6. IMAGE GENERATION → LLM Server
        if self._match_patterns(msg_lower, self.PATTERNS['image']):
            logger.info("Detected: IMAGE GENERATION task")
            return self._track_routing({
                'target': 'llm_server',
                'service': 'image-generation',
                'mode': 'generate',
                'model': 'stable-diffusion'
            })

        # DEFAULT: Obecný chat → HAS Zen Coordinator s auto model selection
        logger.info("Detected: GENERAL CHAT (default)")
        return self._track_routing({
            'target': 'has',
            'service': 'zen-coordinator',
            'mode': 'chat',
            'model': 'auto'  # Zen vybere sám nejlepší model
        })

    def _match_patterns(self, text: str, patterns: list) -> bool:
        """Zkontroluje jestli text matchuje nějaký pattern"""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _track_routing(self, routing: dict) -> dict:
        """Track routing statistics"""
        service = routing['service']
        self.routing_stats[service] = self.routing_stats.get(service, 0) + 1
        return routing

    def _debug_get_matched_patterns(self, text: str) -> dict:
        """Debug metoda - vrátí které patterns matchly"""
        msg_lower = text.lower()
        matched = {}

        for category, patterns in self.PATTERNS.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    matches.append(pattern)

            if matches:
                matched[category] = matches

        return matched
