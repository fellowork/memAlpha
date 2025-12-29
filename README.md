# memAlpha 🧠

A local memory system for AI coding agents with MCP (Model Context Protocol) server support.

## Features

- 🔒 **Agent Isolation**: Each agent's memories are completely isolated by project and agent ID
- 🏠 **100% Local**: Runs entirely on your machine with local vector store and embeddings
- 🚀 **Zero Installation**: Run directly from GitHub with `uv` - no manual setup needed
- 🔍 **Semantic Search**: Find memories using natural language queries
- 🎯 **Flexible Schema**: Agents structure their memories however they want
- 🔌 **OpenAI Compatible**: Optional OpenAI embeddings API support
- 🧪 **Well Tested**: Comprehensive unit tests and BDD scenarios

## Quick Start

### Run from GitHub (Recommended)

Add to your MCP client configuration (e.g., Claude Desktop, Cursor):

```json
{
  "memAlpha": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/yourusername/memAlpha", "memalpha"]
  }
}
```

That's it! The first run will download dependencies automatically.

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/memAlpha.git
cd memAlpha

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run BDD tests
uv run pytest tests/test_bdd_steps.py -v

# Start the MCP server
uv run memalpha
```

## Configuration

memAlpha uses environment variables for configuration:

### Embedding Providers

**Local Embeddings (Default)**

No configuration needed! Uses `sentence-transformers` with `all-MiniLM-L6-v2` model.

- ~80MB model download on first use
- Runs efficiently on CPU
- 384-dimensional embeddings
- Completely private and offline

**OpenAI Embeddings**

```bash
export MEMALPHA_EMBEDDING_PROVIDER=openai
export MEMALPHA_OPENAI_API_KEY=sk-...
export MEMALPHA_OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
export MEMALPHA_OPENAI_MODEL=text-embedding-3-small        # Optional
```

MCP configuration with environment variables:

```json
{
  "memAlpha": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/yourusername/memAlpha", "memalpha"],
    "env": {
      "MEMALPHA_EMBEDDING_PROVIDER": "openai",
      "MEMALPHA_OPENAI_API_KEY": "sk-..."
    }
  }
}
```

### Data Storage

By default, data is stored at:
- **Linux/Mac**: `~/.local/share/memalpha/`
- **Windows**: `%APPDATA%/memalpha/`

Structure:
```
~/.local/share/memalpha/
├── chroma/          # ChromaDB vector store
└── models/          # Cached embedding models (local only)
```

## MCP Tools

### `store_memory`

Store a new memory for an agent.

**Parameters:**
- `project_id` (string, required): Project identifier
- `agent_id` (string, required): Agent identifier
- `content` (string, required): Memory content
- `metadata` (object, optional): Custom metadata

**Example:**
```json
{
  "project_id": "my-web-app",
  "agent_id": "cursor-assistant",
  "content": "User prefers TypeScript over JavaScript for type safety",
  "metadata": {
    "category": "preference",
    "tags": ["language", "typescript"],
    "importance": 8
  }
}
```

### `search_memories`

Search for memories using semantic similarity.

**Parameters:**
- `project_id` (string, required): Project identifier
- `agent_id` (string, required): Agent identifier
- `query` (string, required): Search query
- `limit` (integer, optional): Max results (default: 10)
- `filters` (object, optional): Metadata filters

**Example:**
```json
{
  "project_id": "my-web-app",
  "agent_id": "cursor-assistant",
  "query": "what language does the user prefer",
  "limit": 5
}
```

### `get_memory`

Retrieve a specific memory by ID.

**Parameters:**
- `project_id` (string, required)
- `agent_id` (string, required)
- `memory_id` (string, required)

### `update_memory`

Update an existing memory's content and/or metadata.

**Parameters:**
- `project_id` (string, required)
- `agent_id` (string, required)
- `memory_id` (string, required)
- `content` (string, optional): New content
- `metadata` (object, optional): New metadata

### `delete_memory`

Delete a memory permanently.

**Parameters:**
- `project_id` (string, required)
- `agent_id` (string, required)
- `memory_id` (string, required)

### `list_memories`

List all memories (metadata only) with pagination.

**Parameters:**
- `project_id` (string, required)
- `agent_id` (string, required)
- `limit` (integer, optional): Max results (default: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

### `get_memory_suggestions`

Get suggestions for memory structure and best practices.

**Parameters:** None

**Returns:** Suggested categories, metadata fields, examples, and tips.

## Memory Isolation

Each agent's memories are completely isolated:

```
Collection naming: p_{project_id}_a_{agent_id}_emb_{provider}

