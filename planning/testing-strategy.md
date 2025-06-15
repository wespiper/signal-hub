# Signal Hub Testing Strategy

## Overview
This document outlines the comprehensive testing strategy for Signal Hub, ensuring reliability, performance, and maintainability across all components.

## Testing Philosophy
- **Test-Driven Development (TDD)**: Write tests before implementation
- **Comprehensive Coverage**: Aim for >80% code coverage
- **Fast Feedback**: Unit tests should run in <30 seconds
- **Realistic Testing**: Integration tests with real dependencies
- **Performance Awareness**: Benchmark critical paths

## Testing Pyramid

```
         /\
        /  \  E2E Tests (5%)
       /----\  - Full system tests
      /      \  - User journey tests
     /--------\  Integration Tests (20%)
    /          \  - API contract tests
   /            \  - Database tests
  /--------------\  Unit Tests (75%)
 /                \  - Business logic
/                  \  - Pure functions
```

## Test Categories

### 1. Unit Tests
**Purpose**: Test individual components in isolation

**Scope**:
- Individual functions and methods
- Class behavior
- Edge cases and error handling
- No external dependencies (use mocks)

**Tools**:
- pytest
- pytest-mock
- pytest-asyncio
- hypothesis (property-based testing)

**Example Structure**:
```python
# tests/unit/test_embedding_service.py
class TestEmbeddingService:
    def test_generate_embedding_success(self, mock_openai_client):
        """Test successful embedding generation"""
        
    def test_generate_embedding_rate_limit(self, mock_openai_client):
        """Test rate limit handling"""
        
    def test_batch_processing_optimization(self):
        """Test batch size optimization logic"""
```

### 2. Integration Tests
**Purpose**: Test component interactions and external dependencies

**Scope**:
- Database operations
- API integrations
- File system operations
- Multi-component workflows

**Tools**:
- pytest
- testcontainers (for databases)
- httpx for API mocking
- temporary directories

**Example Structure**:
```python
# tests/integration/test_indexing_pipeline.py
class TestIndexingPipeline:
    def test_full_codebase_indexing(self, temp_codebase, chroma_db):
        """Test indexing a complete codebase"""
        
    def test_incremental_indexing(self, existing_index):
        """Test updating an existing index"""
```

### 3. End-to-End Tests
**Purpose**: Test complete user scenarios

**Scope**:
- MCP server connection
- Full request/response cycle
- Multi-tool interactions
- Performance under load

**Tools**:
- pytest
- MCP test client
- Performance profiling tools

### 4. Performance Tests
**Purpose**: Ensure system meets performance requirements

**Metrics**:
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Resource usage (CPU, memory)
- Concurrency handling

**Tools**:
- pytest-benchmark
- memory_profiler
- locust (for load testing)

## Test Data Management

### Fixtures
```python
# tests/conftest.py
@pytest.fixture
def sample_python_code():
    """Provides sample Python code for testing"""
    
@pytest.fixture
def mock_codebase(tmp_path):
    """Creates a temporary codebase structure"""
    
@pytest.fixture
def embedding_vectors():
    """Provides pre-computed embedding vectors"""
```

### Test Repositories
- Small repo (<100 files): Quick tests
- Medium repo (~1000 files): Integration tests  
- Large repo (>10000 files): Performance tests

## Mocking Strategy

### External Services
```python
# Always mock in unit tests
- OpenAI API calls
- Anthropic API calls
- Network requests

# Real services in integration tests (with test accounts)
- ChromaDB operations
- File system operations
```

### Mock Levels
1. **Function level**: Mock specific functions
2. **Class level**: Mock entire classes
3. **Service level**: Mock external services
4. **Network level**: Intercept HTTP requests

## Continuous Integration

### PR Checks (Must Pass)
```yaml
- Unit tests (all platforms)
- Integration tests
- Linting and formatting
- Type checking
- Security scanning
- Coverage report (>80%)
```

### Nightly Builds
```yaml
- Full E2E test suite
- Performance benchmarks
- Large codebase tests
- Memory leak detection
- Dependency updates
```

## Test Organization

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_server.py
│   │   └── test_config.py
│   ├── indexing/
│   │   ├── test_scanner.py
│   │   ├── test_parsers.py
│   │   └── test_embeddings.py
│   ├── retrieval/
│   │   └── test_search.py
│   └── routing/
│       └── test_model_selection.py
├── integration/
│   ├── test_mcp_protocol.py
│   ├── test_indexing_pipeline.py
│   ├── test_retrieval_accuracy.py
│   └── test_caching.py
├── e2e/
│   ├── test_user_scenarios.py
│   └── test_performance.py
├── fixtures/
│   ├── codebases/
│   ├── embeddings/
│   └── responses/
├── conftest.py
└── pytest.ini
```

## Testing Best Practices

### 1. Test Naming
```python
def test_should_return_embeddings_when_valid_text_provided():
    """Clear, descriptive test names"""
```

### 2. Arrange-Act-Assert
```python
def test_embedding_generation():
    # Arrange
    service = EmbeddingService()
    text = "sample code"
    
    # Act
    result = service.generate_embedding(text)
    
    # Assert
    assert len(result) == 1536
```

### 3. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- No shared state between tests

### 4. Deterministic Tests
- Use fixed seeds for randomness
- Mock time-dependent operations
- Control external dependencies

## Coverage Requirements

### Minimum Coverage Targets
- Overall: 80%
- Core modules: 90%
- API endpoints: 95%
- Utility functions: 70%

### Coverage Exclusions
```ini
# .coveragerc
[run]
omit = 
    */tests/*
    */migrations/*
    */__main__.py
    */config/*
```

## Performance Benchmarks

### Response Time Targets
- Semantic search: <100ms (p95)
- Embedding generation: <50ms per chunk
- Cache hit: <10ms
- Model routing decision: <5ms

### Throughput Targets
- 100 concurrent requests
- 1000 requests/minute sustained
- 10GB codebase indexing in <30 minutes

## Test Maintenance

### Weekly Tasks
- Review flaky tests
- Update test data
- Performance regression check
- Coverage trend analysis

### Monthly Tasks
- Dependency updates
- Test suite optimization
- Mock data refresh
- Documentation updates

## Security Testing

### Static Analysis
- Bandit for Python security
- Dependency vulnerability scanning
- Secret detection in code

### Dynamic Testing
- Input validation testing
- Authentication/authorization tests
- Rate limiting verification
- Injection attack prevention

## Debugging Failed Tests

### Test Artifacts
- Detailed logs for each test
- Screenshots for UI tests
- Performance profiles
- Memory dumps for crashes

### Debugging Tools
```python
# Enable detailed output
pytest -vvs

# Run specific test
pytest tests/unit/test_server.py::test_specific

# Debug with pdb
pytest --pdb

# Profile test performance
pytest --profile
```

## Test Reporting

### CI/CD Reports
- Test results summary
- Coverage reports with diff
- Performance comparison
- Flaky test tracking

### Metrics Dashboard
- Test execution time trends
- Coverage trends
- Failure rate by module
- Performance benchmarks

## Migration Testing

### Version Compatibility
- Test upgrade paths
- Data migration verification
- API backward compatibility
- Configuration migration

## Disaster Recovery Testing

### Scenarios
- Database corruption
- Service unavailability
- Data loss recovery
- Backup restoration