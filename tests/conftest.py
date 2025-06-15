"""Pytest configuration and shared fixtures for Signal Hub tests."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace for tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    return workspace


@pytest.fixture
def mock_env(monkeypatch) -> None:
    """Mock environment variables for testing."""
    # Set test environment
    monkeypatch.setenv("SIGNAL_HUB_ENV", "test")
    monkeypatch.setenv("SIGNAL_HUB_LOG_LEVEL", "DEBUG")
    
    # Mock API keys
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")


@pytest.fixture
def edition_basic(monkeypatch) -> None:
    """Configure Signal Hub Basic edition for testing."""
    monkeypatch.setenv("SIGNAL_HUB_EDITION", "basic")
    monkeypatch.setenv("SIGNAL_HUB_EARLY_ACCESS", "false")


@pytest.fixture
def edition_pro(monkeypatch) -> None:
    """Configure Signal Hub Pro edition for testing."""
    monkeypatch.setenv("SIGNAL_HUB_EDITION", "pro")
    monkeypatch.setenv("SIGNAL_HUB_LICENSE_KEY", "test-pro-license")


@pytest.fixture
def early_access(monkeypatch) -> None:
    """Enable early access mode for testing all features."""
    monkeypatch.setenv("SIGNAL_HUB_EARLY_ACCESS", "true")


@pytest.fixture
def sample_code_file(tmp_workspace: Path) -> Path:
    """Create a sample Python file for testing."""
    code_file = tmp_workspace / "sample.py"
    code_file.write_text('''
def hello_world():
    """Say hello to the world."""
    return "Hello, World!"


class Calculator:
    """Simple calculator class."""
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
''')
    return code_file


@pytest.fixture
def sample_config(tmp_workspace: Path) -> Path:
    """Create a sample configuration file."""
    config_file = tmp_workspace / "config.yaml"
    config_file.write_text('''
edition: basic

server:
  host: localhost
  port: 3333
  name: "Signal Hub Test"

vector_store:
  type: chromadb
  path: ":memory:"

embeddings:
  provider: openai
  model: text-embedding-3-small
  dimension: 1536

cache:
  enabled: true
  ttl_seconds: 300
''')
    return config_file


# Async fixtures
@pytest_asyncio.fixture
async def mock_mcp_server():
    """Mock MCP server for testing."""
    from signal_hub.core.server import SignalHubServer
    
    # This will be implemented when we create the server
    # For now, return None as placeholder
    yield None


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture and assert on logs."""
    with caplog.at_level("DEBUG"):
        yield caplog


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than usual to run"
    )
    config.addinivalue_line(
        "markers", "pro: Tests for Pro edition features"
    )
    config.addinivalue_line(
        "markers", "enterprise: Tests for Enterprise edition features"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)