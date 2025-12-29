"""Unit tests for data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.models import Memory, MemoryMetadata, MemoryCreate, MemoryUpdate


class TestMemoryCreate:
    """Test MemoryCreate model."""

    def test_create_with_minimal_fields(self):
        """Test creating memory with only required fields."""
        memory = MemoryCreate(
            project_id="test-project",
            agent_id="test-agent",
            content="This is a test memory"
        )
        assert memory.project_id == "test-project"
        assert memory.agent_id == "test-agent"
        assert memory.content == "This is a test memory"
        assert memory.metadata == {}

    def test_create_with_metadata(self):
        """Test creating memory with custom metadata."""
        metadata = {
            "tags": ["important", "bug-fix"],
            "category": "procedure",
            "importance": 8
        }
        memory = MemoryCreate(
            project_id="project-1",
            agent_id="agent-1",
            content="Fixed authentication bug",
            metadata=metadata
        )
        assert memory.metadata == metadata

    def test_create_empty_content_fails(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError):
            MemoryCreate(
                project_id="test",
                agent_id="test",
                content=""
            )

    def test_create_missing_project_id_fails(self):
        """Test that missing project_id raises validation error."""
        with pytest.raises(ValidationError):
            MemoryCreate(
                agent_id="test",
                content="test content"
            )

    def test_create_missing_agent_id_fails(self):
        """Test that missing agent_id raises validation error."""
        with pytest.raises(ValidationError):
            MemoryCreate(
                project_id="test",
                content="test content"
            )


class TestMemory:
    """Test Memory model (full memory with ID and timestamps)."""

    def test_memory_with_all_fields(self):
        """Test creating a complete memory object."""
        now = datetime.now()
        memory = Memory(
            memory_id="mem-123",
            project_id="proj-1",
            agent_id="agent-1",
            content="Test memory content",
            metadata={"tags": ["test"]},
            embedding_provider="local",
            embedding_model="all-MiniLM-L6-v2",
            created_at=now,
            updated_at=now
        )
        assert memory.memory_id == "mem-123"
        assert memory.project_id == "proj-1"
        assert memory.agent_id == "agent-1"
        assert memory.content == "Test memory content"
        assert memory.embedding_provider == "local"
        assert memory.embedding_model == "all-MiniLM-L6-v2"

    def test_memory_timestamps_auto_generated(self):
        """Test that timestamps are auto-generated if not provided."""
        memory = Memory(
            memory_id="mem-123",
            project_id="proj-1",
            agent_id="agent-1",
            content="Test",
            embedding_provider="local",
            embedding_model="all-MiniLM-L6-v2"
        )
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)


class TestMemoryUpdate:
    """Test MemoryUpdate model."""

    def test_update_content_only(self):
        """Test updating only content."""
        update = MemoryUpdate(content="Updated content")
        assert update.content == "Updated content"
        assert update.metadata is None

    def test_update_metadata_only(self):
        """Test updating only metadata."""
        metadata = {"tags": ["updated"]}
        update = MemoryUpdate(metadata=metadata)
        assert update.content is None
        assert update.metadata == metadata

    def test_update_both_fields(self):
        """Test updating both content and metadata."""
        update = MemoryUpdate(
            content="New content",
            metadata={"importance": 10}
        )
        assert update.content == "New content"
        assert update.metadata == {"importance": 10}

    def test_update_empty_is_valid(self):
        """Test that an empty update is valid (partial updates)."""
        update = MemoryUpdate()
        assert update.content is None
        assert update.metadata is None


class TestMemoryMetadata:
    """Test MemoryMetadata model (for list operations)."""

    def test_metadata_without_content(self):
        """Test metadata model doesn't include content."""
        metadata = MemoryMetadata(
            memory_id="mem-123",
            project_id="proj-1",
            agent_id="agent-1",
            metadata={"tags": ["test"]},
            embedding_provider="local",
            embedding_model="all-MiniLM-L6-v2",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert metadata.memory_id == "mem-123"
        assert not hasattr(metadata, 'content')  # Should not have content field

