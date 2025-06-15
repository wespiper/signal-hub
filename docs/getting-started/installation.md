# Installation Guide

This guide will help you install Signal Hub on your system. Signal Hub supports macOS, Linux, and Windows.

## System Requirements

Before installing Signal Hub, ensure your system meets these requirements:

- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB for Signal Hub + space for vector embeddings
- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10+

## Quick Installation

### Using pip (Recommended)

The easiest way to install Signal Hub is via pip:

```bash
pip install signal-hub
```

### Using Poetry

If you prefer Poetry for dependency management:

```bash
poetry add signal-hub
```

### Using Docker

For a containerized setup:

```bash
docker pull signalhub/signal-hub:latest
docker run -it signalhub/signal-hub:latest
```

## Platform-Specific Instructions

### macOS

=== "Homebrew"

    ```bash
    # Install Python 3.11+ if needed
    brew install python@3.11
    
    # Install Signal Hub
    pip3 install signal-hub
    ```

=== "Manual"

    ```bash
    # Install Python from python.org
    # Then install Signal Hub
    python3 -m pip install signal-hub
    ```

### Linux

=== "Ubuntu/Debian"

    ```bash
    # Install Python and dependencies
    sudo apt update
    sudo apt install python3.11 python3-pip python3-venv
    
    # Install Signal Hub
    pip3 install signal-hub
    ```

=== "Fedora/RHEL"

    ```bash
    # Install Python and dependencies
    sudo dnf install python3.11 python3-pip
    
    # Install Signal Hub
    pip3 install signal-hub
    ```

=== "Arch"

    ```bash
    # Install Python
    sudo pacman -S python python-pip
    
    # Install Signal Hub
    pip install signal-hub
    ```

### Windows

=== "Command Prompt"

    ```cmd
    # Install Python from python.org first
    # Then install Signal Hub
    py -m pip install signal-hub
    ```

=== "PowerShell"

    ```powershell
    # Install Python from Microsoft Store or python.org
    # Then install Signal Hub
    python -m pip install signal-hub
    ```

=== "WSL2"

    ```bash
    # Follow Linux instructions within WSL2
    sudo apt update
    sudo apt install python3.11 python3-pip
    pip3 install signal-hub
    ```

## Development Installation

For contributing or development work:

### 1. Clone the Repository

```bash
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub
```

### 2. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies

```bash
poetry install --with dev
```

### 4. Activate Virtual Environment

```bash
poetry shell
```

## Post-Installation Setup

### 1. Verify Installation

```bash
signal-hub --version
```

Expected output:
```
Signal Hub v0.1.0
```

### 2. Initialize Configuration

```bash
signal-hub init
```

This creates a default configuration file at `~/.signal-hub/config.yaml`

### 3. Set API Keys

Signal Hub needs API keys for embeddings:

```bash
# Option 1: Environment variable
export OPENAI_API_KEY="your-api-key-here"

# Option 2: Configuration file
signal-hub config set openai.api_key "your-api-key-here"
```

### 4. Test Installation

```bash
# Run a simple test
signal-hub test

# Expected output:
✅ Python version: 3.11.0
✅ Signal Hub installed
✅ Configuration loaded
✅ API key configured
✅ Ready to index!
```

## Docker Installation (Advanced)

### Using Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  signal-hub:
    image: signalhub/signal-hub:latest
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8080:8080"
  
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - ./chroma:/chroma/chroma
    ports:
      - "8000:8000"
```

Start the services:

```bash
docker-compose up -d
```

## Troubleshooting Installation

### Python Version Issues

If you get a Python version error:

```bash
# Check your Python version
python --version

# Install Python 3.11+ using pyenv
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

### Permission Errors

On macOS/Linux, if you get permission errors:

```bash
# Use --user flag
pip install --user signal-hub

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install signal-hub
```

### SSL Certificate Errors

If you encounter SSL errors:

```bash
# Upgrade certificates
pip install --upgrade certifi

# Or disable SSL (not recommended)
pip install --trusted-host pypi.org signal-hub
```

## Next Steps

Now that Signal Hub is installed:

1. 📖 Continue to the [Quick Start Guide](quick-start.md)
2. 🎯 Set up your [First Project](first-project.md)
3. 🧠 Learn about [Core Concepts](concepts.md)

## Getting Help

If you encounter issues:

- 💬 Join our [Discord Server](https://discord.gg/signalhub)
- 🐛 Check [Common Issues](../troubleshooting/common-issues.md)
- 📧 Email support@signalhub.ai