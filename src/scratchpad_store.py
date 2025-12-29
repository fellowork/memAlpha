"""Scratchpad store implementation using JSON files."""

import os
import json
import re
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.models import Scratchpad, ScratchpadCreate, ScratchpadUpdate


class ScratchpadStore:
    """Store for agent scratchpads using simple JSON file storage."""

    def __init__(self, data_path: Optional[str] = None):
        """Initialize scratchpad store.
        
        Args:
            data_path: Path to store scratchpad files (default: ~/.local/share/memalpha/scratchpads)
        """
        if data_path is None:
            data_path = os.path.expanduser("~/.local/share/memalpha/scratchpads")
        
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)

    def _sanitize_id(self, id_string: str) -> str:
        """Sanitize ID string to be safe for filenames.
        
        Args:
            id_string: ID to sanitize
            
        Returns:
            Sanitized ID string
        """
        # Replace unsafe characters with underscores
        return re.sub(r'[^\w\-.]', '_', id_string)

    def _get_filepath(self, project_id: str, agent_id: str) -> Path:
        """Get filepath for a scratchpad.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            
        Returns:
            Path to scratchpad file
        """
        safe_project = self._sanitize_id(project_id)
        safe_agent = self._sanitize_id(agent_id)
        filename = f"{safe_project}_{safe_agent}.json"
        return self.data_path / filename

    def _save_scratchpad(self, scratchpad: Scratchpad) -> None:
        """Save scratchpad to disk.
        
        Args:
            scratchpad: Scratchpad to save
        """
        filepath = self._get_filepath(scratchpad.project_id, scratchpad.agent_id)
        data = {
            "project_id": scratchpad.project_id,
            "agent_id": scratchpad.agent_id,
            "content": scratchpad.content,
            "created_at": scratchpad.created_at.isoformat(),
            "updated_at": scratchpad.updated_at.isoformat()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_scratchpad(self, filepath: Path) -> Optional[Scratchpad]:
        """Load scratchpad from disk.
        
        Args:
            filepath: Path to scratchpad file
            
        Returns:
            Scratchpad object or None if file doesn't exist
        """
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Scratchpad(
                project_id=data["project_id"],
                agent_id=data["agent_id"],
                content=data["content"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def create_scratchpad(self, create: ScratchpadCreate) -> Optional[Scratchpad]:
        """Create a new scratchpad.
        
        Args:
            create: Scratchpad creation request
            
        Returns:
            Created Scratchpad object, or None if already exists
        """
        filepath = self._get_filepath(create.project_id, create.agent_id)
        
        # Check if scratchpad already exists
        if filepath.exists():
            return None
        
        # Create new scratchpad
        now = datetime.now()
        scratchpad = Scratchpad(
            project_id=create.project_id,
            agent_id=create.agent_id,
            content=create.content,
            created_at=now,
            updated_at=now
        )
        
        self._save_scratchpad(scratchpad)
        return scratchpad

    def get_scratchpad(
        self,
        project_id: str,
        agent_id: str
    ) -> Optional[Scratchpad]:
        """Get a scratchpad.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            
        Returns:
            Scratchpad object or None if not found
        """
        filepath = self._get_filepath(project_id, agent_id)
        return self._load_scratchpad(filepath)

    def update_scratchpad(
        self,
        project_id: str,
        agent_id: str,
        update: ScratchpadUpdate
    ) -> Optional[Scratchpad]:
        """Update an existing scratchpad.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            update: Update data
            
        Returns:
            Updated Scratchpad object or None if not found
        """
        existing = self.get_scratchpad(project_id, agent_id)
        if not existing:
            return None
        
        # Update content and timestamp
        updated = Scratchpad(
            project_id=existing.project_id,
            agent_id=existing.agent_id,
            content=update.content,
            created_at=existing.created_at,
            updated_at=datetime.now()
        )
        
        self._save_scratchpad(updated)
        return updated

    def delete_scratchpad(
        self,
        project_id: str,
        agent_id: str
    ) -> bool:
        """Delete a scratchpad.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            
        Returns:
            True if deleted, False if not found
        """
        filepath = self._get_filepath(project_id, agent_id)
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            return True
        except OSError:
            return False

    def list_scratchpads(
        self,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Scratchpad]:
        """List scratchpads with optional filtering.
        
        Args:
            project_id: Optional project filter
            agent_id: Optional agent filter
            
        Returns:
            List of Scratchpad objects
        """
        scratchpads = []
        
        # Load all scratchpad files
        for filepath in self.data_path.glob("*.json"):
            scratchpad = self._load_scratchpad(filepath)
            if scratchpad is None:
                continue
            
            # Apply filters
            if project_id and scratchpad.project_id != project_id:
                continue
            if agent_id and scratchpad.agent_id != agent_id:
                continue
            
            scratchpads.append(scratchpad)
        
        return scratchpads

