"""
LLM Integration Module
Handles DeepSeek-R1 integration via Ollama
"""

from .ollama_client import OllamaClient
from .prompt_templates import PromptTemplate

__all__ = ["OllamaClient", "PromptTemplate"]
