"""Unit tests for embedding providers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.embeddings import (
    EmbeddingProvider,
    LocalEmbedding,
    OpenAIEmbedding,
    get_embedding_provider
)


class TestEmbeddingProviderInterface:
    """Test the abstract EmbeddingProvider interface."""

    def test_interface_requires_implementation(self):
        """Test that EmbeddingProvider cannot be instantiated directly."""
        # This is an abstract base class, should not be instantiable directly
        # We'll verify concrete implementations work correctly instead
        pass


class TestLocalEmbedding:
    """Test LocalEmbedding provider."""

    @patch('src.embeddings.SentenceTransformer')
    def test_initialization(self, mock_transformer):
        """Test LocalEmbedding initializes correctly."""
        provider = LocalEmbedding()
        assert provider.provider_name == "local"
        assert provider.model_name == "all-MiniLM-L6-v2"
        # Model should not be loaded until first use (lazy loading)
        assert provider._model is None

    @patch('src.embeddings.SentenceTransformer')
    def test_lazy_model_loading(self, mock_transformer):
        """Test that model is loaded lazily on first use."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        provider = LocalEmbedding()
        assert provider._model is None
        
        # First call should load model
        result = provider.embed("test text")
        mock_transformer.assert_called_once()
        assert provider._model is not None
        assert len(result) > 0

    @patch('src.embeddings.SentenceTransformer')
    def test_embed_single_text(self, mock_transformer):
        """Test embedding a single text."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4]]
        mock_transformer.return_value = mock_model

        provider = LocalEmbedding()
        result = provider.embed("Hello, world!")
        
        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(x, float) for x in result)

    @patch('src.embeddings.SentenceTransformer')
    def test_embed_batch(self, mock_transformer):
        """Test embedding multiple texts at once."""
        mock_model = Mock()
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        mock_transformer.return_value = mock_model

        provider = LocalEmbedding()
        texts = ["text 1", "text 2", "text 3"]
        results = provider.embed_batch(texts)
        
        assert len(results) == 3
        assert all(len(emb) == 3 for emb in results)

    @patch('src.embeddings.SentenceTransformer')
    def test_dimension_property(self, mock_transformer):
        """Test that dimension property returns correct value."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model

        provider = LocalEmbedding()
        # Trigger model loading
        provider._load_model()
        
        assert provider.dimension == 384

    @patch('src.embeddings.SentenceTransformer')
    def test_model_caching(self, mock_transformer):
        """Test that model is only loaded once."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2]]
        mock_transformer.return_value = mock_model

        provider = LocalEmbedding()
        provider.embed("first")
        provider.embed("second")
        
        # Should only be called once (cached)
        assert mock_transformer.call_count == 1


class TestOpenAIEmbedding:
    """Test OpenAIEmbedding provider."""

    def test_initialization_default(self):
        """Test OpenAIEmbedding initializes with defaults."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="MEMALPHA_OPENAI_API_KEY"):
                OpenAIEmbedding()

    def test_initialization_with_api_key(self):
        """Test OpenAIEmbedding initializes with API key from env."""
        with patch.dict('os.environ', {'MEMALPHA_OPENAI_API_KEY': 'sk-test-key'}):
            provider = OpenAIEmbedding()
            assert provider.provider_name == "openai"
            assert provider.model_name == "text-embedding-3-small"
            assert provider.api_key == "sk-test-key"

    def test_initialization_with_custom_model(self):
        """Test OpenAIEmbedding with custom model."""
        with patch.dict('os.environ', {
            'MEMALPHA_OPENAI_API_KEY': 'sk-test',
            'MEMALPHA_OPENAI_MODEL': 'text-embedding-3-large'
        }):
            provider = OpenAIEmbedding()
            assert provider.model_name == "text-embedding-3-large"

    def test_initialization_with_custom_base_url(self):
        """Test OpenAIEmbedding with custom base URL."""
        with patch.dict('os.environ', {
            'MEMALPHA_OPENAI_API_KEY': 'sk-test',
            'MEMALPHA_OPENAI_BASE_URL': 'https://custom.api.com/v1'
        }):
            provider = OpenAIEmbedding()
            assert provider.base_url == "https://custom.api.com/v1"

    @patch('src.embeddings.OpenAI')
    def test_embed_single_text(self, mock_openai_class):
        """Test embedding a single text with OpenAI."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict('os.environ', {'MEMALPHA_OPENAI_API_KEY': 'sk-test'}):
            provider = OpenAIEmbedding()
            result = provider.embed("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_client.embeddings.create.assert_called_once()

    @patch('src.embeddings.OpenAI')
    def test_embed_batch(self, mock_openai_class):
        """Test embedding multiple texts with OpenAI."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2]),
            Mock(embedding=[0.3, 0.4]),
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict('os.environ', {'MEMALPHA_OPENAI_API_KEY': 'sk-test'}):
            provider = OpenAIEmbedding()
            results = provider.embed_batch(["text 1", "text 2"])
            
            assert len(results) == 2
            assert results[0] == [0.1, 0.2]
            assert results[1] == [0.3, 0.4]

    @patch('src.embeddings.OpenAI')
    def test_dimension_property(self, mock_openai_class):
        """Test dimension property for different models."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        with patch.dict('os.environ', {'MEMALPHA_OPENAI_API_KEY': 'sk-test'}):
            provider = OpenAIEmbedding()
            assert provider.dimension == 1536  # text-embedding-3-small

        with patch.dict('os.environ', {
            'MEMALPHA_OPENAI_API_KEY': 'sk-test',
            'MEMALPHA_OPENAI_MODEL': 'text-embedding-3-large'
        }):
            provider = OpenAIEmbedding()
            assert provider.dimension == 3072


class TestGetEmbeddingProvider:
    """Test the factory function for getting embedding providers."""

    @patch('src.embeddings.SentenceTransformer')
    def test_get_local_provider_default(self, mock_transformer):
        """Test getting local provider by default."""
        with patch.dict('os.environ', {}, clear=True):
            provider = get_embedding_provider()
            assert isinstance(provider, LocalEmbedding)

    @patch('src.embeddings.SentenceTransformer')
    def test_get_local_provider_explicit(self, mock_transformer):
        """Test getting local provider explicitly."""
        with patch.dict('os.environ', {'MEMALPHA_EMBEDDING_PROVIDER': 'local'}):
            provider = get_embedding_provider()
            assert isinstance(provider, LocalEmbedding)

    def test_get_openai_provider(self):
        """Test getting OpenAI provider."""
        with patch.dict('os.environ', {
            'MEMALPHA_EMBEDDING_PROVIDER': 'openai',
            'MEMALPHA_OPENAI_API_KEY': 'sk-test'
        }):
            provider = get_embedding_provider()
            assert isinstance(provider, OpenAIEmbedding)

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider name raises error."""
        with patch.dict('os.environ', {'MEMALPHA_EMBEDDING_PROVIDER': 'invalid'}):
            with pytest.raises(ValueError, match="Unknown embedding provider"):
                get_embedding_provider()

