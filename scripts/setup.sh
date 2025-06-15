#!/bin/bash

# Signal Hub Development Environment Setup Script
# Supports macOS and Linux

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if running on supported OS
check_os() {
    print_step "Checking operating system..."
    
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     OS_TYPE=Linux;;
        Darwin*)    OS_TYPE=Mac;;
        *)          
            print_error "Unsupported OS: ${OS}"
            echo "This script supports macOS and Linux only."
            echo "Windows users should use WSL2 or setup.ps1"
            exit 1
            ;;
    esac
    
    print_success "Detected ${OS_TYPE}"
}

# Check Python version
check_python() {
    print_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.11 or higher"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION"
}

# Check and install Poetry
check_poetry() {
    print_step "Checking Poetry installation..."
    
    if ! command -v poetry &> /dev/null; then
        print_warning "Poetry is not installed. Installing..."
        curl -sSL https://install.python-poetry.org | python3 -
        
        # Add Poetry to PATH
        export PATH="$HOME/.local/bin:$PATH"
        
        # Add to shell profile
        if [[ "$SHELL" == *"zsh"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        fi
        
        print_success "Poetry installed"
    else
        POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
        print_success "Poetry $POETRY_VERSION"
    fi
}

# Check Docker
check_docker() {
    print_step "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker Desktop"
        exit 1
    fi
    
    print_success "Docker is running"
    
    # Check docker-compose
    if command -v docker-compose &> /dev/null; then
        print_success "docker-compose is available"
    elif docker compose version &> /dev/null; then
        print_success "docker compose is available"
    else
        print_error "docker-compose is not available"
        exit 1
    fi
}

# Setup environment file
setup_env() {
    print_step "Setting up environment configuration..."
    
    if [ ! -f "config/.env" ]; then
        cp config/.env.example config/.env
        print_warning "Created config/.env from template"
        print_warning "Please update API keys in config/.env"
    else
        print_success "config/.env already exists"
    fi
    
    # Create dev config if not exists
    if [ ! -f "config/dev.yaml" ]; then
        cat > config/dev.yaml << EOF
# Signal Hub Development Configuration
edition: basic
early_access: true
env: development
debug: true

server:
  host: localhost
  port: 3333
  name: "Signal Hub Dev"

logging:
  level: INFO
  format: rich

vector_store:
  type: chromadb
  host: localhost
  port: 8000

embeddings:
  provider: openai
  model: text-embedding-3-small

cache:
  enabled: true
  ttl: 3600

models:
  default_provider: anthropic
  haiku_threshold: 0.3
  sonnet_threshold: 0.7
EOF
        print_success "Created config/dev.yaml"
    else
        print_success "config/dev.yaml already exists"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_step "Installing Python dependencies..."
    
    poetry install
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p data/cache
    mkdir -p data/logs
    mkdir -p data/embeddings
    
    print_success "Directories created"
}

# Start Docker services
start_services() {
    print_step "Starting Docker services..."
    
    # Use docker compose or docker-compose
    if docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    cd docker
    $DOCKER_COMPOSE up -d chromadb redis postgres
    cd ..
    
    print_success "Services started"
    
    # Wait for services to be ready
    print_step "Waiting for services to be ready..."
    sleep 5
    
    # Check ChromaDB
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        print_success "ChromaDB is ready"
    else
        print_warning "ChromaDB is not responding yet"
    fi
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_warning "Redis is not responding yet"
    fi
}

# Run validation
validate_setup() {
    print_step "Validating setup..."
    
    ./scripts/validate.sh
}

# Main setup flow
main() {
    echo "🚀 Signal Hub Development Environment Setup"
    echo "=========================================="
    echo
    
    # Change to project root
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR/.."
    
    # Run checks and setup
    check_os
    check_python
    check_poetry
    check_docker
    setup_env
    install_dependencies
    create_directories
    start_services
    
    echo
    echo "✅ Setup complete!"
    echo
    echo "Next steps:"
    echo "1. Update API keys in config/.env"
    echo "2. Run './scripts/validate.sh' to verify setup"
    echo "3. Run 'make test' to run tests"
    echo "4. Run 'signal-hub serve' to start the server"
    echo
    echo "For monitoring (optional):"
    echo "  cd docker && docker compose --profile monitoring up -d"
    echo
}

# Run main function
main