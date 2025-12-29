# memAlpha 🧠

**Local memory system for AI coding agents** with semantic search and scratchpad functionality.

Give your AI agents the ability to remember facts, search their knowledge, and take temporary notes - all running 100% locally with optional cloud embeddings.

---

## ✨ What is memAlpha?

memAlpha provides AI agents with two types of memory:

### **Memories** 📚
Long-term knowledge with semantic search
- Store important facts, preferences, and decisions
- Search by meaning, not keywords
- Many memories per agent

### **Scratchpad** 📝
Temporary notepad for quick notes
- One scratchpad per agent per project
- Perfect for TODOs, session notes, drafts
- Simple read/write, no search needed

---

## 🚀 Quick Start

### Installation

No installation needed! Run directly from GitHub:

```json
{
  "memAlpha": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/fellowork/memAlpha", "memalpha"]
  }
}
```

Add this to your MCP client configuration (Claude Desktop, Cursor, etc.) and you're ready!

### First Use

```python
# Store a memory
store_memory(
    project_id="my-app",
    agent_id="cursor-assistant",
    content="User prefers TypeScript over JavaScript",
    metadata={"category": "preference"}
)

# Search your memories
search_memories(
    project_id="my-app",
    agent_id="cursor-assistant",
    query="what language does the user prefer"
)

# Use scratchpad for session notes
create_scratchpad(
    project_id="my-app",
    agent_id="cursor-assistant",
    content="TODO: Fix auth bug, Add dark mode"
)
```

---

## 🛠️ Available Tools

### Memory Tools

| Tool | Purpose |
|------|---------|
| `store_memory` | Save important information for long-term |
| `search_memories` | Find relevant memories using semantic search |
| `get_memory` | Retrieve a specific memory by ID |
| `update_memory` | Update existing memory content or metadata |
| `delete_memory` | Remove a memory permanently |
| `list_memories` | Browse all memories with pagination |
| `get_memory_suggestions` | Get tips on structuring memories |

### Scratchpad Tools

| Tool | Purpose |
|------|---------|
| `create_scratchpad` | Create a notepad for temporary notes |
| `get_scratchpad` | Read current scratchpad content |
| `update_scratchpad` | Update your notes |
| `delete_scratchpad` | Clear the scratchpad |

---

## 💡 Key Concepts

### When to Use What

**Use Memories for:**
- ✅ Facts you want to remember long-term
- ✅ User preferences and requirements  
- ✅ Important decisions and architecture notes
- ✅ Information you want to search later

**Use Scratchpad for:**
- ✅ Current session TODOs
- ✅ Debugging notes and observations
- ✅ Draft text before committing
- ✅ Temporary tracking during work

### Agent Isolation

Each agent gets **completely separate memory** per project:
- `project_id="app-a"` + `agent_id="cursor"` = separate from
- `project_id="app-b"` + `agent_id="cursor"`

No cross-agent or cross-project memory access.

### Memories vs Scratchpad

| Feature | Memories | Scratchpad |
|---------|----------|------------|
| **Quantity** | Many | One per agent/project |
| **Searchable** | ✅ Yes (semantic) | ❌ No |
| **Storage** | Vector database | Simple JSON file |
| **Best for** | Long-term knowledge | Temporary notes |
| **Updates** | Create new entries | Update existing |

---

## 📖 Usage Examples

### Example 1: Remembering User Preferences

```python
# Store the preference
store_memory(
    project_id="webstore",
    agent_id="dev-agent",
    content="User wants email notifications for order updates",
    metadata={
        "category": "requirement",
        "tags": ["email", "notifications"],
        "importance": 8
    }
)

# Later, search for it
results = search_memories(
    project_id="webstore",
    agent_id="dev-agent",
    query="how should we notify users about orders"
)
# Returns relevant memories about notifications
```

### Example 2: Session Work with Scratchpad

```python
# Start of coding session
create_scratchpad(
    project_id="api-project",
    agent_id="cursor",
    content="""
    SESSION GOALS:
    - Fix payment validation bug
    - Add email confirmation
    - Update API docs
    """
)

# During work, update progress
update_scratchpad(
    project_id="api-project",
    agent_id="cursor",
    content="""
    SESSION GOALS:
    ✓ Fixed payment validation bug
    ✓ Added email confirmation
    - Update API docs
    
    NOTES:
    - Payment bug was in Stripe webhook handler
    - Used nodemailer for email
    """
)

# Important learnings → store as memory
store_memory(
    project_id="api-project",
    agent_id="cursor",
    content="Payment validation: Stripe webhooks require raw body parser",
    metadata={"category": "procedure", "importance": 9}
)
```

### Example 3: Team of Agents

