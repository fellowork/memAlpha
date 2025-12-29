"""Data models for memAlpha memory system."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MemoryCreate(BaseModel):
    """Model for creating a new memory."""
    
    project_id: str = Field(..., min_length=1, description="Project identifier")
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    content: str = Field(..., min_length=1, description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class MemoryUpdate(BaseModel):
    """Model for updating an existing memory."""
    
    content: Optional[str] = Field(None, min_length=1, description="Updated content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure content is not empty or whitespace only if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Content cannot be empty')
        return v


class Memory(BaseModel):
    """Complete memory object with all fields."""
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    memory_id: str = Field(..., description="Unique memory identifier")
    project_id: str = Field(..., description="Project identifier")
    agent_id: str = Field(..., description="Agent identifier")
    content: str = Field(..., description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    embedding_provider: str = Field(..., description="Embedding provider used (local/openai)")
    embedding_model: str = Field(..., description="Specific embedding model used")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class MemoryMetadata(BaseModel):
    """Memory metadata without content (for list operations)."""
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    memory_id: str = Field(..., description="Unique memory identifier")
    project_id: str = Field(..., description="Project identifier")
    agent_id: str = Field(..., description="Agent identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    embedding_provider: str = Field(..., description="Embedding provider used")
    embedding_model: str = Field(..., description="Specific embedding model used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SearchResult(BaseModel):
    """Search result with memory and similarity score."""
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    memory: Memory = Field(..., description="Memory object")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")

