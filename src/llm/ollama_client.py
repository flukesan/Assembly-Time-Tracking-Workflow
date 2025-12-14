"""
Ollama Client
Interfaces with local Ollama instance running DeepSeek-R1
"""

import logging
import json
from typing import Optional, List, Dict, Any
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """LLM response with reasoning chain"""
    content: str
    reasoning: Optional[str] = None
    model: Optional[str] = None
    total_duration_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class OllamaClient:
    """
    Ollama Client for DeepSeek-R1

    Features:
    - Supports streaming and non-streaming responses
    - Shows reasoning chain (thinking process)
    - Thai + English bilingual support
    - 100% local execution
    """

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "deepseek-r1:14b",
        timeout: int = 120
    ):
        """
        Initialize Ollama client

        Args:
            base_url: Ollama API base URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        logger.info(
            f"OllamaClient initialized (model={model}, base_url={base_url})"
        )

    async def check_connection(self) -> bool:
        """
        Check if Ollama is accessible

        Returns:
            True if connected, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models

        Returns:
            List of model information
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Pull/download a model

        Args:
            model_name: Model to pull (default: self.model)

        Returns:
            True if successful
        """
        model = model_name or self.model

        try:
            logger.info(f"Pulling model {model}...")

            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/pull",
                json={"name": model}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get('status', '')
                        logger.info(f"Pull status: {status}")

            logger.info(f"Model {model} pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        show_reasoning: bool = True
    ) -> LLMResponse:
        """
        Chat with DeepSeek-R1

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            show_reasoning: Whether to show reasoning chain

        Returns:
            LLM response with reasoning
        """
        try:
            # Prepare request
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ],
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            if max_tokens:
                request_data["options"]["num_predict"] = max_tokens

            # Send request
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=request_data
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            message = data.get('message', {})
            content = message.get('content', '')

            # Extract reasoning if present
            reasoning = None
            actual_content = content

            if show_reasoning and '<think>' in content and '</think>' in content:
                # DeepSeek-R1 wraps thinking in <think> tags
                try:
                    think_start = content.index('<think>') + 7
                    think_end = content.index('</think>')
                    reasoning = content[think_start:think_end].strip()
                    actual_content = content[think_end + 8:].strip()
                except ValueError:
                    pass

            # Get metrics
            total_duration = data.get('total_duration')
            prompt_eval_count = data.get('prompt_eval_count')
            eval_count = data.get('eval_count')

            return LLMResponse(
                content=actual_content,
                reasoning=reasoning,
                model=data.get('model'),
                total_duration_ms=total_duration // 1_000_000 if total_duration else None,
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count
            )

        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        show_reasoning: bool = True
    ) -> LLMResponse:
        """
        Generate completion for a prompt

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            show_reasoning: Whether to show reasoning

        Returns:
            LLM response
        """
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            show_reasoning=show_reasoning
        )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Stream chat responses (for real-time UI)

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Response chunks
        """
        try:
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ],
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }

            if max_tokens:
                request_data["options"]["num_predict"] = max_tokens

            async with self.client.stream(
                'POST',
                f"{self.base_url}/api/chat",
                json=request_data
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if 'message' in data:
                            content = data['message'].get('content', '')
                            if content:
                                yield content

        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager enter"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def get_stats(self) -> dict:
        """Get client statistics"""
        return {
            'model': self.model,
            'base_url': self.base_url,
            'timeout': self.timeout
        }
