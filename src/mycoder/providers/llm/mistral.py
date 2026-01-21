"""
Mistral AI Provider.
"""

import logging
import os

from ..base import APIProviderConfig
from .openai_compat import OpenAIProvider

logger = logging.getLogger(__name__)


class MistralProvider(OpenAIProvider):
    """Mistral AI Provider."""

    def __init__(self, config: APIProviderConfig):
        # Override defaults for Mistral
        if "base_url" not in config.config:
            config.config["base_url"] = "https://api.mistral.ai/v1"
        if "model" not in config.config:
            config.config["model"] = "mistral-large-latest"

        super().__init__(config)
        self.api_key = config.config.get("api_key") or os.getenv("MISTRAL_API_KEY")
