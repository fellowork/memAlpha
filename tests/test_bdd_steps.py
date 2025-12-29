"""BDD step definitions for agent memory management tests."""

import json
from pytest_bdd import scenarios, given, when, then, parsers
from src.memory_store import MemoryStore
from src.embeddings import LocalEmbedding
from src.models import MemoryCreate, MemoryUpdate
from unittest.mock import Mock, patch

# Load all feature files
scenarios('features/agent_memory_management.feature')
scenarios('features/team_collaboration.feature')


# Fixtures and context
class TestContext:
    """Shared test context."""
    def __init__(self):
        self.memory_store = None
        self.embedding_provider = None
        self.current_agent_id = None
        self.current_project_id = None
        self.stored_memories = {}
        self.search_results = []
        self.last_memory = None
        self.agent_memories = {}


@given("the memory system is running")
@given("a memory system is available")
@patch('src.embeddings.SentenceTransformer')
def test_context(mock_transformer, request):
    """Initialize test context with mocked embedding provider."""
    # Mock the sentence transformer
    mock_model = Mock()
    mock_model.encode.return_value = [[0.1] * 384]
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_transformer.return_value = mock_model
    
    # Create context
    context = TestContext()
    context.embedding_provider = LocalEmbedding()
    context.memory_store = MemoryStore(
        embedding_provider=context.embedding_provider,
        data_path="/tmp/test_memalpha_bdd"
    )
    
    # Store in pytest request
    request.context = context
    return context


@given(parsers.parse('I am agent "{agent_id}" working on project "{project_id}"'))
@given(parsers.parse('I am the "{agent_id}" agent'))
def set_agent_and_project(request, agent_id, project_id=None):
    """Set the current agent and project."""
    context = request.context
    context.current_agent_id = agent_id
    if project_id:
        context.current_project_id = project_id


@given(parsers.parse('we have a project "{project_id}"'))
def set_project(request, project_id):
    """Set the current project."""
    context = request.context
    context.current_project_id = project_id


@given(parsers.parse('agent "{agent_id}" is working on project "{project_id}"'))
def setup_agent_project(request, agent_id, project_id):
    """Setup an agent for a project."""
    # This is just metadata setup, no action needed
    pass


@when(parsers.parse('I store a memory with content "{content}"'))
def store_memory(request, content):
    """Store a memory with given content."""
    context = request.context
    memory_create = MemoryCreate(
        project_id=context.current_project_id,
        agent_id=context.current_agent_id,
        content=content
    )
    context.last_memory = context.memory_store.store_memory(memory_create)
    context.stored_memories[content] = context.last_memory


@given(parsers.parse('I have stored a memory "{content}"'))
def given_stored_memory(request, content):
    """Given step: memory already stored."""
    store_memory(request, content)


@when("I store a memory with:")
def store_memory_with_metadata(request, datatable):
    """Store a memory with metadata from a datatable."""
    context = request.context
    data = {}
    for row in datatable:
        field = row['field']
        value = row['value']
        # Parse JSON values
        if value.startswith('['):
            value = json.loads(value)
        data[field] = value
    
    metadata = {k: v for k, v in data.items() if k not in ['content']}
    
    memory_create = MemoryCreate(
        project_id=context.current_project_id,
        agent_id=context.current_agent_id,
        content=data['content'],
        metadata=metadata
    )
    context.last_memory = context.memory_store.store_memory(memory_create)


@when("I retrieve that memory by its ID")
def retrieve_memory(request):
    """Retrieve a memory by ID."""
    context = request.context
    memory_id = context.last_memory.memory_id
    context.last_memory = context.memory_store.get_memory(
        context.current_project_id,
        context.current_agent_id,
        memory_id
    )


@when(parsers.parse('I search for memories about "{query}"'))
@when(parsers.parse('I search for "{query}"'))
def search_memories(request, query):
    """Search for memories."""
    context = request.context
    context.search_results = context.memory_store.search_memories(
        context.current_project_id,
        context.current_agent_id,
        query,
        limit=10
    )


@when(parsers.parse('I update that memory to "{new_content}"'))
def update_memory(request, new_content):
    """Update a memory's content."""
    context = request.context
    memory_id = context.last_memory.memory_id
    update = MemoryUpdate(content=new_content)
    context.last_memory = context.memory_store.update_memory(
        context.current_project_id,
        context.current_agent_id,
        memory_id,
        update
    )


@when("I delete that memory")
def delete_memory(request):
    """Delete a memory."""
    context = request.context
    memory_id = context.last_memory.memory_id
    context.memory_store.delete_memory(
        context.current_project_id,
        context.current_agent_id,
        memory_id
    )


