# Signal Hub Documentation

Welcome to Signal Hub - an intelligent MCP server that extends Claude's context through RAG (Retrieval-Augmented Generation) while optimizing costs via smart model routing and caching.

<div align="center">
  <img src="assets/signal-hub-banner.png" alt="Signal Hub Banner" width="600">
</div>

## 🚀 What is Signal Hub?

Signal Hub solves the fundamental limitation of LLM context windows by providing unlimited effective context through semantic search of your codebase. It intelligently routes queries between Claude's models (Haiku, Sonnet, Opus) to optimize costs while maintaining quality.

### Key Benefits

- **🧠 Unlimited Context**: Access your entire codebase through semantic search
- **💰 70%+ Cost Savings**: Smart routing reduces API costs dramatically  
- **⚡ Lightning Fast**: Semantic caching for instant responses
- **🔧 Zero Configuration**: Works out of the box with sensible defaults
- **🌍 Open Source**: MIT licensed with active community

## 📦 Editions

### Signal Hub Basic (Open Source)
The community edition provides everything you need to get started:

- ✅ MCP server integration with Claude Code
- ✅ Codebase indexing and semantic search
- ✅ Rule-based model routing
- ✅ Semantic caching
- ✅ Cost tracking
- ✅ Manual escalation

### Signal Hub Pro (Coming Soon)
Advanced features for power users ($29/mo + 15% of savings):

- 🚀 ML-powered intelligent routing
- 📊 Detailed analytics dashboard
- 🔌 REST API access
- 🏆 Priority support

### Signal Hub Enterprise
For teams and organizations (custom pricing):

- 👥 Team management
- 🔐 SSO integration  
- 📊 Custom dashboards
- 🏢 Dedicated support

## 🎯 Quick Start

Get up and running in under 5 minutes:

```bash
# Install Signal Hub
pip install signal-hub

# Initialize your project
signal-hub init my-project
cd my-project

# Index your codebase
signal-hub index .

# Start the server
signal-hub serve
```

Then configure Claude Code to use Signal Hub as an MCP server!

## 📚 Documentation Overview

### [Getting Started](getting-started/installation.md)
New to Signal Hub? Start here:
- Installation guide for all platforms
- Quick start tutorial
- Your first project walkthrough
- Core concepts explained

### [User Guide](user-guide/configuration.md)
Learn how to use Signal Hub effectively:
- Configuration options
- Indexing strategies
- Search techniques
- Routing optimization
- Security best practices

### [Architecture](architecture/overview.md)
Understand how Signal Hub works:
- System design
- Component breakdown
- Plugin system
- Data flow

### [API Reference](api-reference/mcp-tools.md)
Technical details for developers:
- MCP tool specifications
- Configuration schemas
- Plugin development
- Python API

### [Troubleshooting](troubleshooting/common-issues.md)
Get help when you need it:
- Common issues and solutions
- Debugging techniques
- Performance tuning
- FAQ

## 🤝 Community

Join our growing community:

- 💬 [Discord Server](https://discord.gg/signalhub) - Get help and chat
- 🐛 [Issue Tracker](https://github.com/wespiper/signal-hub/issues) - Report bugs
- 💡 [Discussions](https://github.com/wespiper/signal-hub/discussions) - Share ideas
- 🌟 [GitHub](https://github.com/wespiper/signal-hub) - Star us!

## 🚦 Current Status

Signal Hub Basic is feature-complete and ready for production use:

- ✅ **Sprint 1**: Core infrastructure and MCP server
- ✅ **Sprint 2**: RAG implementation and search
- ✅ **Sprint 3**: Model routing and caching
- 🚧 **Sprint 4**: Documentation and polish (current)

## 🎁 Early Access Program

All Pro and Enterprise features are currently FREE during our beta period. Join by setting:

```bash
export SIGNAL_HUB_EARLY_ACCESS=true
```

Help shape the future of Signal Hub!