# Sprint 1: Core Infrastructure - Detailed Implementation Plan

## Sprint Goal
Establish a solid foundation with a working MCP server that can connect to Claude Code, scan codebases, and generate embeddings stored in ChromaDB.

---

## SH-001: Initialize Open Source Repository
**Priority**: High | **Story Points**: 3 | **Dependencies**: None

### Subtasks:
1. **Repository Setup** (0.5 points)
   - Create GitHub repository with description
   - Configure repository settings (issues, discussions, wiki)
   - Set up branch protection for main branch

2. **License and Legal** (0.5 points)
   - Add MIT license file
   - Create NOTICE file for third-party attributions
   - Add copyright headers template

3. **Community Files** (1 point)
   - Create detailed README.md
   - Add CONTRIBUTING.md with guidelines
   - Create CODE_OF_CONDUCT.md
   - Add SECURITY.md for vulnerability reporting

4. **Issue Management** (1 point)
   - Create issue templates (bug, feature, question)
   - Create pull request template
   - Set up labels for issue categorization
   - Create GitHub project board for sprint tracking

### Testing:
- Verify all links in documentation work
- Test issue creation with templates
- Validate license compatibility

---

## SH-002: Python Project Structure
**Priority**: High | **Story Points**: 2 | **Dependencies**: SH-001

### Subtasks:
1. **Project Configuration** (0.5 points)
   ```
   signal-hub/
   ├── src/
   │   └── signal_hub/
   │       ├── __init__.py
   │       ├── __main__.py
   │       ├── config/
   │       ├── core/
   │       ├── indexing/
   │       ├── retrieval/
   │       ├── routing/
   │       └── utils/
   ├── tests/
   │   ├── unit/
   │   ├── integration/
   │   └── fixtures/
   ├── pyproject.toml
   └── Makefile
   ```

2. **Dependency Management** (0.5 points)
   - Configure Poetry with all dependencies
   - Create requirements.txt for non-Poetry users
   - Add .python-version file
   - Document dependency installation

3. **Development Tools** (0.5 points)
   - Configure pre-commit hooks
   - Set up .editorconfig
   - Create .env.example
   - Add VS Code workspace settings

4. **CI Configuration** (0.5 points)
   - Create initial GitHub Actions workflow
   - Add dependabot configuration
   - Configure code coverage reporting

### Testing:
- Verify Poetry installation works
- Test pre-commit hooks trigger correctly
- Validate CI pipeline runs

---

## SH-003: Basic MCP Server Implementation
**Priority**: High | **Story Points**: 5 | **Dependencies**: SH-002

### Subtasks:
1. **Core Server Class** (2 points)
   ```python
   # src/signal_hub/core/server.py
   class SignalHubServer:
       - __init__ with configuration
       - start() method
       - stop() method
       - handle_request() method
       - list_tools() implementation
   ```

2. **MCP Protocol Handler** (1.5 points)
   - Implement request parsing
   - Response formatting
   - Error handling and logging
   - Connection management

3. **Configuration System** (1 point)
   ```python
   # src/signal_hub/config/settings.py
   class Settings:
       - Load from YAML/JSON
       - Environment variable overrides
       - Validation with Pydantic
       - Default configurations
   ```

4. **Server Entry Point** (0.5 points)
   - CLI command to start server
   - Graceful shutdown handling
   - Health check endpoint
   - Basic logging setup

### Testing:
```python
# tests/unit/test_server.py
- test_server_initialization
- test_server_start_stop
- test_configuration_loading
- test_mcp_protocol_compliance
- test_error_handling
```

---

## SH-004: Codebase Scanner Module
**Priority**: High | **Story Points**: 5 | **Dependencies**: SH-003

### Subtasks:
1. **Directory Walker** (1.5 points)
   ```python
   # src/signal_hub/indexing/scanner.py
   class CodebaseScanner:
       - walk_directory(path, ignore_patterns)
       - respect_gitignore()
       - filter_by_extensions()
       - handle_symlinks safely
   ```

2. **File Discovery** (1 point)
   - Detect programming languages
   - Extract file metadata
   - Handle binary files
   - Progress tracking with callbacks

3. **Ignore Pattern System** (1.5 points)
   - Parse .gitignore files
   - Support custom ignore patterns
   - Handle nested .gitignore files
   - Performance optimization for large repos

4. **Scanning Configuration** (1 point)
   ```yaml
   # config/scanning.yaml
   scanning:
     max_file_size: 10MB
     ignore_patterns: []
     include_patterns: []
     follow_symlinks: false
   ```

### Testing:
```python
# tests/unit/test_scanner.py
- test_directory_walking
- test_gitignore_parsing
- test_file_filtering
- test_large_repository_performance
- test_symlink_handling
```

---

## SH-005: File Parser Framework
**Priority**: Medium | **Story Points**: 3 | **Dependencies**: SH-004

### Subtasks:
1. **Parser Base Class** (1 point)
   ```python
   # src/signal_hub/indexing/parsers/base.py
   class BaseParser(ABC):
       - parse(file_path) -> ParseResult
       - extract_chunks() -> List[Chunk]
       - get_metadata() -> Dict
   ```

2. **Language-Specific Parsers** (1.5 points)
   - Python parser with AST
   - JavaScript/TypeScript with tree-sitter
   - Markdown parser
   - Plain text fallback

3. **Parser Registry** (0.5 points)
   ```python
   # src/signal_hub/indexing/parsers/registry.py
   class ParserRegistry:
       - register_parser(extension, parser_class)
       - get_parser(file_path) -> BaseParser
       - list_supported_extensions()
   ```

