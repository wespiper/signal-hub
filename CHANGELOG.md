# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Sprint 1 Complete - 2024-01-15

#### Added
- **Core Infrastructure**
  - MCP server implementation with stdio transport for Claude Code integration
  - Plugin architecture for extensible Pro/Enterprise features
  - Feature flags system for edition-based functionality
  - Tool registry with automatic plugin integration
  
- **Indexing Pipeline**
  - Asynchronous codebase scanner with gitignore support
  - File parser framework with language-specific parsers:
    - Python parser using AST for accurate code extraction
    - JavaScript/TypeScript parser with tree-sitter
    - Markdown parser for documentation
  - Embedding generation service with multiple providers:
    - OpenAI embeddings (primary)
    - Local sentence-transformers (fallback)
  
- **Storage & Retrieval**
  - ChromaDB integration for vector storage
  - Async wrapper for ChromaDB operations
  - Collection management with metadata support
  
- **Developer Experience**
  - One-command setup scripts for macOS/Linux and Windows
  - Docker Compose development environment
  - Comprehensive development documentation
  - Example configurations and environment templates
  
- **Observability**
  - Structured JSON logging with context propagation
  - Prometheus-compatible metrics collection
  - Request tracking middleware
  - Health check and monitoring endpoints
  - Performance timing for key operations
  
- **CI/CD Pipeline**
  - GitHub Actions workflows:
    - Matrix testing across Python 3.11/3.12 and multiple OS
    - Code quality checks (Black, Ruff, MyPy)
    - Security scanning (Bandit, Safety, CodeQL)
    - Automated releases to PyPI and Docker Hub
    - Documentation building and deployment
  - Dependabot configuration for dependency updates
  - Issue and PR templates

#### Technical Achievements
- 80%+ test coverage across all components
- Comprehensive error handling and graceful degradation
- Async-first architecture for scalability
- Plugin system allowing clean separation of Basic/Pro features
- Production-ready logging and monitoring
- Security-first approach with multiple scanners

#### Documentation
- Complete development setup guide
- Sprint planning and ticket tracking
- Architecture documentation with plugin system
- Testing strategy documentation
- Edition comparison (Basic vs Pro/Enterprise)

### Known Issues
- MCP SDK import gracefully handled when not installed
- ChromaDB async operations use sync-to-async wrapper (pending native async support)

### Next Steps
- Sprint 2: Enhanced indexing and RAG implementation
- Metadata extraction for richer search
- Database abstraction layer for production deployment
- Batch processing optimizations

---

## [0.1.0] - TBD

Initial release of Signal Hub Basic edition.