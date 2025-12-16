"""
LLM Factory Module.

Provides a unified interface for creating LLM instances across different providers.
Supports Groq (Llama 3.3, Mixtral), HuggingFace, and Ollama.
"""

from app.core.config import LLMProvider, Settings, get_settings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class LLMFactory:
    """Factory class for creating LLM and embedding instances."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def create_llm(self, temperature: float = 0.7) -> BaseChatModel:
        """
        Create an LLM instance based on the configured provider.

        Args:
            temperature: Sampling temperature for generation.

        Returns:
            A LangChain chat model instance.

        Raises:
            ValueError: If the provider is not supported or API key is missing.
        """
        provider = self.settings.llm_provider

        if provider == LLMProvider.GROQ:
            return self._create_groq_llm(temperature)
        elif provider == LLMProvider.HUGGINGFACE:
            return self._create_huggingface_llm(temperature)
        elif provider == LLMProvider.OLLAMA:
            return self._create_ollama_llm(temperature)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _create_groq_llm(self, temperature: float) -> BaseChatModel:
        """Create a Groq LLM instance (Llama 3.3, Mixtral)."""
        if not self.settings.groq_api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable. "
                "Get a free API key at https://console.groq.com/"
            )

        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=self.settings.groq_api_key,
            model_name=self.settings.groq_model,
            temperature=temperature,
            max_tokens=4096,
        )

    def _create_huggingface_llm(self, temperature: float) -> BaseChatModel:
        """Create a HuggingFace LLM instance."""
        if not self.settings.huggingface_api_key:
            raise ValueError(
                "HuggingFace API key is required. Set HUGGINGFACE_API_KEY environment variable."
            )

        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

        llm = HuggingFaceEndpoint(
            repo_id=self.settings.huggingface_model,
            huggingfacehub_api_token=self.settings.huggingface_api_key,
            temperature=temperature,
            max_new_tokens=4096,
        )
        return ChatHuggingFace(llm=llm)

    def _create_ollama_llm(self, temperature: float) -> BaseChatModel:
        """Create an Ollama LLM instance for local models."""
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_model,
            temperature=temperature,
        )

    def create_embeddings(self) -> Embeddings:
        """
        Create an embeddings instance using HuggingFace sentence-transformers.

        Returns:
            A LangChain embeddings instance.
        """
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=self.settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """
    Convenience function to get an LLM instance.

    Args:
        temperature: Sampling temperature for generation.

    Returns:
        A LangChain chat model instance.
    """
    factory = LLMFactory()
    return factory.create_llm(temperature)


def get_embeddings() -> Embeddings:
    """
    Convenience function to get an embeddings instance.

    Returns:
        A LangChain embeddings instance.
    """
    factory = LLMFactory()
    return factory.create_embeddings()
