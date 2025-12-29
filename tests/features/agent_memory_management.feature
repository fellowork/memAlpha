Feature: Agent Memory Management
  As an AI coding agent working on software projects
  I want to store and retrieve my memories
  So that I can remember important information across conversations

  Background:
    Given the memory system is running
    And I am agent "cursor-assistant" working on project "webstore"

  Scenario: Agent stores a new memory
    When I store a memory with content "User prefers TypeScript over JavaScript"
    Then the memory should be successfully stored
    And the memory should have a unique ID
    And the memory should contain the content "User prefers TypeScript over JavaScript"

  Scenario: Agent retrieves a previously stored memory
    Given I have stored a memory "The database uses PostgreSQL"
    When I retrieve that memory by its ID
    Then I should get the memory with content "The database uses PostgreSQL"

  Scenario: Agent searches for relevant memories
    Given I have stored the following memories:
      | content                                    |
      | User prefers React for frontend            |
      | The API is built with FastAPI              |
      | Database migrations use Alembic            |
      | User wants dark mode support               |
    When I search for memories about "frontend preferences"
    Then I should find at least 1 relevant memory
    And the top result should be related to frontend

  Scenario: Agent updates a memory when requirements change
    Given I have stored a memory "API uses REST endpoints"
    When I update that memory to "API uses GraphQL endpoints"
    Then the memory should be updated successfully
    And retrieving it should show "API uses GraphQL endpoints"

  Scenario: Agent deletes outdated memories
    Given I have stored a memory "Using MongoDB for storage"
    When I delete that memory
    Then retrieving it should return nothing

  Scenario: Agent stores memories with custom metadata
    When I store a memory with:
      | field    | value                           |
      | content  | User wants email notifications  |
      | tags     | ["feature-request", "email"]    |
      | category | requirement                     |
      | priority | high                            |
    Then the memory should include the custom metadata
    And the metadata should have tags "feature-request" and "email"

  Scenario: Multiple agents working on the same project
    Given agent "backend-specialist" is working on project "webstore"
    And agent "frontend-specialist" is working on project "webstore"
    When "backend-specialist" stores a memory "Database schema designed"
    And "frontend-specialist" stores a memory "UI mockups completed"
    Then "backend-specialist" should only see their own memories
    And "frontend-specialist" should only see their own memories
    And the memories should not overlap

  Scenario: Agent working on multiple projects
    Given I am agent "cursor-assistant" working on project "webstore"
    And I store a memory "Webstore uses Stripe for payments"
    When I switch to project "blog-platform"
    And I store a memory "Blog uses Markdown for posts"
    Then searching in "webstore" should find payment-related memories
    And searching in "blog-platform" should find markdown-related memories
    And the projects should have isolated memories

