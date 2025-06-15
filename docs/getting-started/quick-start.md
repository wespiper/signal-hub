# Quick Start Guide

Get Signal Hub running with your first project in under 10 minutes! This guide assumes you've already [installed Signal Hub](installation.md).

## 🚀 5-Minute Setup

### Step 1: Initialize Your Project

```bash
# Create a new directory for your project
mkdir my-awesome-project
cd my-awesome-project

# Initialize Signal Hub
signal-hub init
```

This creates a `signal-hub.yaml` configuration file with sensible defaults.

### Step 2: Configure Your API Key

Signal Hub uses OpenAI for embeddings. Set your API key:

```bash
# Option 1: Environment variable (recommended)
export OPENAI_API_KEY="sk-..."

# Option 2: Store securely in Signal Hub
signal-hub keys set openai
# Enter your API key when prompted
```

!!! tip "API Key Security"
    Signal Hub encrypts stored API keys. Never commit API keys to version control!

### Step 3: Index Your Codebase

Point Signal Hub at your code:

```bash
# Index current directory
signal-hub index .

# Or index a specific project
signal-hub index ~/projects/my-app
```

You'll see progress output:
```
🔍 Scanning files...
📁 Found 156 files to index
🧠 Generating embeddings...
✨ Indexed 156 files in 45 seconds
```

### Step 4: Start the MCP Server

```bash
signal-hub serve
```

Output:
```
🚀 Signal Hub MCP Server
📍 Listening on stdio
🔧 4 tools available
⚡ Ready for connections!
```

### Step 5: Connect Claude Code

Add Signal Hub to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "signal-hub": {
      "command": "signal-hub",
      "args": ["serve"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

## 🎯 Your First Search

Once connected, try these commands in Claude Code:

### Basic Code Search
```
"Find the function that handles user authentication"
```

Signal Hub will:
1. Search semantically across your codebase
2. Return relevant code snippets
3. Include surrounding context

### Explain Code
```
"Explain how the payment processing works"
```

Signal Hub will:
1. Find all payment-related code
2. Assemble coherent context
3. Route to appropriate model

### Find Similar Code
```
"Find code similar to this error handling pattern"
```

## 🎮 Interactive Demo

Let's walk through a real example with a Python web app:

### 1. Clone Sample Project
```bash
git clone https://github.com/signal-hub/sample-webapp
cd sample-webapp
```

### 2. Quick Index
```bash
signal-hub index . --quick
```

The `--quick` flag indexes only key files for faster demo.

### 3. Test Searches

Try these searches to see Signal Hub in action:

```bash
# Search for authentication logic
signal-hub search "user login and authentication"

# Find database models
signal-hub search "database models and schemas"

# Look for API endpoints
signal-hub search "REST API routes"
```

### 4. Check Routing Decisions

See how Signal Hub routes queries:

```bash
# Simple query → Haiku (fast & cheap)
signal-hub search "list all functions" --explain-routing

# Complex query → Sonnet/Opus
signal-hub search "analyze security vulnerabilities in auth" --explain-routing
```

## ⚙️ Configuration Basics

The generated `signal-hub.yaml` includes:

```yaml
# Indexing settings
indexing:
  include_patterns:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"

# Routing rules
routing:
  default_model: haiku
  rules:
    - name: length_based
      thresholds:
        haiku: 500
        sonnet: 2000

# Caching
caching:
  enabled: true
  similarity_threshold: 0.85
```

## 📊 Monitor Usage

Check your usage and costs:

```bash
# View current session stats
signal-hub stats

# See cost breakdown
signal-hub costs --period today
```

Example output:
```
📊 Signal Hub Usage Stats
========================
Queries: 47
Cache Hits: 19 (40.4%)
Models Used:
  - Haiku: 31 (66%)
  - Sonnet: 14 (30%)
  - Opus: 2 (4%)
Estimated Savings: $3.42 (72%)
```

## 🔥 Pro Tips

### 1. Use Manual Escalation
When you need a better model, use inline hints:
```
"@opus Debug this complex concurrency issue"
```

### 2. Leverage Caching
Similar queries use cached results:
```
"What does the User model do?"  # First query
"Explain the User model"        # Cache hit!
```

### 3. Optimize Indexing
For large codebases, index incrementally:
```bash
# Index only Python files first
signal-hub index . --include "**/*.py"

# Add JavaScript later
signal-hub index . --include "**/*.js" --update
```

## 🚧 Troubleshooting

### Index Not Found
```
Error: No index found for current directory
```
**Solution**: Run `signal-hub index .` first

### API Key Issues
```
Error: OpenAI API key not configured
```
**Solution**: Set `OPENAI_API_KEY` environment variable

### Connection Failed
```
Error: Failed to connect to MCP server
```
**Solution**: Ensure `signal-hub serve` is running

## 🎉 What's Next?

Congratulations! You've got Signal Hub running. Here's what to explore next:

1. 📖 [First Project Tutorial](first-project.md) - Detailed walkthrough
2. 🧠 [Core Concepts](concepts.md) - Understand how it works
3. ⚙️ [Configuration Guide](../user-guide/configuration.md) - Customize settings
4. 🚀 [Advanced Features](../user-guide/routing.md) - Optimize routing

## 💡 Quick Commands Reference

| Command | Description |
|---------|-------------|
| `signal-hub init` | Initialize configuration |
| `signal-hub index .` | Index current directory |
| `signal-hub serve` | Start MCP server |
| `signal-hub search "query"` | Test search |
| `signal-hub stats` | View usage statistics |
| `signal-hub costs` | Check cost breakdown |
| `signal-hub update` | Update index |
| `signal-hub config` | Manage configuration |

Happy coding with unlimited context! 🚀