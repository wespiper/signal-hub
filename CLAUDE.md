# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with Signal Hub.

## Engineering Approach

Take the role of a senior principal engineer. Prioritize:

- Clean, maintainable code architecture
- Scalable and performant solutions
- Comprehensive error handling
- Clear documentation and comments
- Industry best practices and design patterns
- Test-driven development (TDD)

## Project Overview

**Signal Hub** is an intelligent MCP server that extends Claude's context through RAG (Retrieval-Augmented Generation) while optimizing costs via smart model routing and caching. It enables unlimited effective context for Claude Code through semantic search of codebases.

### 🎯 Hybrid Open Source Model
- **Signal Hub Basic** (Open Source): Core MCP, rule-based routing, basic caching
- **Signal Hub Pro** ($29/mo + 15% of savings): ML-powered routing, advanced analytics
- **Signal Hub Enterprise**: Team features, SSO, audit logging
- **Early Access**: Set `SIGNAL_HUB_EARLY_ACCESS=true` for all features during beta

See `docs/EDITIONS.md` for complete feature comparison.

**Current Status**: Sprint 1 (Core Infrastructure) - Building Signal Hub Basic foundation with plugin architecture for Pro/Enterprise features.

## Architecture Overview

- **MCP Server**: Handles communication with Claude Code (with plugin support)
- **Plugin System**: Extensible architecture for Pro/Enterprise features
- **Feature Flags**: Edition-based functionality control
- **Indexing Pipeline**: Scans, parses, and embeds codebases
- **RAG System**: Retrieves relevant context via semantic search
- **Model Router**: Rule-based (Basic) or ML-powered (Pro) selection
- **Cache Layer**: Basic semantic caching (Basic) or smart deduplication (Pro)

See `planning/architecture/system-design.md` for detailed architecture.

### Core Technology

- **Backend**: Python 3.11+, MCP SDK, asyncio
- **Vector Store**: ChromaDB (dev), PostgreSQL + pgvector (prod)
- **Embeddings**: OpenAI API with local fallback
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Quality**: black, ruff, mypy, pre-commit

## Development Workflow

### Step 1: Before Starting Any Task

```bash
# Check project status and edition strategy
cat planning/README.md
cat docs/EDITIONS.md

# Review current sprint tickets
ls planning/tickets/sprint-*/

# Check plugin architecture
cat src/signal_hub/core/plugins.py
cat src/signal_hub/core/features.py

# Check implementation status
find src/ -name "*.py" | xargs grep -l "TODO\|FIXME\|NotImplementedError"

# Review existing tests
find tests/ -name "test_*.py" | head -10
```

### Step 2: Plan and Track Progress

- Use TodoWrite tool to break down complex tasks
- Reference specific tickets (e.g., SH-S01-003)
- Mark tasks as in_progress before starting
- Update status immediately upon completion

### Step 3: Implement Following TDD

1. Write tests first based on acceptance criteria
2. Implement to make tests pass
3. Refactor for clarity and performance
4. Ensure >80% test coverage

### Step 4: Quality Checks

```bash
# Run tests for your component
pytest tests/unit/[component] -v

# Check coverage
pytest tests/ --cov=signal_hub --cov-report=term-missing

# Code quality
make lint
make format
make type-check

# Full test suite before committing
make test
```

### Step 5: Commit Using Standard Format

```bash
git add .
git commit -m "Implement [Ticket ID]: [Brief description]

- [Key implementation detail]
- [Key implementation detail]

Closes [Ticket ID]

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Development Commands

### Essential Commands

```bash
# Development setup
make dev-install

# Run specific tests
pytest tests/unit/test_server.py -v

# Run with coverage
pytest --cov=signal_hub --cov-report=html

# Code quality
make format  # Formats code
make lint    # Checks style
make type-check  # Type checking

# Start development server (Signal Hub Basic)
signal-hub serve --config config/dev.yaml

# Start with early access (all features enabled)
SIGNAL_HUB_EARLY_ACCESS=true signal-hub serve --config config/dev.yaml
```

### Discovery Commands

```bash
# Find TODOs
grep -r "TODO\|FIXME" src/

# Check code structure
find src/ -name "*.py" | head -20

