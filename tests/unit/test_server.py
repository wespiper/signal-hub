"""Unit tests for Signal Hub MCP server."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from signal_hub.config.settings import Settings, ServerSettings, Edition
from signal_hub.core.server import SignalHubServer
from signal_hub.core.protocol import MessageType, ErrorCode
from signal_hub.core.features import Feature


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Settings(
        edition=Edition.BASIC,
        early_access=False,
        server=ServerSettings(host="localhost", port=3333),
        plugins_enabled=["basic_router", "basic_cache"]
    )
    return settings


@pytest.fixture
def server(mock_settings):
    """Create server instance for testing."""
    with patch('signal_hub.core.server.setup_logging'):
        server = SignalHubServer(mock_settings)
        return server


class TestSignalHubServer:
    """Test SignalHubServer class."""
    
    def test_server_initialization(self, server, mock_settings):
        """Test server initializes correctly."""
        assert server.settings == mock_settings
        assert server.protocol is not None
        assert server.plugin_manager is not None
        assert server.tool_registry is not None
        assert not server._running
    
    def test_get_server_name(self, mock_settings):
        """Test server name generation."""
        # Basic edition
        assert mock_settings.get_server_name() == "Signal Hub Basic"
        
        # Pro edition
        mock_settings.edition = Edition.PRO
        assert mock_settings.get_server_name() == "Signal Hub Pro"
        
        # Early access
        mock_settings.early_access = True
        assert mock_settings.get_server_name() == "Signal Hub (Early Access)"
    
    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test initialization handler."""
        message = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "TestClient",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await server._handle_initialize(message)
        
        assert response["id"] == "1"
        assert "result" in response
        assert "serverInfo" in response["result"]
        assert "capabilities" in response["result"]
        assert response["result"]["serverInfo"]["name"] == "Signal Hub Basic"
    
    @pytest.mark.asyncio
    async def test_handle_list_tools(self, server):
        """Test list tools handler."""
        message = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list"
        }
        
        response = await server._handle_list_tools(message)
        
        assert response["id"] == "2"
        assert "result" in response
        assert "tools" in response["result"]
        assert isinstance(response["result"]["tools"], list)
        
        # Should have at least the get_server_info tool
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "get_server_info" in tool_names
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_success(self, server):
        """Test successful tool call."""
        message = {
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/call",
            "params": {
                "name": "get_server_info",
                "arguments": {}
            }
        }
        
        response = await server._handle_call_tool(message)
        
        assert response["id"] == "3"
        assert "result" in response
        assert "content" in response["result"]
        
        # Check content is properly formatted
        content = response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        
        # Parse the result
        result_data = json.loads(content[0]["text"])
        assert "version" in result_data
        assert "edition" in result_data
        assert result_data["edition"] == "basic"
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_not_found(self, server):
        """Test calling non-existent tool."""
        message = {
            "jsonrpc": "2.0",
            "id": "4",
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool",
                "arguments": {}
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            await server._handle_call_tool(message)
        
        # Should raise ProtocolError with TOOL_NOT_FOUND
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_handle_shutdown(self, server):
        """Test shutdown handler."""
        message = {
            "jsonrpc": "2.0",
            "id": "5",
            "method": "shutdown"
        }
        
        server._running = True
        response = await server._handle_shutdown(message)
        
        assert response["id"] == "5"
        assert "result" in response
        assert response["result"]["status"] == "shutting_down"
        
        # Give shutdown time to execute
        await asyncio.sleep(0.1)
        assert not server._running
    
    def test_load_plugins_basic(self, mock_settings):
        """Test plugin loading for basic edition."""
        with patch('signal_hub.core.server.setup_logging'):
            server = SignalHubServer(mock_settings)
            
            # Should load basic plugins
            plugins = server.plugin_manager.get_plugins()
            assert len(plugins) > 0
    
    def test_load_plugins_early_access(self, mock_settings):
        """Test plugin loading with early access."""
        mock_settings.early_access = True
        mock_settings.plugins_enabled = [
            "basic_router", 
            "basic_cache",
            "ml_router",
            "advanced_analytics"
        ]
        
        with patch('signal_hub.core.server.setup_logging'):
            server = SignalHubServer(mock_settings)
            
            # Should load all plugins in early access
            plugins = server.plugin_manager.get_plugins()
            assert len(plugins) >= 2  # At least basic plugins


class TestProtocolHandlers:
    """Test protocol message handlers."""
    
    @pytest.mark.asyncio
    async def test_protocol_handler_registration(self, server):
        """Test protocol handlers are registered."""
        handlers = server.protocol._handlers
        
        assert MessageType.INITIALIZE.value in handlers
        assert MessageType.LIST_TOOLS.value in handlers
        assert MessageType.CALL_TOOL.value in handlers
        assert MessageType.SHUTDOWN.value in handlers
        assert MessageType.PING.value in handlers  # Default handler
    
    @pytest.mark.asyncio
    async def test_ping_handler(self, server):
        """Test ping handler."""
        message = {
            "jsonrpc": "2.0",
            "id": "ping-1",
            "method": "ping"
        }
        
        # Process through protocol
        response_json = await server.protocol.process_message(json.dumps(message))
        response = json.loads(response_json)
        
        assert response["id"] == "ping-1"
        assert response["result"]["method"] == "pong"
        assert "timestamp" in response["result"]


class TestServerLifecycle:
    """Test server lifecycle methods."""
    
    @pytest.mark.asyncio
    async def test_shutdown_sequence(self, server):
        """Test graceful shutdown sequence."""
        server._running = True
        
        # Mock plugin manager
        server.plugin_manager.shutdown = AsyncMock()
        
        await server._shutdown()
        
        assert not server._running
        assert server._shutdown_event.is_set()
        server.plugin_manager.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_server(self, server, mock_settings):
        """Test health check server startup."""
        mock_settings.server.health_check_enabled = True
        
        # Mock aiohttp
        with patch('signal_hub.core.server.web') as mock_web:
            mock_app = MagicMock()
            mock_web.Application.return_value = mock_app
            mock_runner = AsyncMock()
            mock_web.AppRunner.return_value = mock_runner
            
            # Start health server task
            health_task = asyncio.create_task(server.start_health_server())
            
            # Give it time to start
            await asyncio.sleep(0.1)
            
            # Trigger shutdown
            server._shutdown_event.set()
            
            # Wait for completion
            await health_task
            
            # Verify setup was called
            mock_runner.setup.assert_called_once()
            mock_runner.cleanup.assert_called_once()


# Import asyncio for the tests
import asyncio