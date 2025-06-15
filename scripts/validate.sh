#!/bin/bash

# Signal Hub Environment Validation Script
# Checks that all dependencies and services are properly configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "-------------------"
}

# System Requirements
check_system() {
    print_header "System Requirements"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" = "3.11" ]; then
            check_pass "Python $PYTHON_VERSION installed"
        else
            check_fail "Python $PYTHON_VERSION installed (3.11+ required)"
        fi
    else
        check_fail "Python not installed"
    fi
    
    # Check Poetry
    if command -v poetry &> /dev/null; then
        POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
        check_pass "Poetry $POETRY_VERSION installed"
    else
        check_fail "Poetry not installed"
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            check_pass "Docker is running"
        else
            check_fail "Docker daemon not running"
        fi
    else
        check_fail "Docker not installed"
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        check_pass "Git $GIT_VERSION installed"
    else
        check_fail "Git not installed"
    fi
    
    echo
}

# Python Environment
check_python_env() {
    print_header "Python Environment"
    
    # Check if in project directory
    if [ -f "pyproject.toml" ]; then
        check_pass "In Signal Hub project directory"
    else
        check_fail "Not in Signal Hub project directory"
        return
    fi
    
    # Check virtual environment
    if poetry env info --path &> /dev/null; then
        check_pass "Poetry virtual environment exists"
        
        # Check dependencies
        if poetry check &> /dev/null; then
            check_pass "Poetry dependencies satisfied"
        else
            check_fail "Poetry dependencies not satisfied"
        fi
    else
        check_fail "Poetry virtual environment not created"
    fi
    
    # Check if signal-hub command is available
    if poetry run which signal-hub &> /dev/null; then
        check_pass "signal-hub CLI installed"
    else
        check_fail "signal-hub CLI not installed"
    fi
    
    echo
}

# Configuration Files
check_config() {
    print_header "Configuration Files"
    
    # Check .env file
    if [ -f "config/.env" ]; then
        check_pass "config/.env exists"
        
        # Check for required API keys
        source config/.env
        
        if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key" ]; then
            check_pass "OPENAI_API_KEY configured"
        else
            check_warn "OPENAI_API_KEY not configured (required for embeddings)"
        fi
        
        if [ -n "$ANTHROPIC_API_KEY" ] && [ "$ANTHROPIC_API_KEY" != "your-anthropic-api-key" ]; then
            check_pass "ANTHROPIC_API_KEY configured"
        else
            check_warn "ANTHROPIC_API_KEY not configured (required for model routing)"
        fi
    else
        check_fail "config/.env not found"
    fi
    
    # Check dev.yaml
    if [ -f "config/dev.yaml" ]; then
        check_pass "config/dev.yaml exists"
    else
        check_fail "config/dev.yaml not found"
    fi
    
    echo
}

# Docker Services
check_services() {
    print_header "Docker Services"
    
    # Check ChromaDB
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
        check_pass "ChromaDB is accessible at localhost:8000"
    else
        check_fail "ChromaDB not accessible at localhost:8000"
        check_warn "Run: cd docker && docker compose up -d chromadb"
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null && redis-cli ping > /dev/null 2>&1; then
        check_pass "Redis is accessible at localhost:6379"
    else
        check_fail "Redis not accessible at localhost:6379"
        check_warn "Run: cd docker && docker compose up -d redis"
    fi
    
    # Check PostgreSQL
    if command -v psql &> /dev/null && PGPASSWORD=signalhub psql -h localhost -U signalhub -d signalhub -c "SELECT 1" > /dev/null 2>&1; then
        check_pass "PostgreSQL is accessible at localhost:5432"
    else
        check_warn "PostgreSQL not accessible (optional for development)"
    fi
    
    echo
}

# Directory Structure
check_directories() {
    print_header "Directory Structure"
    
    # Check required directories
    DIRS=("data" "data/cache" "data/logs" "data/embeddings")
    for dir in "${DIRS[@]}"; do
        if [ -d "$dir" ]; then
            check_pass "Directory $dir exists"
        else
            check_fail "Directory $dir missing"
        fi
    done
    
    echo
}

# Development Tools
check_dev_tools() {
    print_header "Development Tools"
    
    # Check make
    if command -v make &> /dev/null; then
        check_pass "make is available"
    else
        check_warn "make not installed (optional but recommended)"
    fi
    
    # Check pre-commit
    if poetry run which pre-commit &> /dev/null; then
        check_pass "pre-commit installed"
        
        # Check if hooks are installed
        if [ -f ".git/hooks/pre-commit" ]; then
            check_pass "pre-commit hooks installed"
        else
            check_warn "pre-commit hooks not installed"
            check_warn "Run: poetry run pre-commit install"
        fi
    else
        check_warn "pre-commit not installed (recommended)"
    fi
    
    echo
}

# Summary
print_summary() {
    echo "=================================="
    echo -e "${BLUE}Validation Summary${NC}"
    echo "=================================="
    echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"
    echo
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ Environment is ready!${NC}"
        echo
        echo "You can now run:"
        echo "  - 'make test' to run tests"
        echo "  - 'signal-hub serve' to start the server"
        echo "  - 'make dev' to start development server"
    else
        echo -e "${RED}❌ Environment needs attention${NC}"
        echo
        echo "Please fix the failed checks above."
        echo "Run './scripts/setup.sh' to set up missing components."
    fi
}

# Main
main() {
    echo "🔍 Signal Hub Environment Validation"
    echo "===================================="
    echo
    
    # Change to project root
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR/.."
    
    # Run all checks
    check_system
    check_python_env
    check_config
    check_services
    check_directories
    check_dev_tools
    
    # Print summary
    print_summary
}

# Run validation
main