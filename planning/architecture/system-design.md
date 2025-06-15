# Signal Hub System Architecture

## Overview
Signal Hub is an MCP server that provides intelligent context retrieval and model routing for Claude Code, optimizing costs while maintaining quality.

### 🎯 Hybrid Open Source Model
- **Signal Hub Basic** (Open Source): Core MCP functionality with basic routing and caching
- **Signal Hub Pro/Enterprise**: Advanced ML-powered features via plugin architecture
- **Plugin System**: Extensible design allowing Pro features to be added without modifying core

## Core Components

### 0. Plugin Architecture (NEW)
- **Plugin Manager**: Loads and manages plugin lifecycle
- **Plugin Interfaces**: ModelRouter, CacheStrategy, AnalyticsProvider
- **Feature Flags**: Edition-based feature availability
- **Plugin Registry**: Discovers and registers available plugins

### 1. MCP Server Layer
- **SignalHubServer**: Main server class handling MCP protocol
- **Tool Registry**: Manages available MCP tools
- **Request Handler**: Processes incoming tool requests
- **Response Builder**: Formats responses for Claude Code

### 2. Indexing Pipeline
- **Code Scanner**: Traverses and discovers files
- **File Parsers**: Language-specific parsing logic
- **Chunk Generator**: Creates semantic chunks from code
- **Embedding Service**: Generates vector embeddings
- **Metadata Extractor**: Captures file and code metadata

### 3. Retrieval System
- **Vector Store**: ChromaDB for development, pgvector for production
- **Similarity Search**: Finds relevant code chunks
- **Context Assembly**: Builds coherent context from chunks
- **Ranking Engine**: Orders results by relevance

### 4. Model Routing (Plugin-Based)
- **Basic Router** (Signal Hub Basic): Rule-based model selection
- **ML Router** (Pro Plugin): ML-powered complexity assessment
- **Routing Engine**: Plugin-based architecture for extensibility
- **Cost Tracker**: Monitors token usage and costs
- **Escalation Handler**: Manages manual model upgrades

### 5. Caching Layer (Plugin-Based)
- **Basic Cache** (Signal Hub Basic): Simple semantic caching
- **Advanced Cache** (Pro Plugin): ML-optimized caching strategies
- **Cache Manager**: Plugin-based cache strategy selection
- **Performance Monitor**: Tracks cache hit rates

## Data Flow

```
1. User Query → MCP Server
2. MCP Server → Complexity Assessment
3. Parallel:
   a. Vector Search → Retrieve Context
   b. Cache Lookup → Check for Similar Queries
4. Context Assembly → Rank and Filter
5. Model Selection → Route to Appropriate Model
6. Generate Response → Cache Result
7. Return to User via MCP
```

## Key Design Decisions

### Modularity
- **NEW**: Plugin architecture for all major components
- **NEW**: Feature flags for edition-based functionality
- Plugin architecture for parsers and embedders
- Swappable vector stores and cache backends
- Extensible tool system
- **NEW**: Clear separation between Basic and Pro features

### Performance
- Async/await for concurrent operations
- Batch processing for embeddings
- Lazy loading of large files
- Connection pooling for databases

### Scalability
- Stateless server design
- Horizontal scaling support
- Distributed caching capability
- Queue-based indexing for large codebases

### Security
- Sandboxed code execution
- API key management
- Rate limiting per user/project
- Audit logging for enterprise
- **NEW**: License key validation for Pro features
- **NEW**: Feature access control based on edition

## Technology Choices

### Core Stack
- **Language**: Python 3.11+
- **Framework**: MCP Python SDK
- **Async**: asyncio with aiohttp
- **Testing**: pytest with pytest-asyncio

### Data Storage
- **Vectors**: ChromaDB (dev), PostgreSQL + pgvector (prod)
- **Cache**: SQLite (dev), Redis (prod)
- **Config**: YAML files with environment overrides
- **Metrics**: Prometheus format

### External Services
- **Embeddings**: OpenAI API with local fallback
- **Models**: Anthropic API
- **Monitoring**: OpenTelemetry compatible
- **Logging**: Structured JSON logs

## Development Workflow

### Local Development
1. Clone repository
2. Install dependencies with Poetry
3. Run docker-compose for services
4. Start MCP server in development mode
5. Connect with Claude Code

### Testing Strategy
- Unit tests for all core modules
- Integration tests for MCP protocol
- End-to-end tests with mock Claude Code
- Performance benchmarks for routing decisions
- Load tests for concurrent users

### Deployment
- Docker containers for all services
- Kubernetes manifests for production
- Helm charts for enterprise deployment
- Terraform modules for cloud resources