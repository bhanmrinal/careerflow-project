"""
LLM Factory Module.

Provides LLM and embedding instances using Groq API (Llama 3.3 70B, Mixtral 8x7B).
"""

from app.core.config import Settings, get_settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq


class LLMFactory:
    """Factory class for creating LLM and embedding instances."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def create_llm(self, temperature: float = 0.7) -> BaseChatModel:
        """
        Create a Groq LLM instance (Llama 3.3 70B or Mixtral 8x7B).

        Args:
            temperature: Sampling temperature for generation.

        Returns:
            A LangChain ChatGroq instance.

        Raises:
            ValueError: If Groq API key is not configured.
        """
        if not self.settings.groq_api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable. "
                "Get a free API key at https://console.groq.com/"
            )

        return ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.groq_model,
            temperature=temperature,
            max_tokens=4096,
        )

    def create_embeddings(self) -> Embeddings:
        """
        Create an embeddings instance using sentence-transformers.

        Returns:
            A LangChain HuggingFaceEmbeddings instance.
        """
        return HuggingFaceEmbeddings(
            model_name=self.settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """
    Get a Groq LLM instance.

    Args:
        temperature: Sampling temperature for generation.

    Returns:
        A LangChain ChatGroq instance.
    """
    factory = LLMFactory()
    return factory.create_llm(temperature)


def get_embeddings() -> Embeddings:
    """
    Get a sentence-transformers embeddings instance.

    Returns:
        A LangChain HuggingFaceEmbeddings instance.
    """
    factory = LLMFactory()
    return factory.create_embeddings()
