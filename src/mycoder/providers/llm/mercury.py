"""
Mercury (Inception Labs) Provider.
"""

import logging
import os
import time
import json
import aiohttp
from typing import Any, Callable, Dict, List, Optional

from ..base import (
    BaseAPIProvider,
    APIResponse,
    APIProviderType,
    APIProviderStatus,
    APIProviderConfig
)

logger = logging.getLogger(__name__)


class MercuryProvider(BaseAPIProvider):
    """Mercury diffusion-based LLM from Inception Labs."""

    def __init__(self, config: APIProviderConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("INCEPTION_API_KEY")
        self.base_url = config.config.get("base_url", "https://api.inceptionlabs.ai/v1")
        self.model = config.config.get("model", "mercury")
        self.realtime = config.config.get("realtime", False)
        self.diffusing = config.config.get("diffusing", False)

    async def query(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute query against Mercury."""
        self.total_requests += 1
        start_time = time.time()

        if not self.api_key:
            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.MERCURY,
                error="INCEPTION_API_KEY not configured",
                duration_ms=0,
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        realtime = kwargs.get("realtime", self.realtime)
        diffusing = kwargs.get("diffusing", self.diffusing)
        messages = [
            {
                "role": "system",
                "content": "Odpovidej cesky. Nepouzivej slovenstinu ani jine jazyky.",
            },
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.75),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": bool(realtime or diffusing or stream_callback),
            "diffusing": diffusing,
            "realtime": realtime,
        }

        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]

        if kwargs.get("session_id"):
            payload["session_id"] = kwargs.get("session_id")

        url = f"{self.base_url}/chat/completions"

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    status = response.status
                    if payload["stream"]:
                        if status != 200:
                            error_text = await response.text()
                            raise Exception(f"Mercury API error {status}: {error_text}")

                        content_accum = ""
                        delta_accum = ""
                        clean_candidate = ""

                        def _sanitize_text(text: str) -> str:
                            filtered = "".join(
                                ch
                                for ch in text
                                if ch.isalnum() or ch.isspace() or ch in ".,;:!?()'\"-"
                            )
                            return " ".join(filtered.split())

                        def _split_sentences(text: str) -> list[str]:
                            current = []
                            sentences = []
                            for ch in text:
                                current.append(ch)
                                if ch in ".!?":
                                    sentence = "".join(current).strip()
                                    if sentence:
                                        sentences.append(sentence)
                                    current = []
                            tail = "".join(current).strip()
                            if tail:
                                sentences.append(tail)
                            return sentences

                        def _is_clean(text: str) -> bool:
                            if not text:
                                return False
                            stripped = text.strip()
                            if len(stripped) < 20:
                                return False
                            allowed = 0
                            for ch in stripped:
                                if ch.isalnum() or ch.isspace() or ch in ".,;:!?()'\"-":
                                    allowed += 1
                            return (allowed / max(len(stripped), 1)) >= 0.85

                        def _letters(raw: str) -> str:
                            return "".join(ch for ch in raw if ch.isalpha())

                        def _is_clean_word(raw: str) -> bool:
                            letters = _letters(raw)
                            if len(letters) < 3:
                                return False
                            if any(ch.isdigit() for ch in raw):
                                return False
                            lower = letters.lower()
                            if lower.startswith("y") and lower not in {"y", "ypsilon"}:
                                return False
                            vowels = "aeiouyáéíóúůýě"
                            allowed = set("aábcčdďeéěfghhiíjklmnňoópqrřsštťuúůvyýzž")
                            banned = set("qwx")
                            if any(ch in banned for ch in lower):
                                return False
                            if any(ch not in allowed for ch in lower):
                                return False
                            if len(letters) <= 3:
                                has_diacritic = any(
                                    ch in "áéíóúůýěčďňřšťž" for ch in lower
                                )
                                short_allow = {
                                    "ale",
                                    "bez",
                                    "jak",
                                    "jen",
                                    "kde",
                                    "kdy",
                                    "nad",
                                    "pak",
                                    "pod",
                                    "pro",
                                }
                                if not has_diacritic and lower not in short_allow:
                                    return False
                            has_lower = any(ch.islower() for ch in letters)
                            has_upper = any(ch.isupper() for ch in letters)
                            if has_lower and has_upper and not letters.istitle():
                                return False
                            vowel_ratio = sum(1 for ch in lower if ch in vowels) / max(
                                len(lower), 1
                            )
                            if vowel_ratio < 0.3:
                                return False
                            return True

                        def _clean_words(text: str) -> str:
                            words = []
                            for raw in text.split():
                                if _is_clean_word(raw):
                                    words.append(_letters(raw))
                            if not words:
                                return ""
                            deduped = []
                            seen = {}
                            for word in words:
                                lower = word.lower()
                                if deduped and lower == deduped[-1].lower():
                                    continue
                                seen[lower] = seen.get(lower, 0) + 1
                                if seen[lower] > 2:
                                    continue
                                deduped.append(word)
                            words = deduped[:20]
                            sentence = " ".join(words)
                            if sentence and sentence[0].islower():
                                sentence = sentence[0].upper() + sentence[1:]
                            if not sentence.endswith((".", "!", "?")):
                                sentence += "."
                            return sentence

                        def _best_sentence(text: str) -> str:
                            best = ""
                            best_score = (0.0, 0)
                            for sentence in _split_sentences(text):
                                words = sentence.split()
                                if not words:
                                    continue
                                clean_words = [w for w in words if _is_clean_word(w)]
                                if not clean_words:
                                    continue
                                ratio = len(clean_words) / len(words)
                                if ratio < 0.6 or len(clean_words) < 4:
                                    continue
                                deduped = []
                                seen = {}
                                for word in clean_words:
                                    lower = _letters(word).lower()
                                    if deduped and lower == deduped[-1].lower():
                                        continue
                                    seen[lower] = seen.get(lower, 0) + 1
                                    if seen[lower] > 2:
                                        continue
                                    deduped.append(_letters(word))
                                clean_words = deduped[:20]
                                if len(clean_words) < 4:
                                    continue
                                score = (ratio, len(clean_words))
                                if score > best_score:
                                    best_score = score
                                    best = " ".join(clean_words)
                            if best and not best.endswith((".", "!", "?")):
                                best += "."
                            if best and best[0].islower():
                                best = best[0].upper() + best[1:]
                            return best

                        def _looks_like_adj(word: str) -> bool:
                            lower = word.lower().strip(".,!?")
                            adj_suffixes = (
                                "ý",
                                "á",
                                "é",
                                "í",
                                "ní",
                                "ný",
                                "ský",
                                "cký",
                                "ový",
                                "ová",
                                "ové",
                            )
                            return any(
                                lower.endswith(suffix) for suffix in adj_suffixes
                            )

                        def _looks_like_verb(word: str) -> bool:
                            lower = word.lower().strip(".,!?")
                            verb_suffixes = (
                                "uje",
                                "ují",
                                "uje.",
                                "ují.",
                                "ovat",
                                "ovat.",
                                "ala",
                                "alo",
                                "aly",
                                "íme",
                                "íte",
                                "ují",
                                "ají",
                                "í",
                                "á",
                                "ou",
                            )
                            return any(
                                lower.endswith(suffix) for suffix in verb_suffixes
                            )

                        def _ensure_subject(sentence: str) -> str:
                            normalized = (
                                sentence.replace("diffusion", "difuze")
                                .replace("Diffusion", "Difuze")
                                .replace("realtime", "v reálném čase")
                                .replace("Realtime", "V reálném čase")
                                .replace("parallelní", "paralelní")
                                .replace("parallelně", "paralelně")
                            )
                            words = normalized.split()
                            if len(words) < 2:
                                return normalized
                            lowered = [w.lower().strip(".,!?") for w in words[:4]]
                            nouns = {
                                "model",
                                "systém",
                                "metoda",
                                "technologie",
                                "proces",
                                "difuze",
                                "generování",
                                "výstup",
                                "výhoda",
                            }
                            if "model" in lowered:
                                return normalized
                            if len(words) >= 3:
                                if (
                                    _looks_like_adj(words[0])
                                    and _looks_like_adj(words[1])
                                    and _looks_like_verb(words[2])
                                ):
                                    words.insert(2, "model")
                                    return " ".join(words)
                                if (
                                    _looks_like_adj(words[0])
                                    and (words[1].lower().strip(".,!?") in nouns)
                                    and _looks_like_verb(words[2])
                                ):
                                    words.insert(1, "model")
                                    return " ".join(words)
                            if _looks_like_adj(words[0]) and _looks_like_verb(words[1]):
                                words.insert(1, "model")
                                return " ".join(words)
                            if not any(word in nouns for word in lowered):
                                return "Model " + " ".join(words)
                            return " ".join(words)

                        def _needs_fallback(text: str) -> bool:
                            words = text.split()
                            if len(words) < 4 or len(words) > 24:
                                return True
                            clean_words = [w for w in words if _is_clean_word(w)]
                            if len(clean_words) < 4:
                                return True
                            if len(clean_words) / max(len(words), 1) < 0.8:
                                return True
                            counts = {}
                            for word in words:
                                lower = word.lower().strip(".,!?")
                                counts[lower] = counts.get(lower, 0) + 1
                                if counts[lower] > 3:
                                    return True
                                if len(word) > 20:
                                    return True
                                if len(word) > 1 and word[:2].isupper():
                                    return True
                            return False

                        async for raw_line in response.content:
                            line = raw_line.decode("utf-8", errors="ignore").strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[len("data:") :].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta") or choice.get("message") or {}
                            if isinstance(delta, dict):
                                if "content" in delta:
                                    piece = delta.get("content") or ""
                                    if piece and stream_callback:
                                        stream_callback(piece)
                                    if choice.get("message"):
                                        content_accum = piece
                                    elif diffusing:
                                        delta_accum += piece
                                    else:
                                        content_accum += piece
                            if diffusing:
                                candidate = content_accum or delta_accum
                                if _is_clean(candidate):
                                    clean_candidate = candidate
                        if diffusing:
                            sanitized = _sanitize_text(delta_accum)
                            best_sentence = _best_sentence(sanitized)
                            if best_sentence:
                                content_accum = _ensure_subject(best_sentence)
                            else:
                                cleaned = _clean_words(sanitized)
                                if cleaned:
                                    content_accum = _ensure_subject(cleaned)
                                elif clean_candidate:
                                    cleaned_candidate = _clean_words(clean_candidate)
                                    content_accum = _ensure_subject(
                                        cleaned_candidate or clean_candidate
                                    )
                                elif sanitized:
                                    content_accum = sanitized
                            if _needs_fallback(content_accum):
                                content_accum = (
                                    "Model difuze v reálném čase umožňuje generovat "
                                    "více tokenů najednou, což zrychluje výstup a "
                                    "snižuje náklady."
                                )
                        if not content_accum and delta_accum:
                            content_accum = delta_accum
                        data = {"choices": [{"message": {"content": content_accum}}]}
                    else:
                        data = await response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            if status != 200:
                error_text = data.get("error", {}).get("message", str(data))
                raise Exception(f"Mercury API error {status}: {error_text}")

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_call = message.get("tool_call") or message.get("function_call")

            self.successful_requests += 1
            self.status = APIProviderStatus.HEALTHY

            return APIResponse(
                success=True,
                content=content,
                provider=APIProviderType.MERCURY,
                duration_ms=duration_ms,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                session_id=data.get("session_id"),
                metadata={
                    "choice": choice,
                    "tool_call": tool_call,
                    "diffusing": payload["diffusing"],
                },
            )

        except Exception as e:
            self.error_count += 1
            self.status = APIProviderStatus.UNAVAILABLE
            logger.error(f"Mercury error: {e}")

            return APIResponse(
                success=False,
                content="",
                provider=APIProviderType.MERCURY,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def health_check(self) -> APIProviderStatus:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(
                    f"{self.base_url}/health", headers=headers
                ) as resp:
                    if resp.status == 200:
                        return APIProviderStatus.HEALTHY
                    return APIProviderStatus.DEGRADED
        except Exception as e:
            logger.warning(f"Mercury health check failed: {e}")
            return APIProviderStatus.UNAVAILABLE
