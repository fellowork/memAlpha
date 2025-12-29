"""Unit tests for scratchpad functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

from src.models import ScratchpadCreate, ScratchpadUpdate, Scratchpad
from src.scratchpad_store import ScratchpadStore


class TestScratchpadModels:
    """Test scratchpad data models."""

    def test_create_scratchpad_minimal(self):
        """Test creating scratchpad with minimal fields."""
        scratchpad = ScratchpadCreate(
            project_id="test-project",
            agent_id="test-agent",
            content="My notes here"
        )
        assert scratchpad.project_id == "test-project"
        assert scratchpad.agent_id == "test-agent"
        assert scratchpad.content == "My notes here"

    def test_create_scratchpad_empty_content_allowed(self):
        """Test that empty content is allowed (agent can create blank scratchpad)."""
        scratchpad = ScratchpadCreate(
            project_id="test-project",
            agent_id="test-agent",
            content=""
        )
        assert scratchpad.content == ""

    def test_create_scratchpad_missing_required_fields(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValidationError):
            ScratchpadCreate(
                project_id="test",
                content="test"
                # Missing agent_id
            )

    def test_scratchpad_update_model(self):
        """Test scratchpad update model."""
        update = ScratchpadUpdate(content="Updated content")
        assert update.content == "Updated content"

    def test_scratchpad_update_empty_allowed(self):
        """Test that empty update content is allowed."""
        update = ScratchpadUpdate(content="")
        assert update.content == ""

    def test_full_scratchpad_model(self):
        """Test full scratchpad model with timestamps."""
        now = datetime.now()
        scratchpad = Scratchpad(
            project_id="proj-1",
            agent_id="agent-1",
            content="Test content",
            created_at=now,
            updated_at=now
        )
        assert scratchpad.project_id == "proj-1"
        assert scratchpad.agent_id == "agent-1"
        assert scratchpad.content == "Test content"
        assert isinstance(scratchpad.created_at, datetime)
        assert isinstance(scratchpad.updated_at, datetime)


class TestScratchpadStore:
    """Test scratchpad storage operations."""

    @pytest.fixture
    def temp_store_dir(self):
        """Create a temporary directory for scratchpad storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def scratchpad_store(self, temp_store_dir):
        """Create a scratchpad store with temporary directory."""
        return ScratchpadStore(data_path=temp_store_dir)

    def test_store_initialization(self, temp_store_dir):
        """Test that store creates necessary directories."""
        store = ScratchpadStore(data_path=temp_store_dir)
        assert store.data_path.exists()
        assert store.data_path.is_dir()

    def test_create_scratchpad(self, scratchpad_store):
        """Test creating a new scratchpad."""
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="My first scratchpad"
        )
        scratchpad = scratchpad_store.create_scratchpad(create)
        
        assert scratchpad is not None
        assert scratchpad.project_id == "proj-1"
        assert scratchpad.agent_id == "agent-1"
        assert scratchpad.content == "My first scratchpad"
        assert scratchpad.created_at is not None
        assert scratchpad.updated_at is not None

    def test_create_scratchpad_when_already_exists(self, scratchpad_store):
        """Test that creating scratchpad when one exists returns None."""
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="First"
        )
        scratchpad_store.create_scratchpad(create)
        
        # Try to create again
        result = scratchpad_store.create_scratchpad(create)
        assert result is None  # Should fail because it already exists

    def test_get_scratchpad(self, scratchpad_store):
        """Test retrieving an existing scratchpad."""
        # Create first
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="Test content"
        )
        created = scratchpad_store.create_scratchpad(create)
        
        # Retrieve
        retrieved = scratchpad_store.get_scratchpad("proj-1", "agent-1")
        
        assert retrieved is not None
        assert retrieved.content == "Test content"
        assert retrieved.project_id == "proj-1"
        assert retrieved.agent_id == "agent-1"

    def test_get_scratchpad_not_found(self, scratchpad_store):
        """Test getting non-existent scratchpad returns None."""
        result = scratchpad_store.get_scratchpad("nonexistent", "agent")
        assert result is None

    def test_update_scratchpad(self, scratchpad_store):
        """Test updating an existing scratchpad."""
        # Create
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="Original content"
        )
        scratchpad_store.create_scratchpad(create)
        
        # Update
        update = ScratchpadUpdate(content="Updated content")
        updated = scratchpad_store.update_scratchpad("proj-1", "agent-1", update)
        
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.updated_at > updated.created_at

    def test_update_nonexistent_scratchpad(self, scratchpad_store):
        """Test updating non-existent scratchpad returns None."""
        update = ScratchpadUpdate(content="Test")
        result = scratchpad_store.update_scratchpad("nonexistent", "agent", update)
        assert result is None

    def test_delete_scratchpad(self, scratchpad_store):
        """Test deleting a scratchpad."""
        # Create
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="To be deleted"
        )
        scratchpad_store.create_scratchpad(create)
        
        # Delete
        result = scratchpad_store.delete_scratchpad("proj-1", "agent-1")
        assert result is True
        
        # Verify it's gone
        retrieved = scratchpad_store.get_scratchpad("proj-1", "agent-1")
        assert retrieved is None

    def test_delete_nonexistent_scratchpad(self, scratchpad_store):
        """Test deleting non-existent scratchpad returns False."""
        result = scratchpad_store.delete_scratchpad("nonexistent", "agent")
        assert result is False

    def test_list_scratchpads(self, scratchpad_store):
        """Test listing all scratchpads."""
        # Create multiple scratchpads
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-1", content="Scratch 1"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-2", content="Scratch 2"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-2", agent_id="agent-1", content="Scratch 3"
        ))
        
        # List all
        all_scratchpads = scratchpad_store.list_scratchpads()
        assert len(all_scratchpads) == 3

    def test_list_scratchpads_by_project(self, scratchpad_store):
        """Test listing scratchpads filtered by project."""
        # Create multiple scratchpads
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-1", content="Scratch 1"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-2", content="Scratch 2"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-2", agent_id="agent-1", content="Scratch 3"
        ))
        
        # List by project
        proj1_scratchpads = scratchpad_store.list_scratchpads(project_id="proj-1")
        assert len(proj1_scratchpads) == 2

    def test_list_scratchpads_by_agent(self, scratchpad_store):
        """Test listing scratchpads filtered by agent."""
        # Create multiple scratchpads
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-1", content="Scratch 1"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-1", agent_id="agent-2", content="Scratch 2"
        ))
        scratchpad_store.create_scratchpad(ScratchpadCreate(
            project_id="proj-2", agent_id="agent-1", content="Scratch 3"
        ))
        
        # List by agent
        agent1_scratchpads = scratchpad_store.list_scratchpads(agent_id="agent-1")
        assert len(agent1_scratchpads) == 2

    def test_scratchpad_persistence(self, temp_store_dir):
        """Test that scratchpads persist across store instances."""
        # Create scratchpad in first store instance
        store1 = ScratchpadStore(data_path=temp_store_dir)
        create = ScratchpadCreate(
            project_id="proj-1",
            agent_id="agent-1",
            content="Persistent content"
        )
        store1.create_scratchpad(create)
        
        # Create new store instance and retrieve
        store2 = ScratchpadStore(data_path=temp_store_dir)
        retrieved = store2.get_scratchpad("proj-1", "agent-1")
        
        assert retrieved is not None
        assert retrieved.content == "Persistent content"

    def test_filename_sanitization(self, scratchpad_store):
        """Test that special characters in IDs are handled safely."""
        create = ScratchpadCreate(
            project_id="my-project/with/slashes",
            agent_id="agent@email.com",
            content="Test"
        )
        scratchpad = scratchpad_store.create_scratchpad(create)
        assert scratchpad is not None
        
        # Should be able to retrieve it
        retrieved = scratchpad_store.get_scratchpad(
            "my-project/with/slashes",
            "agent@email.com"
        )
        assert retrieved is not None

