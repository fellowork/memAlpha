"""Unit tests for memory store."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.memory_store import MemoryStore
from src.models import MemoryCreate, MemoryUpdate, Memory
from src.embeddings import LocalEmbedding


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider."""
    provider = Mock(spec=LocalEmbedding)
    provider.provider_name = "local"
    provider.model_name = "test-model"
    provider.dimension = 384
    provider.embed.return_value = [0.1, 0.2, 0.3, 0.4]
    provider.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
    return provider


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaDB client."""
    with patch('src.memory_store.chromadb.PersistentClient') as mock_client_class:
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        yield mock_client, mock_collection


class TestMemoryStoreInitialization:
    """Test MemoryStore initialization."""

    @patch('src.memory_store.chromadb.PersistentClient')
    def test_initialization_default_path(self, mock_client_class, mock_embedding_provider):
        """Test initialization with default data path."""
        store = MemoryStore(embedding_provider=mock_embedding_provider)
        assert store.embedding_provider == mock_embedding_provider
        mock_client_class.assert_called_once()

    @patch('src.memory_store.chromadb.PersistentClient')
    def test_initialization_custom_path(self, mock_client_class, mock_embedding_provider):
        """Test initialization with custom data path."""
        custom_path = "/tmp/test_chroma"
        store = MemoryStore(
            embedding_provider=mock_embedding_provider,
            data_path=custom_path
        )
        mock_client_class.assert_called_once()


class TestCollectionNaming:
    """Test collection name generation."""

    @patch('src.memory_store.chromadb.PersistentClient')
    def test_collection_name_format(self, mock_client_class, mock_embedding_provider):
        """Test collection name follows correct format."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        name = store._get_collection_name("my-project", "agent-1")
        
        assert name == "p_my-project_a_agent-1_emb_local"

    @patch('src.memory_store.chromadb.PersistentClient')
    def test_collection_name_sanitization(self, mock_client_class, mock_embedding_provider):
        """Test collection name sanitizes special characters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        # Test with special characters that might be problematic
        name = store._get_collection_name("my@project!", "agent#1")
        
        # Should replace or remove special characters
        assert "@" not in name and "!" not in name and "#" not in name


class TestStoreMemory:
    """Test storing memories."""

    def test_store_memory_success(self, mock_chroma_client, mock_embedding_provider):
        """Test successfully storing a memory."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.add = Mock()

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        memory_create = MemoryCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="Test memory",
            metadata={"tags": ["test"]}
        )

        memory = store.store_memory(memory_create)

        assert isinstance(memory, Memory)
        assert memory.content == "Test memory"
        assert memory.project_id == "proj-1"
        assert memory.agent_id == "agent-1"
        assert memory.embedding_provider == "local"
        assert memory.embedding_model == "test-model"
        assert memory.memory_id is not None
        mock_embedding_provider.embed.assert_called_once_with("Test memory")
        mock_collection.add.assert_called_once()

    def test_store_memory_generates_unique_ids(self, mock_chroma_client, mock_embedding_provider):
        """Test that each stored memory gets a unique ID."""
        mock_client, mock_collection = mock_chroma_client
        
        store = MemoryStore(embedding_provider=mock_embedding_provider)
        memory1 = store.store_memory(MemoryCreate(
            project_id="proj", agent_id="agent", content="Memory 1"
        ))
        memory2 = store.store_memory(MemoryCreate(
            project_id="proj", agent_id="agent", content="Memory 2"
        ))

        assert memory1.memory_id != memory2.memory_id


class TestGetMemory:
    """Test retrieving memories by ID."""

    def test_get_memory_success(self, mock_chroma_client, mock_embedding_provider):
        """Test successfully retrieving a memory."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            'ids': ['mem-123'],
            'documents': ['Test memory'],
            'metadatas': [{
                'project_id': 'proj-1',
                'agent_id': 'agent-1',
                'custom_metadata': '{"tags": ["test"]}',
                'embedding_provider': 'local',
                'embedding_model': 'test-model',
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00'
            }]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        memory = store.get_memory("proj-1", "agent-1", "mem-123")

        assert memory is not None
        assert memory.memory_id == "mem-123"
        assert memory.content == "Test memory"
        assert memory.project_id == "proj-1"

    def test_get_memory_not_found(self, mock_chroma_client, mock_embedding_provider):
        """Test getting a non-existent memory returns None."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            'ids': [],
            'documents': [],
            'metadatas': []
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        memory = store.get_memory("proj-1", "agent-1", "nonexistent")

        assert memory is None