# Review configuration
find . -name "*.yaml" -o -name "*.toml" | grep -v ".git"

# Check for incomplete implementations
grep -r "NotImplementedError\|pass" src/
```

## Quality Requirements

- **Test Coverage**: Minimum 80% (target 90%+)
- **Performance**: 
  - Indexing: 1000 files/minute
  - Search: <2 seconds response time
  - Embedding: 1000 chunks/minute
- **Documentation**: Docstrings for all public APIs
- **Error Handling**: Graceful degradation, clear error messages

## Project Structure

```
signal-hub/
├── src/signal_hub/        # Main application code
│   ├── core/             # MCP server implementation
│   │   ├── plugins.py    # Plugin system (✓ IMPLEMENTED)
│   │   ├── features.py   # Feature flags (✓ IMPLEMENTED)
│   │   ├── server.py     # MCP server with plugin support
│   │   └── tools.py      # Tool registry
│   ├── plugins/          # Plugin implementations
│   │   └── pro_example.py # Example Pro features
│   ├── indexing/         # Code scanning and parsing
│   │   ├── scanner.py    # Directory traversal
│   │   ├── parsers/      # Language-specific parsers
│   │   └── embeddings/   # Embedding generation
│   ├── retrieval/        # RAG implementation
│   ├── routing/          # Model selection logic
│   ├── storage/          # Vector and cache stores
│   └── utils/            # Shared utilities
├── tests/
│   ├── unit/            # Unit tests by component
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test data
├── planning/            # Sprint planning and tickets
├── docs/               # Documentation
│   └── EDITIONS.md     # Signal Hub editions comparison
└── examples/
    └── plugin_demo.py  # Plugin system demonstration
```

## Current Sprint Focus (Sprint 1)

Building Signal Hub Basic foundation with plugin architecture:
- SH-S01-001: Repository setup (70% complete - needs branch protection)
- SH-S01-002: Python project structure with plugins (✓ Partially complete)
- SH-S01-003: Basic MCP server with plugin support (Priority)
- SH-S01-004: Codebase scanner
- SH-S01-005: File parser framework
- SH-S01-006: Embedding generation
- SH-S01-007: ChromaDB integration

**Key Achievement**: Plugin architecture and feature flags already implemented!

## Testing Strategy

Follow the comprehensive testing strategy in `planning/testing-strategy.md`:
- Unit tests for all components
- Integration tests for workflows
- Performance benchmarks
- Mock external services in unit tests

## Important Reminders

1. **Follow TDD**: Write tests before implementation
2. **Check tickets**: Each ticket has detailed requirements
3. **Use abstractions**: Database abstraction layer (Sprint 2)
4. **Performance matters**: Batch operations where possible
5. **Document as you go**: Clear docstrings and comments
6. **Open source quality**: This will be public code
7. **Edition awareness**: Consider Basic vs Pro features when implementing
8. **Plugin first**: New Pro features should be implemented as plugins
9. **Feature flags**: Use `@require_feature` decorator for Pro/Enterprise features

## Getting Started

```bash
# 1. Review current sprint
cat planning/tickets/sprint-01/README.md

# 2. Set up development environment
make dev-install

# 3. Run existing tests
make test

# 4. Start with a specific ticket
cat planning/tickets/sprint-01/SH-S01-003-mcp-server-implementation.md

# 5. Begin TDD implementation
```

## Key Documentation References

- **Edition Strategy**: `docs/EDITIONS.md` - Feature comparison and pricing
- **Sprint Overview**: `planning/sprints/overview.md` - High-level sprint plan
- **Sprint Goals**: `planning/sprints/sprint-goals.md` - Detailed goals by edition
- **Architecture**: `planning/architecture/system-design.md` - Plugin architecture
- **Plugin System**: `src/signal_hub/core/plugins.py` - How to create plugins
- **Feature Flags**: `src/signal_hub/core/features.py` - Edition management

---

**Remember**: We're building Signal Hub Basic as a high-quality open source foundation, with clear paths to Pro ($29/mo + 15% of savings) and Enterprise editions. Quality and maintainability are paramount. Follow the sprint plan and ticket requirements closely.