### Testing:
```python
# tests/unit/test_parsers.py
- test_python_parser_functions
- test_javascript_parser
- test_markdown_parsing
- test_parser_registry
- test_unsupported_file_types
```

---

## SH-006: Embedding Generation Pipeline
**Priority**: High | **Story Points**: 5 | **Dependencies**: SH-005

### Subtasks:
1. **Embedding Service** (2 points)
   ```python
   # src/signal_hub/indexing/embeddings.py
   class EmbeddingService:
       - generate_embedding(text) -> Vector
       - batch_generate(texts) -> List[Vector]
       - handle_rate_limits()
       - cost_tracking()
   ```

2. **Chunk Processing** (1.5 points)
   - Text preprocessing
   - Token counting
   - Chunk size optimization
   - Metadata preservation

3. **Provider Abstraction** (1 point)
   - OpenAI provider
   - Local provider (sentence-transformers)
   - Provider selection logic
   - Fallback handling

4. **Batch Processing** (0.5 points)
   - Queue management
   - Progress tracking
   - Error recovery
   - Checkpointing

### Testing:
```python
# tests/unit/test_embeddings.py
- test_embedding_generation
- test_batch_processing
- test_provider_fallback
- test_rate_limit_handling
- test_cost_tracking
```

---

## SH-007: ChromaDB Integration
**Priority**: High | **Story Points**: 3 | **Dependencies**: SH-006

### Subtasks:
1. **Database Client** (1 point)
   ```python
   # src/signal_hub/storage/chromadb_client.py
   class ChromaDBClient:
       - connect(connection_string)
       - create_collection(name, metadata)
       - health_check()
   ```

2. **Vector Operations** (1 point)
   - Store embeddings with metadata
   - Query by similarity
   - Update existing vectors
   - Delete vectors

3. **Collection Management** (0.5 points)
   - Create project-specific collections
   - Collection versioning
   - Backup and restore
   - Migration support

4. **Query Interface** (0.5 points)
   ```python
   # src/signal_hub/storage/queries.py
   class VectorQuery:
       - search(query_vector, top_k)
       - filter_by_metadata()
       - hybrid_search()
   ```

### Testing:
```python
# tests/integration/test_chromadb.py
- test_connection_management
- test_vector_storage
- test_similarity_search
- test_metadata_filtering
- test_collection_operations
```

---

## SH-008: Development Environment Setup
**Priority**: Medium | **Story Points**: 2 | **Dependencies**: None

### Subtasks:
1. **Docker Configuration** (1 point)
   ```yaml
   # docker-compose.yml
   services:
     chromadb:
       image: chromadb/chroma
     redis:
       image: redis:alpine
     signal-hub:
       build: .
   ```

2. **Environment Scripts** (0.5 points)
   - setup.sh for first-time setup
   - Environment validation script
   - Data seeding script
   - Development server script

3. **Documentation** (0.5 points)
   - Developer setup guide
   - Troubleshooting guide
   - Architecture diagrams
   - API documentation

### Testing:
- Test Docker Compose setup
- Verify all services start correctly
- Test development workflow

---

## SH-009: Basic Logging and Monitoring
**Priority**: Medium | **Story Points**: 2 | **Dependencies**: SH-003

### Subtasks:
1. **Logging Configuration** (1 point)
   ```python
   # src/signal_hub/utils/logging.py
   - Structured JSON logging
   - Log levels configuration
   - Request ID tracking
   - Performance logging
   ```

2. **Metrics Collection** (0.5 points)
   - Request count
   - Response times
   - Error rates
   - Token usage

3. **Debug Tools** (0.5 points)
   - Debug mode flag
   - Request/response logging
   - Performance profiling
   - Memory usage tracking

### Testing:
```python
# tests/unit/test_logging.py
- test_structured_logging
- test_log_levels
- test_request_tracking
- test_metrics_collection
```

---

## SH-010: Initial CI/CD Pipeline
**Priority**: Medium | **Story Points**: 3 | **Dependencies**: SH-002

### Subtasks:
1. **Test Pipeline** (1 point)
   ```yaml
   # .github/workflows/test.yml
   - Python version matrix
   - Unit test execution
   - Integration tests
   - Coverage reporting
   ```

2. **Quality Checks** (1 point)
   - Linting (ruff)
   - Formatting (black)
   - Type checking (mypy)
   - Security scanning

3. **Release Pipeline** (1 point)
   - Version tagging
   - Changelog generation
   - PyPI publishing
   - Docker image building

### Testing:
- Verify CI runs on all PRs
- Test release process
- Validate coverage reporting

---

## Testing Strategy for Sprint 1

### Unit Tests (Target: 80% coverage)
- Test each module in isolation
- Mock external dependencies
- Focus on edge cases
- Use pytest fixtures

### Integration Tests
- Test MCP server with mock Claude Code
- Test full indexing pipeline
- Test ChromaDB operations
- End-to-end scanning and embedding

### Performance Tests
- Benchmark large repository scanning
- Measure embedding generation speed
- Test concurrent request handling
- Memory usage under load

### Test Structure:
```
tests/
├── unit/
│   ├── test_server.py
│   ├── test_scanner.py
│   ├── test_parsers.py
│   ├── test_embeddings.py
│   └── test_config.py
├── integration/
│   ├── test_mcp_protocol.py
│   ├── test_indexing_pipeline.py
│   └── test_chromadb_operations.py
├── fixtures/
│   ├── sample_codebases/
│   └── mock_responses/
└── conftest.py
```

## Definition of Done for Sprint 1
- [ ] All unit tests passing with >80% coverage
- [ ] Integration tests for critical paths
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] CI/CD pipeline green
- [ ] Performance benchmarks established
- [ ] Demo-able MCP server that can index a small codebase