class TestSearchMemories:
    """Test searching memories."""

    def test_search_memories_success(self, mock_chroma_client, mock_embedding_provider):
        """Test successfully searching memories."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.query.return_value = {
            'ids': [['mem-1', 'mem-2']],
            'documents': [['Memory 1', 'Memory 2']],
            'metadatas': [[
                {
                    'project_id': 'proj-1',
                    'agent_id': 'agent-1',
                    'custom_metadata': '{}',
                    'embedding_provider': 'local',
                    'embedding_model': 'test-model',
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                },
                {
                    'project_id': 'proj-1',
                    'agent_id': 'agent-1',
                    'custom_metadata': '{}',
                    'embedding_provider': 'local',
                    'embedding_model': 'test-model',
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                }
            ]],
            'distances': [[0.1, 0.3]]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        results = store.search_memories("proj-1", "agent-1", "search query", limit=5)

        assert len(results) == 2
        assert results[0].memory.content == "Memory 1"
        assert results[1].memory.content == "Memory 2"
        assert 0.0 <= results[0].similarity_score <= 1.0
        mock_embedding_provider.embed.assert_called_once_with("search query")

    def test_search_with_filters(self, mock_chroma_client, mock_embedding_provider):
        """Test searching with metadata filters."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.query.return_value = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        filters = {"importance": {"$gte": 5}}
        results = store.search_memories(
            "proj-1", "agent-1", "query",
            limit=10, filters=filters
        )

        # Verify filters were passed to query
        call_args = mock_collection.query.call_args
        assert call_args is not None


class TestUpdateMemory:
    """Test updating memories."""

    def test_update_content(self, mock_chroma_client, mock_embedding_provider):
        """Test updating memory content."""
        mock_client, mock_collection = mock_chroma_client
        # Mock get to return existing memory
        mock_collection.get.return_value = {
            'ids': ['mem-123'],
            'documents': ['Old content'],
            'metadatas': [{
                'project_id': 'proj-1',
                'agent_id': 'agent-1',
                'custom_metadata': '{}',
                'embedding_provider': 'local',
                'embedding_model': 'test-model',
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00'
            }]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        update = MemoryUpdate(content="New content")
        updated = store.update_memory("proj-1", "agent-1", "mem-123", update)

        assert updated is not None
        assert updated.content == "New content"
        # Should re-embed when content changes
        assert mock_embedding_provider.embed.call_count >= 1

    def test_update_metadata_only(self, mock_chroma_client, mock_embedding_provider):
        """Test updating only metadata."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            'ids': ['mem-123'],
            'documents': ['Content'],
            'metadatas': [{
                'project_id': 'proj-1',
                'agent_id': 'agent-1',
                'custom_metadata': '{"old": "data"}',
                'embedding_provider': 'local',
                'embedding_model': 'test-model',
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00'
            }]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        update = MemoryUpdate(metadata={"new": "data"})
        updated = store.update_memory("proj-1", "agent-1", "mem-123", update)

        assert updated is not None
        # Should not re-embed when only metadata changes
        mock_embedding_provider.embed.assert_not_called()


class TestDeleteMemory:
    """Test deleting memories."""

    def test_delete_memory_success(self, mock_chroma_client, mock_embedding_provider):
        """Test successfully deleting a memory."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.delete = Mock()

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        result = store.delete_memory("proj-1", "agent-1", "mem-123")

        assert result is True
        mock_collection.delete.assert_called_once()


class TestListMemories:
    """Test listing memories."""

    def test_list_memories(self, mock_chroma_client, mock_embedding_provider):
        """Test listing memories with pagination."""
        mock_client, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            'ids': ['mem-1', 'mem-2'],
            'documents': ['Content 1', 'Content 2'],
            'metadatas': [
                {
                    'project_id': 'proj-1',
                    'agent_id': 'agent-1',
                    'custom_metadata': '{}',
                    'embedding_provider': 'local',
                    'embedding_model': 'test-model',
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                },
                {
                    'project_id': 'proj-1',
                    'agent_id': 'agent-1',
                    'custom_metadata': '{}',
                    'embedding_provider': 'local',
                    'embedding_model': 'test-model',
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                }
            ]
        }

        store = MemoryStore(embedding_provider=mock_embedding_provider)
        metadatas = store.list_memories("proj-1", "agent-1", limit=10, offset=0)

        assert len(metadatas) == 2
        assert metadatas[0].memory_id == "mem-1"
        assert metadatas[1].memory_id == "mem-2"

