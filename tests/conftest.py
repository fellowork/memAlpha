"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.embeddings import LocalEmbedding
from src.memory_store import MemoryStore


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="memalpha_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider for testing."""
    provider = Mock(spec=LocalEmbedding)
    provider.provider_name = "local"
    provider.model_name = "test-model"
    provider.dimension = 384
    provider.embed.return_value = [0.1] * 384
    provider.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    return provider


@pytest.fixture
def memory_store(mock_embedding_provider, temp_data_dir):
    """Create a memory store for testing."""
    return MemoryStore(
        embedding_provider=mock_embedding_provider,
        data_path=temp_data_dir
    )


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    import os
    env_backup = os.environ.copy()
    yield
    # Restore environment
    os.environ.clear()
    os.environ.update(env_backup)


# BDD-specific fixtures
@pytest.fixture
def context(request):
    """Shared context for BDD tests."""
    if not hasattr(request, 'context'):
        from tests.test_bdd_steps import TestContext
        request.context = TestContext()
    return request.context

