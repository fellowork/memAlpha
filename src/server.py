"""MCP server for memAlpha memory system."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.memory_store import MemoryStore
from src.embeddings import get_embedding_provider
from src.models import MemoryCreate, MemoryUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memalpha")


# Initialize the MCP server
app = Server("memalpha")

# Global memory store (initialized on startup)
memory_store: Optional[MemoryStore] = None


def get_memory_suggestions() -> Dict[str, Any]:
    """Get suggestions for memory structure and best practices.
    
    Returns:
        Dictionary with suggestions and examples
    """
    return {
        "suggested_categories": [
            "fact",          # Factual information about the project
            "procedure",     # How to do something
            "preference",    # User/team preferences
            "context",       # Project context and background
            "decision",      # Important decisions made
            "issue",         # Problems and their solutions
        ],
        "metadata_fields": {
            "tags": "List of tags for categorization (e.g., ['backend', 'api'])",
            "category": "One of the suggested categories above",
            "importance": "Integer 0-10 indicating importance",
            "source": "Where this information came from",
            "related_to": "IDs of related memories",
        },
        "examples": [
            {
                "content": "User prefers TypeScript over JavaScript for type safety",
                "metadata": {
                    "category": "preference",
                    "tags": ["language", "typescript"],
                    "importance": 8
                }
            },
            {
                "content": "Authentication implemented using JWT with 7-day expiry",
                "metadata": {
                    "category": "fact",
                    "tags": ["security", "auth", "jwt"],
                    "importance": 9
                }
            },
            {
                "content": "To deploy: run 'yarn build' then 'yarn deploy:prod'",
                "metadata": {
                    "category": "procedure",
                    "tags": ["deployment", "commands"],
                    "importance": 7
                }
            }
        ],
        "best_practices": [
            "Store specific, actionable information",
            "Use consistent tagging across related memories",
            "Mark important decisions with high importance scores",
            "Include context in the content, not just facts",
            "Update memories when information changes rather than creating duplicates",
            "Use descriptive content that will match semantic searches"
        ]
    }


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="store_memory",
            description=(
                "Store a new memory for an agent in a project. "
                "Memories are automatically embedded for semantic search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Memory content - be specific and descriptive (required)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional custom metadata (tags, category, importance, etc.)",
                        "default": {}
                    }
                },
                "required": ["project_id", "agent_id", "content"]
            }
        ),
        Tool(
            name="search_memories",
            description=(
                "Search for memories using semantic similarity. "
                "Returns memories ranked by relevance to the query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (required)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional metadata filters",
                        "default": {}
                    }
                },
                "required": ["project_id", "agent_id", "query"]
            }
        ),
        Tool(
            name="get_memory",
            description="Retrieve a specific memory by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory identifier (required)"
                    }
                },
                "required": ["project_id", "agent_id", "memory_id"]
            }
        ),
        Tool(
            name="update_memory",
            description=(
                "Update an existing memory's content and/or metadata. "
                "If content is updated, the embedding is automatically regenerated."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory identifier (required)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Updated content (optional)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Updated metadata (optional)"
                    }
                },
                "required": ["project_id", "agent_id", "memory_id"]
            }
        ),
        Tool(
            name="delete_memory",
            description="Delete a memory permanently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "Memory identifier (required)"
                    }
                },
                "required": ["project_id", "agent_id", "memory_id"]
            }
        ),
        Tool(
            name="list_memories",
            description=(
                "List memories (metadata only, without full content) with pagination. "
                "Useful for browsing available memories."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier (required)"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier (required)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)",
                        "default": 100
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination (default: 0)",
                        "default": 0
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional metadata filters",
                        "default": {}
                    }
                },
                "required": ["project_id", "agent_id"]
            }
        ),
        Tool(
            name="get_memory_suggestions",
            description=(
                "Get suggestions and best practices for structuring memories. "
                "Returns suggested categories, metadata fields, examples, and tips."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    global memory_store
    
    if memory_store is None:
        return [TextContent(
            type="text",
            text="Error: Memory store not initialized"
        )]
    
    try:
        if name == "store_memory":
            memory_create = MemoryCreate(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                content=arguments["content"],
                metadata=arguments.get("metadata", {})
            )
            memory = memory_store.store_memory(memory_create)
            return [TextContent(
                type="text",
                text=f"Memory stored successfully!\n\n"
                     f"Memory ID: {memory.memory_id}\n"
                     f"Content: {memory.content}\n"
                     f"Metadata: {memory.metadata}\n"
                     f"Embedding: {memory.embedding_provider}/{memory.embedding_model}"
            )]
        
        elif name == "search_memories":
            results = memory_store.search_memories(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                query=arguments["query"],
                limit=arguments.get("limit", 10),
                filters=arguments.get("filters")
            )
            
            if not results:
                return [TextContent(
                    type="text",
                    text="No memories found matching your query."
                )]
            
            response = f"Found {len(results)} relevant memories:\n\n"
            for i, result in enumerate(results, 1):
                response += (
                    f"{i}. [Score: {result.similarity_score:.3f}] "
                    f"(ID: {result.memory.memory_id})\n"
                    f"   {result.memory.content}\n"
                    f"   Metadata: {result.memory.metadata}\n\n"
                )
            return [TextContent(type="text", text=response)]
        
        elif name == "get_memory":
            memory = memory_store.get_memory(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                memory_id=arguments["memory_id"]
            )
            
            if not memory:
                return [TextContent(
                    type="text",
                    text=f"Memory with ID '{arguments['memory_id']}' not found."
                )]
            
            return [TextContent(
                type="text",
                text=f"Memory ID: {memory.memory_id}\n"
                     f"Content: {memory.content}\n"
                     f"Metadata: {memory.metadata}\n"
                     f"Created: {memory.created_at}\n"
                     f"Updated: {memory.updated_at}\n"
                     f"Embedding: {memory.embedding_provider}/{memory.embedding_model}"
            )]
        
        elif name == "update_memory":
            update = MemoryUpdate(
                content=arguments.get("content"),
                metadata=arguments.get("metadata")
            )
            
            memory = memory_store.update_memory(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                memory_id=arguments["memory_id"],
                update=update
            )
            
            if not memory:
                return [TextContent(
                    type="text",
                    text=f"Memory with ID '{arguments['memory_id']}' not found."
                )]
            
            return [TextContent(
                type="text",
                text=f"Memory updated successfully!\n\n"
                     f"Memory ID: {memory.memory_id}\n"
                     f"Content: {memory.content}\n"
                     f"Metadata: {memory.metadata}\n"
                     f"Updated: {memory.updated_at}"
            )]
        
        elif name == "delete_memory":
            success = memory_store.delete_memory(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                memory_id=arguments["memory_id"]
            )
            
            if success:
                return [TextContent(
                    type="text",
                    text=f"Memory '{arguments['memory_id']}' deleted successfully."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to delete memory '{arguments['memory_id']}'."
                )]
        
        elif name == "list_memories":
            metadatas = memory_store.list_memories(
                project_id=arguments["project_id"],
                agent_id=arguments["agent_id"],
                limit=arguments.get("limit", 100),
                offset=arguments.get("offset", 0),
                filters=arguments.get("filters")
            )
            
            if not metadatas:
                return [TextContent(
                    type="text",
                    text="No memories found."
                )]
            
            response = f"Found {len(metadatas)} memories:\n\n"
            for metadata in metadatas:
                response += (
                    f"- ID: {metadata.memory_id}\n"
                    f"  Metadata: {metadata.metadata}\n"
                    f"  Created: {metadata.created_at}\n"
                    f"  Updated: {metadata.updated_at}\n\n"
                )
            return [TextContent(type="text", text=response)]
        
        elif name == "get_memory_suggestions":
            suggestions = get_memory_suggestions()
            
            response = "Memory Structure Suggestions\n" + "="*50 + "\n\n"
            
            response += "Suggested Categories:\n"
            for cat in suggestions["suggested_categories"]:
                response += f"  - {cat}\n"
            
            response += "\nRecommended Metadata Fields:\n"
            for field, desc in suggestions["metadata_fields"].items():
                response += f"  - {field}: {desc}\n"
            
            response += "\nExamples:\n"
            for i, example in enumerate(suggestions["examples"], 1):
                response += f"\n{i}. Content: {example['content']}\n"
                response += f"   Metadata: {example['metadata']}\n"
            
            response += "\nBest Practices:\n"
            for tip in suggestions["best_practices"]:
                response += f"  - {tip}\n"
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    global memory_store
    
    # Initialize embedding provider and memory store
    logger.info("Initializing memAlpha...")
    try:
        embedding_provider = get_embedding_provider()
        logger.info(f"Using embedding provider: {embedding_provider.provider_name} "
                   f"({embedding_provider.model_name})")
        
        memory_store = MemoryStore(embedding_provider=embedding_provider)
        logger.info(f"Memory store initialized at: {memory_store.data_path}")
    except Exception as e:
        logger.error(f"Failed to initialize: {str(e)}")
        raise
    
    # Run the server
    logger.info("Starting MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Entry point for command-line execution."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

