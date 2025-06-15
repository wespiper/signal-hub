# Signal Hub

![CI](https://github.com/wespiper/signal-hub/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/github/license/wespiper/signal-hub)
![GitHub release](https://img.shields.io/github/v/release/wespiper/signal-hub?include_prereleases)

> Intelligent developer assistant that extends Claude's context through MCP+RAG, providing seamless access to codebase knowledge while optimizing costs through smart model routing and caching.

## Overview

Signal Hub is part of the Signal ecosystem, serving as the central convergence point where all your code context comes together for intelligent AI routing. It acts as an MCP (Model Context Protocol) server that gives Claude unlimited effective context through RAG (Retrieval-Augmented Generation) while intelligently routing queries to the most cost-effective model.

### 🎯 Signal Hub Editions

#### Signal Hub Basic (Open Source)
The community edition provides core functionality for extending Claude's context:
- ✅ MCP server integration with Claude Code
- ✅ Codebase indexing and semantic search
- ✅ Basic RAG retrieval and context assembly
- ✅ Simple rule-based model routing
- ✅ Semantic caching for repeated queries
- ✅ Manual escalation to premium models
- ✅ Basic cost tracking

#### Signal Hub (Pro/Enterprise) - Coming Soon
Advanced features for teams and power users:
- 🚀 ML-powered intelligent model routing
- 📈 Learning algorithms that improve over time
- 💰 Advanced cost optimization (save 70%+ on AI costs)
- 📊 Detailed analytics and ROI reporting
- 👥 Team collaboration and sharing
- 🔐 Enterprise security and compliance
- ⚡ Priority support and SLAs

> **Early Access Program**: Currently, all features are available to early adopters to help us refine the product and pricing. [Join our Discord](https://discord.gg/signalhub) to participate!

### Key Features

- 🚀 **Unlimited Context**: Access your entire codebase through semantic search
- 💰 **Cost Optimization**: Automatic routing between Haiku, Sonnet, and Opus based on complexity
- ⚡ **Lightning Fast**: Semantic caching for instant responses to similar queries
- 🔄 **Continuous Learning**: Improves routing decisions based on user feedback (Pro)
- 🛠️ **Zero Friction**: Works out of the box with minimal configuration
- 🌍 **Open Source**: Community-driven development with transparent roadmap

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker Desktop
- Git

### One-Command Setup

#### macOS/Linux
```bash
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
./scripts/setup.sh
```

#### Windows
```powershell
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
.\scripts\setup.ps1
```

### Manual Setup

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Configure Signal Hub:
```bash
cp config/.env.example config/.env
# Add your OpenAI API key for embeddings
```

4. Start services:
```bash
cd docker && docker compose up -d
cd .. && signal-hub serve --config config/dev.yaml
```

5. Connect with Claude Code by adding Signal Hub to your MCP servers configuration.

## Usage

Signal Hub provides several MCP tools for intelligent code navigation:

- `search_codebase`: Semantic search across all code
- `explain_code`: Deep explanation of code snippets
- `find_references`: Find usages of functions/classes
- `get_context`: Get relevant context for current work
- `escalate_query`: Manual escalation to better model

## Architecture

Signal Hub consists of several key components:

1. **MCP Server**: Handles communication with Claude Code
2. **Indexing Pipeline**: Scans and embeds your codebase
3. **RAG System**: Retrieves relevant context for queries
4. **Model Router**: Intelligently selects the appropriate model
5. **Cache Layer**: Stores and retrieves similar queries

## Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Generate coverage report
make test-coverage
```

### Code Quality

```bash
make format     # Format code with Black
make lint       # Run Ruff linter
make type-check # Type checking with MyPy
make quality    # Run all quality checks
```

### Development Workflow

1. **Start Development Environment**:
   ```bash
   make dev
   ```

2. **Run with Early Access Features**:
   ```bash
   SIGNAL_HUB_EARLY_ACCESS=true signal-hub serve
   ```

3. **Monitor Logs**:
   ```bash
   # JSON logs for production
   SIGNAL_HUB_LOG_FORMAT=json signal-hub serve
   
   # Check metrics endpoint
   curl http://localhost:3334/metrics
   ```

### Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

- 🐛 Report bugs using our [issue template](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 Request features using our [feature template](.github/ISSUE_TEMPLATE/feature_request.md)
- 🔧 Submit PRs following our [PR template](.github/pull_request_template.md)

## Roadmap

### Phase 1: Open Source Foundation (Complete ✅)
- ✅ Basic MCP server implementation with plugin architecture
- ✅ Codebase indexing and embedding pipeline
- ✅ File parser framework (Python, JavaScript, Markdown)
- ✅ ChromaDB integration for vector storage
- ✅ Development environment with Docker
- ✅ Comprehensive logging and monitoring
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Security scanning and dependency management

### Phase 2: Community & Intelligence (Next)
- 🚀 RAG retrieval system with semantic search
- 🧠 ML-powered routing optimization
- 📊 User feedback collection and learning
- 📈 Performance analytics dashboard
- 🔄 Advanced caching strategies
- 🌐 Web-based configuration UI

### Phase 3: Monetization
- Pro tier with advanced features
- Enterprise deployment options
- Team management capabilities

### Phase 4: Platform Expansion
- IDE integrations
- API for third-party tools
- Advanced customization

## License

Signal Hub is open source software licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

- 📖 [Documentation](https://docs.signalhub.ai)
- 💬 [Discord Community](https://discord.gg/signalhub)
- 🐛 [Issue Tracker](https://github.com/yourusername/signal-hub/issues)
- 📧 [Email Support](mailto:support@signalhub.ai)

## Acknowledgments

Signal Hub is built on top of excellent open source projects:
- [MCP](https://github.com/anthropics/mcp) - Model Context Protocol by Anthropic
- [ChromaDB](https://www.trychroma.com/) - Vector database for embeddings
- [Tree-sitter](https://tree-sitter.github.io/) - Code parsing library

---

**Signal Hub** - Where your codebase knowledge meets intelligent AI routing.