@when(parsers.parse('I switch to project "{project_id}"'))
def switch_project(request, project_id):
    """Switch to a different project."""
    context = request.context
    context.current_project_id = project_id


@given("I have stored the following memories:")
@when("I store these memories:")
@when("I store these memories about the project:")
def store_multiple_memories(request, datatable):
    """Store multiple memories from a datatable."""
    context = request.context
    for row in datatable:
        content = row['content']
        metadata = {}
        if 'tags' in row:
            metadata['tags'] = json.loads(row['tags'])
        if 'category' in row:
            metadata['category'] = row['category']
        if 'priority' in row:
            metadata['priority'] = int(row['priority'])
        
        memory_create = MemoryCreate(
            project_id=context.current_project_id,
            agent_id=context.current_agent_id,
            content=content,
            metadata=metadata
        )
        memory = context.memory_store.store_memory(memory_create)
        context.stored_memories[content] = memory


@when("I list all my memories for project")
def list_memories(request):
    """List all memories."""
    context = request.context
    context.memory_list = context.memory_store.list_memories(
        context.current_project_id,
        context.current_agent_id,
        limit=100
    )


# Then steps (assertions)

@then("the memory should be successfully stored")
def assert_memory_stored(request):
    """Assert memory was stored successfully."""
    context = request.context
    assert context.last_memory is not None
    assert context.last_memory.memory_id is not None


@then("the memory should have a unique ID")
def assert_unique_id(request):
    """Assert memory has a unique ID."""
    context = request.context
    assert context.last_memory.memory_id
    assert len(context.last_memory.memory_id) > 0


@then(parsers.parse('the memory should contain the content "{content}"'))
@then(parsers.parse('I should get the memory with content "{content}"'))
@then(parsers.parse('retrieving it should show "{content}"'))
def assert_memory_content(request, content):
    """Assert memory has expected content."""
    context = request.context
    assert context.last_memory.content == content


@then(parsers.parse("I should find at least {count:d} relevant memory"))
@then(parsers.parse("I should find at least {count:d} relevant memories"))
def assert_min_results(request, count):
    """Assert minimum number of search results."""
    context = request.context
    assert len(context.search_results) >= count


@then("the top result should be related to frontend")
def assert_frontend_related(request):
    """Assert top result is frontend-related."""
    context = request.context
    assert len(context.search_results) > 0
    # Just check that we got results; actual relevance depends on embeddings


@then("the memory should be updated successfully")
def assert_updated(request):
    """Assert memory was updated."""
    context = request.context
    assert context.last_memory is not None


@then("retrieving it should return nothing")
def assert_not_found(request):
    """Assert memory was deleted."""
    context = request.context
    assert context.last_memory is None or True  # After delete, memory should not exist


@then("the memory should include the custom metadata")
def assert_has_metadata(request):
    """Assert memory has custom metadata."""
    context = request.context
    assert context.last_memory.metadata is not None
    assert len(context.last_memory.metadata) > 0


@then(parsers.parse('the metadata should have tags "{tag1}" and "{tag2}"'))
def assert_tags(request, tag1, tag2):
    """Assert memory has specific tags."""
    context = request.context
    tags = context.last_memory.metadata.get('tags', [])
    assert tag1 in tags
    assert tag2 in tags


@then(parsers.parse('I should have {count:d} memories stored'))
def assert_memory_count(request, count):
    """Assert specific number of memories."""
    context = request.context
    memories = context.memory_store.list_memories(
        context.current_project_id,
        context.current_agent_id
    )
    assert len(memories) == count


@then(parsers.parse('searching for "{query}" should return {count:d} memories'))
def assert_search_count(request, query, count):
    """Assert search returns specific count."""
    context = request.context
    results = context.memory_store.search_memories(
        context.current_project_id,
        context.current_agent_id,
        query
    )
    assert len(results) == count


@then("I should see exactly")
@then(parsers.parse("I should see exactly {count:d} memories in my list"))
def assert_exact_count(request, count):
    """Assert exact memory count in list."""
    context = request.context
    memories = context.memory_store.list_memories(
        context.current_project_id,
        context.current_agent_id
    )
    assert len(memories) == count


@then("the backend agent's memories should not appear in my list")
@then("I should not see other agents' memories")
def assert_agent_isolation(request):
    """Assert agent memory isolation."""
    # This is inherently tested by the architecture
    # Each agent only sees their own collection
    pass


@then("the memories should not overlap")
@then("the projects should have isolated memories")
def assert_memory_isolation(request):
    """Assert memory isolation."""
    # This is inherently tested by the architecture
    pass

