Feature: Team of Agents Building Software Together
  As part of a team of AI agents building software
  Each agent maintains their own specialized memories
  While working on shared projects

  Background:
    Given a memory system is available
    And we have a project "ai-powered-crm"

  Scenario: Backend agent remembers database decisions
    Given I am the "backend-architect" agent
    When I store these memories about the project:
      | content                                      | tags                    |
      | Using PostgreSQL 15 for main database        | ["database", "tech"]    |
      | Redis for caching and session management     | ["cache", "tech"]       |
      | Database replication configured for reads    | ["database", "scaling"] |
    Then I should have 3 memories stored
    And searching for "database" should return 2 memories

  Scenario: Frontend agent tracks UI decisions independently
    Given I am the "frontend-developer" agent
    When I store these memories:
      | content                                   | category    |
      | Using Next.js 14 with App Router          | technology  |
      | Tailwind CSS for styling                  | technology  |
      | User prefers clean, minimal interface     | preference  |
    And the "backend-architect" agent has 3 memories stored
    Then I should see exactly 3 memories in my list
    And the backend agent's memories should not appear in my list

  Scenario: DevOps agent manages deployment memories
    Given I am the "devops-engineer" agent
    When I store a memory "CI/CD pipeline uses GitHub Actions"
    And I store a memory "Deploying to AWS ECS Fargate"
    And I search for "deployment"
    Then I should find memories about AWS and GitHub Actions
    And I should not see other agents' memories

  Scenario: QA agent tracks test coverage and bugs
    Given I am the "qa-specialist" agent
    When I store memories with priority levels:
      | content                           | priority |
      | Critical bug in authentication    | 10       |
      | Unit test coverage at 85%         | 5        |
      | Integration tests need updating   | 7        |
    And I search for memories with filters:
      | field    | operator | value |
      | priority | >=       | 7     |
    Then I should find 2 high-priority memories

  Scenario: Agent switches between tasks
    Given I am the "fullstack-developer" agent
    And I am working on project "ai-powered-crm"
    When I store a memory "CRM uses Salesforce API integration"
    And I switch to project "internal-dashboard"
    And I store a memory "Dashboard shows real-time metrics"
    Then my "ai-powered-crm" memories should include Salesforce
    And my "internal-dashboard" memories should include metrics
    And the two projects should have separate memory spaces

  Scenario: Team lead reviews agent progress
    Given I am the "team-lead" agent
    When I list all my memories for project "ai-powered-crm"
    Then I should see memories organized by timestamp
    And each memory should have metadata about when it was created

  Scenario: Agent migrates knowledge between embedding providers
    Given I am the "backend-architect" agent
    And I have 5 memories stored using local embeddings
    When the system switches to OpenAI embeddings
    And I store a new memory "Added GraphQL API endpoint"
    Then I should only see 1 memory in my current memory space
    And the old local embedding memories should be in a separate space

  Scenario: Agent performs semantic search for related memories
    Given I am the "security-specialist" agent
    When I store these memories:
      | content                                           |
      | Implemented JWT authentication with 2FA           |
      | API keys stored in AWS Secrets Manager            |
      | Rate limiting: 100 requests per minute per user   |
      | CORS configured for trusted domains only          |
    And I search for "how do we handle auth"
    Then the top result should be about JWT authentication
    And the results should be ranked by semantic similarity

  Scenario: Long-running project with many memories
    Given I am the "project-manager" agent
    And I have stored 500 memories over 6 months
    When I search for "sprint planning decisions"
    Then the search should complete quickly
    And I should get the most relevant results first
    And I can paginate through additional results

