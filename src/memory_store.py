"""Memory store implementation using ChromaDB."""

import os
import json
import uuid
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings

from src.models import Memory, MemoryCreate, MemoryUpdate, MemoryMetadata, SearchResult
from src.embeddings import EmbeddingProvider


class MemoryStore:
    """Memory store using ChromaDB for vector storage."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        data_path: Optional[str] = None
    ):
        """Initialize memory store.
        
        Args:
            embedding_provider: Embedding provider to use
            data_path: Path to store ChromaDB data (default: ~/.local/share/memalpha/chroma)
        """
        self.embedding_provider = embedding_provider
        
        if data_path is None:
            data_path = os.path.expanduser("~/.local/share/memalpha/chroma")
        
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.data_path)
        )

    def _get_collection_name(self, project_id: str, agent_id: str) -> str:
        """Generate collection name for a project-agent-embedding combination.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            
        Returns:
            Collection name string
        """
        # Sanitize IDs to be safe for collection names
        safe_project = re.sub(r'[^a-zA-Z0-9_-]', '_', project_id)
        safe_agent = re.sub(r'[^a-zA-Z0-9_-]', '_', agent_id)
        provider = self.embedding_provider.provider_name
        
        return f"p_{safe_project}_a_{safe_agent}_emb_{provider}"

    def _get_or_create_collection(self, project_id: str, agent_id: str):
        """Get or create a collection for the given project and agent.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            
        Returns:
            ChromaDB collection
        """
        collection_name = self._get_collection_name(project_id, agent_id)
        
        metadata = {
            "project_id": project_id,
            "agent_id": agent_id,
            "embedding_provider": self.embedding_provider.provider_name,
            "embedding_model": self.embedding_provider.model_name,
            "embedding_dimension": self.embedding_provider.dimension,
        }
        
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata
        )
        
        return collection

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize custom metadata to JSON string.
        
        Args:
            metadata: Custom metadata dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(metadata)

    def _deserialize_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Deserialize custom metadata from JSON string.
        
        Args:
            metadata_str: JSON string
            
        Returns:
            Metadata dictionary
        """
        if not metadata_str:
            return {}
        return json.loads(metadata_str)

    def store_memory(self, memory_create: MemoryCreate) -> Memory:
        """Store a new memory.
        
        Args:
            memory_create: Memory creation request
            
        Returns:
            Created Memory object
        """
        collection = self._get_or_create_collection(
            memory_create.project_id,
            memory_create.agent_id
        )
        
        # Generate unique ID
        memory_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self.embedding_provider.embed(memory_create.content)
        
        # Prepare metadata for ChromaDB
        now = datetime.now()
        chroma_metadata = {
            "project_id": memory_create.project_id,
            "agent_id": memory_create.agent_id,
            "custom_metadata": self._serialize_metadata(memory_create.metadata),
            "embedding_provider": self.embedding_provider.provider_name,
            "embedding_model": self.embedding_provider.model_name,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        # Store in ChromaDB
        collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[memory_create.content],
            metadatas=[chroma_metadata]
        )
        
        # Return Memory object
        return Memory(
            memory_id=memory_id,
            project_id=memory_create.project_id,
            agent_id=memory_create.agent_id,
            content=memory_create.content,
            metadata=memory_create.metadata,
            embedding_provider=self.embedding_provider.provider_name,
            embedding_model=self.embedding_provider.model_name,
            created_at=now,
            updated_at=now
        )

    def get_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_id: str
    ) -> Optional[Memory]:
        """Retrieve a memory by ID.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            memory_id: Memory identifier
            
        Returns:
            Memory object or None if not found
        """
        collection = self._get_or_create_collection(project_id, agent_id)
        
        result = collection.get(
            ids=[memory_id],
            include=["documents", "metadatas"]
        )
        
        if not result['ids']:
            return None
        
        metadata = result['metadatas'][0]
        return Memory(
            memory_id=result['ids'][0],
            project_id=metadata['project_id'],
            agent_id=metadata['agent_id'],
            content=result['documents'][0],
            metadata=self._deserialize_metadata(metadata.get('custom_metadata', '{}')),
            embedding_provider=metadata['embedding_provider'],
            embedding_model=metadata['embedding_model'],
            created_at=datetime.fromisoformat(metadata['created_at']),
            updated_at=datetime.fromisoformat(metadata['updated_at'])
        )

    def search_memories(
        self,
        project_id: str,
        agent_id: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search memories using semantic similarity.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        collection = self._get_or_create_collection(project_id, agent_id)
        
        # Generate query embedding
        query_embedding = self.embedding_provider.embed(query)
        
        # Prepare where clause for filters
        where = None
        if filters:
            # Convert custom metadata filters to ChromaDB format
            # This is a simplified implementation
            where = filters
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        if results['ids'][0]:
            for i, memory_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                # Convert distance to similarity score (1 - normalized distance)
                # ChromaDB uses L2 distance, we convert to 0-1 similarity
                similarity = 1.0 / (1.0 + distance)
                
                memory = Memory(
                    memory_id=memory_id,
                    project_id=metadata['project_id'],
                    agent_id=metadata['agent_id'],
                    content=results['documents'][0][i],
                    metadata=self._deserialize_metadata(metadata.get('custom_metadata', '{}')),
                    embedding_provider=metadata['embedding_provider'],
                    embedding_model=metadata['embedding_model'],
                    created_at=datetime.fromisoformat(metadata['created_at']),
                    updated_at=datetime.fromisoformat(metadata['updated_at'])
                )
                
                search_results.append(SearchResult(
                    memory=memory,
                    similarity_score=min(similarity, 1.0)  # Cap at 1.0
                ))
        
        return search_results

    def update_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_id: str,
        update: MemoryUpdate
    ) -> Optional[Memory]:
        """Update an existing memory.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            memory_id: Memory identifier
            update: Update data
            
        Returns:
            Updated Memory object or None if not found
        """
        # Get existing memory
        existing = self.get_memory(project_id, agent_id, memory_id)
        if not existing:
            return None
        
        collection = self._get_or_create_collection(project_id, agent_id)
        
        # Determine what to update
        new_content = update.content if update.content is not None else existing.content
        new_metadata = update.metadata if update.metadata is not None else existing.metadata
        
        # Prepare updated ChromaDB metadata
        now = datetime.now()
        chroma_metadata = {
            "project_id": project_id,
            "agent_id": agent_id,
            "custom_metadata": self._serialize_metadata(new_metadata),
            "embedding_provider": existing.embedding_provider,
            "embedding_model": existing.embedding_model,
            "created_at": existing.created_at.isoformat(),
            "updated_at": now.isoformat(),
        }
        
        # If content changed, re-embed
        if update.content is not None:
            new_embedding = self.embedding_provider.embed(new_content)
            collection.update(
                ids=[memory_id],
                embeddings=[new_embedding],
                documents=[new_content],
                metadatas=[chroma_metadata]
            )
        else:
            # Only metadata changed, no need to re-embed
            collection.update(
                ids=[memory_id],
                documents=[new_content],
                metadatas=[chroma_metadata]
            )
        
        return Memory(
            memory_id=memory_id,
            project_id=project_id,
            agent_id=agent_id,
            content=new_content,
            metadata=new_metadata,
            embedding_provider=existing.embedding_provider,
            embedding_model=existing.embedding_model,
            created_at=existing.created_at,
            updated_at=now
        )

    def delete_memory(
        self,
        project_id: str,
        agent_id: str,
        memory_id: str
    ) -> bool:
        """Delete a memory.
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            memory_id: Memory identifier
            
        Returns:
            True if deleted, False otherwise
        """
        collection = self._get_or_create_collection(project_id, agent_id)
        
        try:
            collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def list_memories(
        self,
        project_id: str,
        agent_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryMetadata]:
        """List memories (metadata only, no content).
        
        Args:
            project_id: Project identifier
            agent_id: Agent identifier
            limit: Maximum number of results
            offset: Offset for pagination
            filters: Optional metadata filters
            
        Returns:
            List of MemoryMetadata objects
        """
        collection = self._get_or_create_collection(project_id, agent_id)
        
        # Get all IDs and metadatas
        # ChromaDB doesn't have native pagination, so we handle it here
        result = collection.get(
            include=["metadatas"]
        )
        
        # Apply offset and limit
        ids = result['ids'][offset:offset + limit]
        metadatas_list = result['metadatas'][offset:offset + limit]
        
        # Convert to MemoryMetadata objects
        memory_metadatas = []
        for i, memory_id in enumerate(ids):
            metadata = metadatas_list[i]
            memory_metadatas.append(MemoryMetadata(
                memory_id=memory_id,
                project_id=metadata['project_id'],
                agent_id=metadata['agent_id'],
                metadata=self._deserialize_metadata(metadata.get('custom_metadata', '{}')),
                embedding_provider=metadata['embedding_provider'],
                embedding_model=metadata['embedding_model'],
                created_at=datetime.fromisoformat(metadata['created_at']),
                updated_at=datetime.fromisoformat(metadata['updated_at'])
            ))
        
        return memory_metadatas