```python
# Backend agent stores their knowledge
store_memory(
    project_id="saas-app",
    agent_id="backend-specialist",
    content="Using PostgreSQL 15 with read replicas for scaling"
)

# Frontend agent stores separately
store_memory(
    project_id="saas-app",
    agent_id="frontend-specialist",
    content="Using Next.js 14 with App Router"
)

# Each agent only sees their own memories
# Complete isolation between agents
```

---

## ⚙️ Configuration

### Local Embeddings (Default)

**No configuration needed!** Works out of the box:
- Uses `sentence-transformers` with `all-MiniLM-L6-v2`
- Runs on CPU (no GPU needed)
- ~80MB model download on first use
- 100% private and offline

### OpenAI Embeddings (Optional)

For higher quality or when you don't want to run local models:

```json
{
  "memAlpha": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/fellowork/memAlpha", "memalpha"],
    "env": {
      "MEMALPHA_EMBEDDING_PROVIDER": "openai",
      "MEMALPHA_OPENAI_API_KEY": "sk-your-key-here"
    }
  }
}
```

**Optional settings:**
```bash
MEMALPHA_OPENAI_BASE_URL=https://api.openai.com/v1  # Custom endpoint
MEMALPHA_OPENAI_MODEL=text-embedding-3-small        # Different model
```

### Data Storage

All data stored locally at:
```
~/.local/share/memalpha/
├── chroma/          # Vector database (memories)
├── scratchpads/     # JSON files (scratchpads)
└── models/          # Cached embedding models
```

---

## 🎯 Best Practices

### Memory Guidelines

1. **Be specific** - Store actionable information
   - ❌ "User likes dark themes"
   - ✅ "User prefers dark mode with high contrast (WCAG AAA)"

2. **Use consistent tags** - Makes filtering easier
   ```python
   metadata={"category": "preference", "tags": ["ui", "accessibility"]}
   ```

3. **Mark importance** - Helps prioritize
   ```python
   metadata={"importance": 9}  # 0-10 scale
   ```

4. **Update, don't duplicate** - Keep knowledge clean
   ```python
   update_memory(...)  # Instead of creating duplicates
   ```

### Scratchpad Workflow

```
1. Start session → create_scratchpad() with goals
2. Work & update → update_scratchpad() with progress
3. Important insights → store_memory() for long-term
4. End session → delete_scratchpad() to clean up
```

### Suggested Memory Categories

From `get_memory_suggestions`:
- `fact` - Factual information about the project
- `procedure` - How to do something
- `preference` - User/team preferences
- `context` - Project context and background
- `decision` - Important decisions made
- `issue` - Problems and their solutions

---

## 🔒 Privacy & Security

- ✅ **100% local by default** - No external API calls
- ✅ **All data on your machine** - Nothing leaves your computer
- ✅ **No telemetry** - We don't track anything
- ✅ **Optional OpenAI** - You control when to use external APIs
- ✅ **Open source** - Audit the code yourself

---

## 📊 Performance

- **Local embeddings**: ~50ms per text on CPU
- **Storage**: ~1KB per memory (varies with content)
- **Search**: Sub-second for 1000s of memories
- **Tested scale**: 10,000+ memories per agent

---

## 🧪 Development & Testing

### Running Tests Locally

```bash
# Clone repository
git clone https://github.com/fellowork/memAlpha.git
cd memAlpha

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

- **64 unit tests** - All passing ✅
- **95%+ coverage** on core modules
- **TDD approach** - Tests written first
- **BDD scenarios** - Real-world use cases

### Project Structure

```
memAlpha/
├── src/
│   ├── models.py          # Pydantic data models
│   ├── embeddings.py      # Local & OpenAI providers
│   ├── memory_store.py    # ChromaDB wrapper
│   ├── scratchpad_store.py # JSON file storage
│   └── server.py          # MCP server
├── tests/
│   ├── test_models.py
│   ├── test_embeddings.py
│   ├── test_memory_store.py
│   ├── test_scratchpad.py
│   └── features/          # BDD scenarios
├── .github/workflows/     # CI/CD pipelines
└── pyproject.toml
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Write tests for new features (TDD approach)
2. Maintain test coverage above 90%
3. Update documentation
4. Follow existing code style

See `.github/SETUP.md` for development workflow.

---

## 📄 License

MIT License - Copyright (c) 2025 fellowork GmbH

Free to use for any purpose, including commercial. See LICENSE file for details.

---

## 🔗 Links

- **Repository**: https://github.com/fellowork/memAlpha
- **Issues**: https://github.com/fellowork/memAlpha/issues
- **CI/CD Setup**: See `.github/SETUP.md`
- **LLM-optimized docs**: See `llm.txt`

---

## 💬 Questions?

- Check `llm.txt` for AI-optimized documentation
- See `.github/SETUP.md` for detailed setup
- Open an issue on GitHub

---

**Built with ❤️ using TDD • 64 Tests • 95%+ Coverage**