Examples:
- p_myapp_a_cursor_emb_local      # Local embeddings
- p_myapp_a_cursor_emb_openai     # OpenAI embeddings
- p_blog_a_assistant_emb_local    # Different project
```

### Key Points:

1. **Same agent, different projects** = Different memory spaces
2. **Different agents, same project** = Different memory spaces
3. **Same agent+project, different embeddings** = Different memory spaces

Switching embedding providers creates a new memory space. Your old memories remain accessible if you switch back.

## Architecture

```
┌─────────────────┐
│   MCP Client    │  (Claude Desktop, Cursor, etc.)
└────────┬────────┘
         │ stdio
┌────────▼────────┐
│   MCP Server    │  (memAlpha)
└────────┬────────┘
         │
    ┌────▼─────┬─────────────┐
    │          │             │
┌───▼───┐ ┌───▼────┐ ┌─────▼─────┐
│Memory │ │Embedding│ │  ChromaDB │
│Store  │ │Provider │ │  (Vector  │
│       │ │         │ │   Store)  │
└───────┘ └─────┬───┘ └───────────┘
                │
        ┌───────▼────────┐
        │                │
   ┌────▼─────┐   ┌─────▼──────┐
   │  Local   │   │   OpenAI   │
   │sentence- │   │  Embedding │
   │transform.│   │    API     │
   └──────────┘   └────────────┘
```

## Development

### Project Structure

```
memAlpha/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── memory_store.py    # ChromaDB wrapper
│   ├── embeddings.py      # Embedding providers
│   └── models.py          # Pydantic data models
├── tests/
│   ├── test_models.py
│   ├── test_embeddings.py
│   ├── test_memory_store.py
│   ├── test_bdd_steps.py
│   └── features/
│       ├── agent_memory_management.feature
│       └── team_collaboration.feature
├── pyproject.toml
├── README.md
└── .gitignore
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Only unit tests
uv run pytest tests/test_*.py -v

# Only BDD tests
uv run pytest tests/test_bdd_steps.py -v

# Specific test file
uv run pytest tests/test_embeddings.py -v
```

### Code Quality

```bash
# Type checking (if using mypy)
uv run mypy src/

# Linting (if using ruff)
uv run ruff check src/

# Formatting (if using black)
uv run black src/ tests/
```

## Use Cases

### Solo Agent

```python
# Agent stores learnings
store_memory(
  project_id="my-saas",
  agent_id="cursor",
  content="User wants dark mode toggle in settings",
  metadata={"category": "feature-request", "priority": "high"}
)

# Later, agent searches
search_memories(
  project_id="my-saas",
  agent_id="cursor",
  query="what features did user request"
)
```

### Team of Agents

```python
# Backend specialist
store_memory(
  project_id="crm-app",
  agent_id="backend-specialist",
  content="Using PostgreSQL with read replicas for scaling"
)

# Frontend specialist (different agent, same project)
store_memory(
  project_id="crm-app",
  agent_id="frontend-specialist",
  content="Using Next.js 14 with App Router"
)

# Each agent only sees their own memories
```

### Multi-Project Agent

```python
# Working on project A
store_memory(
  project_id="ecommerce",
  agent_id="fullstack-dev",
  content="Payment integration uses Stripe"
)

# Switch to project B
store_memory(
  project_id="blog-platform",
  agent_id="fullstack-dev",
  content="Content stored as Markdown files"
)

# Memories are isolated by project
```

## Memory Best Practices

From `get_memory_suggestions` tool:

### Suggested Categories

- `fact` - Factual information about the project
- `procedure` - How to do something
- `preference` - User/team preferences
- `context` - Project context and background
- `decision` - Important decisions made
- `issue` - Problems and their solutions

### Recommended Metadata Fields

- `tags` - List of tags for categorization
- `category` - One of the suggested categories
- `importance` - Integer 0-10 indicating importance
- `source` - Where this information came from
- `related_to` - IDs of related memories

### Tips

1. Store specific, actionable information
2. Use consistent tagging across related memories
3. Mark important decisions with high importance scores
4. Include context in the content, not just facts
5. Update memories when information changes
6. Use descriptive content for better semantic search

## Troubleshooting

### Model Download Issues

If local model download fails:
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### ChromaDB Persistence Issues

If you encounter ChromaDB errors, try clearing the data:
```bash
rm -rf ~/.local/share/memalpha/chroma
```

### OpenAI API Errors

Check your API key and base URL:
```bash
echo $MEMALPHA_OPENAI_API_KEY
echo $MEMALPHA_OPENAI_BASE_URL
```

## Performance

- **Local embeddings**: ~50ms per embedding on CPU
- **Storage**: ~1KB per memory (varies with content length)
- **Search**: Sub-second for thousands of memories
- **Scalability**: Tested with 10,000+ memories per agent

## Contributing

Contributions welcome! Please:

1. Write tests for new features
2. Follow TDD approach
3. Add BDD scenarios for user-facing features
4. Update documentation

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [MCP](https://github.com/modelcontextprotocol) - Model Context Protocol
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [sentence-transformers](https://www.sbert.net/) - Local embeddings
- [Pydantic](https://pydantic.dev/) - Data validation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

