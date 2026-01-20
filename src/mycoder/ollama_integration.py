"""
Ollama Integration for MyCoder
Local LLM support with CodeLlama and other models
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama API integration.
    Provides local LLM capabilities for MyCoder when cloud services unavailable.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(
                f"{self.base_url}/api/tags", timeout=5
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """Generate response using Ollama model."""

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Prepare request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }

            if system:
                payload["system"] = system

            # Make request
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,  # Longer timeout for generation
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    return {
                        "content": result.get("response", ""),
                        "model": model,
                        "done": result.get("done", False),
                        "eval_count": result.get("eval_count", 0),
                        "eval_duration": result.get("eval_duration", 0),
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error {response.status}: {error_text}")
                    return {
                        "content": f"Ollama API error: {response.status}",
                        "error": True,
                    }

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return {"content": f"Local LLM unavailable: {e}", "error": True}


class CodeGenerationProvider:
    """
    Specialized provider for code generation models (Codestral, CodeLlama, etc.).
    Optimized for programming tasks with intelligent model selection.
    """

    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        # Prioritize DeepSeek as primary model (optimized for Q9550 system)
        self.model_name = "deepseek-coder:1.3b-base-q4_0"
        self.fallback_models = [
            "deepseek-coder:1.3b-base-q4_0",  # DeepSeek Coder (lightweight, fast)
            "codellama:7b-instruct-q4_0",  # Meta's code model
            "codellama:7b-instruct",  # Meta's code model
            "codestral:22b-v0.1-q4_0",  # Mistral AI's code model (fallback only)
            "llama3.2:3b-instruct-q4_0",
        ]

    async def is_ready(self) -> bool:
        """Check if any code generation model is available."""
        if not await self.ollama.is_available():
            return False

        models = await self.ollama.list_models()
        model_names = [m.get("name", "") for m in models]

        # Check if primary or fallback model available
        for model in [self.model_name] + self.fallback_models:
            if any(model in name for name in model_names):
                return True
        return False

    async def get_available_model(self) -> Optional[str]:
        """Get the best available model."""
        models = await self.ollama.list_models()
        model_names = [m.get("name", "") for m in models]

        # Try models in order of preference
        for model in [self.model_name] + self.fallback_models:
            if any(model in name for name in model_names):
                # Return exact match from available models
                for name in model_names:
                    if model in name:
                        return name
        return None

    def _get_model_specific_prompt(self, model: str, prompt: str, language: str) -> str:
        """Get model-specific prompt optimization."""

        if "deepseek" in model.lower():
            # DeepSeek Coder specific prompting (optimized for code generation)
            return f"""You are DeepSeek Coder, an AI assistant specialized in {language} programming.

Task: {prompt}

Please provide clean, efficient {language} code that:
- Follows {language} best practices and conventions
- Is well-structured and readable
- Includes appropriate error handling
- Has concise but helpful comments where needed
- Is optimized for performance

Generate only the requested {language} code:"""

        elif "codestral" in model.lower():
            # Codestral specific prompting
            return f"""<s>[INST] You are Codestral, a helpful coding assistant specialized in {language}.

Task: {prompt}

Requirements:
- Write clean, efficient, and well-documented code
- Follow {language} best practices and conventions
- Include type hints where applicable
- Add brief comments for complex logic
- Handle edge cases and errors appropriately

Generate only the requested {language} code: [/INST]"""

        elif "codellama" in model.lower():
            # CodeLlama specific prompting
            return f"""[INST] Generate {language} code for: {prompt}

Requirements:
- Clean, readable code
- Proper error handling
- Follow best practices
- Include comments where needed [/INST]"""

        else:
            # Generic prompting for other models
            return f"Generate {language} code: {prompt}"

    async def generate_code(
        self, prompt: str, context: Optional[str] = None, language: str = "python"
    ) -> Dict[str, Any]:
        """
        Generate code using the best available model (Codestral preferred).

        Args:
            prompt: The coding task description
            context: Additional context or existing code
            language: Programming language (python, javascript, etc.)

        Returns:
            Dict with generated code and metadata
        """

        model = await self.get_available_model()
        if not model:
            return {
                "content": "No code generation model available. Please pull codestral:22b-v0.1-q4_0 or codellama:7b-instruct",
                "error": True,
            }

        # Use model-specific prompting
        if context:
            enhanced_prompt = f"Context:\n{context}\n\nTask: {prompt}"
        else:
            enhanced_prompt = prompt

        optimized_prompt = self._get_model_specific_prompt(
            model, enhanced_prompt, language
        )

        # Adjust generation parameters based on model
        if "deepseek" in model.lower():
            temperature = 0.2  # DeepSeek Coder works well with slightly higher temp than Codestral
            max_tokens = 2000  # Reasonable limit for 1.3B model
        elif "codestral" in model.lower():
            temperature = 0.1  # Codestral works better with lower temp
            max_tokens = 4000  # Codestral can handle longer outputs
        else:
            temperature = 0.3
            max_tokens = 2000

        result = await self.ollama.generate(
            model=model,
            prompt=optimized_prompt,
            system=None,  # System message is included in the prompt for model-specific formatting
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if result.get("error"):
            return result

        # Post-process code response
        content = result.get("content", "").strip()

        # Extract code from markdown blocks if present
        if "```" in content:
            lines = content.split("\n")
            code_lines = []
            in_code_block = False

            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    code_lines.append(line)

            if code_lines:
                content = "\n".join(code_lines)

        return {
            "content": content,
            "model": model,
            "language": language,
            "tokens_used": result.get("eval_count", 0),
            "generation_time": result.get("eval_duration", 0)
            / 1_000_000,  # Convert to seconds
        }


# Integration with MyCoder adaptive modes
async def get_ollama_provider() -> Optional[CodeGenerationProvider]:
    """Get Ollama code generation provider if available."""
    try:
        async with OllamaClient() as client:
            if await client.is_available():
                provider = CodeGenerationProvider(client)
                if await provider.is_ready():
                    return provider
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Ollama provider: {e}")
        return None


# Example usage
async def demo_ollama():
    """Demo Ollama integration."""
    print("🤖 Testing Ollama integration...")

    async with OllamaClient() as client:
        # Check availability
        if not await client.is_available():
            print("❌ Ollama not available")
            return

        print("✅ Ollama is available")

        # List models
        models = await client.list_models()
        print(f"📋 Available models: {len(models)}")
        for model in models[:3]:  # Show first 3
            print(f"   • {model.get('name', 'unknown')}")

        # Test Code Generation
        provider = CodeGenerationProvider(client)
        if await provider.is_ready():
            model = await provider.get_available_model()
            print(f"✅ Code generation ready with model: {model}")

            result = await provider.generate_code(
                "Create a Python function that reads a CSV file and returns a pandas DataFrame",
                language="python",
            )

            print("🎯 Generated code:")
            print("-" * 40)
            print(result.get("content", "No response"))
            print("-" * 40)
            print(f"Model: {result.get('model')}")
            print(f"Tokens: {result.get('tokens_used')}")
            print(f"Generation time: {result.get('generation_time', 0):.2f}s")
        else:
            print("❌ No code generation models ready")


if __name__ == "__main__":
    asyncio.run(demo_ollama())
