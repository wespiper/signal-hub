# Signal Hub Development Setup Guide

Welcome to Signal Hub! This guide will help you set up your development environment quickly and efficiently.

## 🚀 Quick Start (5 minutes)

### Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Git** - [Download](https://git-scm.com/downloads)

### One-Command Setup

#### macOS/Linux

```bash
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
./scripts/setup.sh
```

#### Windows (PowerShell as Administrator)

```powershell
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
.\scripts\setup.ps1
```

#### Windows (WSL2 - Recommended)

```bash
# In WSL2 terminal
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
./scripts/setup.sh
```

## 📋 Manual Setup

If you prefer manual setup or the automated script fails:

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment

```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### 4. Start Services

```bash
cd docker
docker compose up -d chromadb redis postgres
cd ..
```

### 5. Verify Setup

```bash
./scripts/validate.sh
```

## 🔧 Configuration

### Required API Keys

Edit `config/.env` and add your API keys:

```env
OPENAI_API_KEY=your-openai-api-key      # For embeddings
ANTHROPIC_API_KEY=your-anthropic-api-key # For model routing
```

Get API keys from:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

### Optional Configuration

- `SIGNAL_HUB_EARLY_ACCESS=true` - Enable all Pro features for testing
- `SIGNAL_HUB_DEBUG=true` - Enable debug logging
- `SIGNAL_HUB_PORT=3333` - Change server port

## 🐳 Docker Services

Signal Hub uses Docker for external services:

| Service | Port | Purpose |
|---------|------|---------|
| ChromaDB | 8000 | Vector database for embeddings |
| Redis | 6379 | Caching layer |
| PostgreSQL | 5432 | Future pgvector support |
| Prometheus | 9090 | Metrics (optional) |
| Grafana | 3000 | Dashboards (optional) |

### Service Management

```bash
# Start all services
cd docker && docker compose up -d

# Start only required services
cd docker && docker compose up -d chromadb redis

# Start with monitoring
cd docker && docker compose --profile monitoring up -d

# Stop all services
cd docker && docker compose down

# View logs
cd docker && docker compose logs -f
```

## 🧪 Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific tests
poetry run pytest tests/unit/test_server.py

# Run with coverage
make test-coverage

# Run only unit tests
poetry run pytest tests/unit/

# Run only integration tests
poetry run pytest tests/integration/
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# All quality checks
make quality
```

### Starting the Server

```bash
# Development mode
make dev

# Or directly
signal-hub serve --config config/dev.yaml

# With early access features
SIGNAL_HUB_EARLY_ACCESS=true signal-hub serve
```

## 🛠️ Common Tasks

### Add a New Dependency

```bash
poetry add package-name
poetry add --group dev package-name  # Dev dependency
```

### Update Dependencies

```bash
poetry update
```

### Reset Environment

```bash
# Clean everything
make clean

# Reinstall
poetry install
```

### Database Migrations (Future)

```bash
# When we add PostgreSQL migrations
poetry run alembic upgrade head
```

## 🐛 Troubleshooting

### Poetry Issues

```bash
# Update Poetry
poetry self update

# Clear cache
poetry cache clear pypi --all

# Reinstall dependencies
poetry install --no-cache
```

### Docker Issues

```bash
# Reset Docker volumes
cd docker
docker compose down -v
docker compose up -d

# Check service health
docker compose ps
docker compose logs chromadb
```

### Port Conflicts

If you get port conflicts, update `docker/.env`:

```env
CHROMADB_PORT=8001
REDIS_PORT=6380
POSTGRES_PORT=5433
```

### API Key Issues

Ensure your API keys are valid:

```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

## 🎯 IDE Setup

### VS Code

Install recommended extensions:

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
```

Settings (`.vscode/settings.json`):

```json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "editor.formatOnSave": true
}
```

### PyCharm

1. Open project
2. Configure Poetry interpreter:
   - Settings → Project → Python Interpreter
   - Add Interpreter → Poetry Environment
3. Enable pytest as test runner
4. Configure code style to use Black

## 📚 Next Steps

1. Read the [Architecture Guide](../planning/architecture/system-design.md)
2. Review [Sprint 1 Tickets](../planning/tickets/sprint-01/README.md)
3. Check out [Contributing Guidelines](../CONTRIBUTING.md)
4. Join our [Discord Community](#) (Coming soon!)

## 🆘 Getting Help

- **Documentation**: Check `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/wespiper/signal-hub/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wespiper/signal-hub/discussions)

Happy coding! 🎉