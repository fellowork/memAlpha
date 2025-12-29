"""Embedding providers for memAlpha."""

import os
from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer
from openai import OpenAI


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (local/openai)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        pass


class LocalEmbedding(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize local embedding provider.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self._model_name = model_name
        self._model = None  # Lazy loading

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load_model(self):
        """Load the model lazily on first use."""
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        self._load_model()
        embedding = self._model.encode([text])[0]
        # Handle both numpy arrays and lists (for testing)
        return embedding.tolist() if hasattr(embedding, 'tolist') else embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        embeddings = self._model.encode(texts)
        # Handle both numpy arrays and lists (for testing)
        return [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding provider."""

    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self):
        """Initialize OpenAI embedding provider from environment variables."""
        self.api_key = os.getenv("MEMALPHA_OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "MEMALPHA_OPENAI_API_KEY environment variable is required for OpenAI embeddings"
            )

        self.base_url = os.getenv(
            "MEMALPHA_OPENAI_BASE_URL",
            "https://api.openai.com/v1"
        )
        self._model_name = os.getenv(
            "MEMALPHA_OPENAI_MODEL",
            "text-embedding-3-small"
        )

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI API."""
        response = self.client.embeddings.create(
            model=self._model_name,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API."""
        response = self.client.embeddings.create(
            model=self._model_name,
            input=texts
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self.MODEL_DIMENSIONS.get(self._model_name, 1536)


def get_embedding_provider() -> EmbeddingProvider:
    """Factory function to get the configured embedding provider.
    
    Returns:
        EmbeddingProvider instance based on MEMALPHA_EMBEDDING_PROVIDER env var
        
    Raises:
        ValueError: If unknown provider is specified
    """
    provider_name = os.getenv("MEMALPHA_EMBEDDING_PROVIDER", "local").lower()

    if provider_name == "local":
        return LocalEmbedding()
    elif provider_name == "openai":
        return OpenAIEmbedding()
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider_name}. "
            "Valid options are: 'local', 'openai'"
        )

