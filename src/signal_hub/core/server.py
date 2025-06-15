"""Signal Hub MCP Server implementation."""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import signal
import sys
from pathlib import Path
from contextlib import asynccontextmanager

try:
    import mcp.server
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool as MCPTool, TextContent
except ImportError:
    # MCP not installed yet - we'll handle this gracefully
    Server = None
    stdio_server = None
    MCPTool = None
    TextContent = None

from signal_hub.config.settings import Settings
from signal_hub.config.loader import load_config, validate_config
from signal_hub.core.protocol import ProtocolHandler, MessageType, ErrorCode, ProtocolError
from signal_hub.core.tools import ToolRegistry
from signal_hub.core.plugins import PluginManager
from signal_hub.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


class SignalHubServer:
    """Main Signal Hub MCP server implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.protocol = ProtocolHandler()
        self.plugin_manager = PluginManager()
        self.tool_registry = ToolRegistry(self.plugin_manager)
        self._running = False
        self._server: Optional[Server] = None
        self._shutdown_event = asyncio.Event()
        
        # Setup logging
        setup_logging(
            level=settings.logging.level,
            log_file=settings.logging.file,
            json_format=settings.logging.format == "json",
            rich_console=settings.logging.rich_console
        )
        
        # Load plugins
        self._load_plugins()
        
        # Register protocol handlers
        self._register_handlers()
    
    def _load_plugins(self):
        """Load enabled plugins."""
        logger.info("Loading plugins...")
        
        # Load basic plugins (always enabled for Signal Hub Basic)
        if "basic_router" in self.settings.plugins_enabled:
            from signal_hub.plugins.pro_example import BasicModelRouter
            self.plugin_manager.register(BasicModelRouter())
        
        if "basic_cache" in self.settings.plugins_enabled:
            from signal_hub.plugins.pro_example import BasicCacheStrategy
            self.plugin_manager.register(BasicCacheStrategy())
        
        # Load pro plugins if enabled
        if self.settings.early_access or self.settings.edition.value != "basic":
            if "ml_router" in self.settings.plugins_enabled:
                from signal_hub.plugins.pro_example import MLModelRouter
                self.plugin_manager.register(MLModelRouter())
            
            if "advanced_analytics" in self.settings.plugins_enabled:
                from signal_hub.plugins.pro_example import AdvancedAnalyticsProvider
                self.plugin_manager.register(AdvancedAnalyticsProvider())
        
        logger.info(f"Loaded {len(self.plugin_manager.get_plugins())} plugins")
    
    def _register_handlers(self):
        """Register protocol message handlers."""
        self.protocol.register_handler(MessageType.INITIALIZE, self._handle_initialize)
        self.protocol.register_handler(MessageType.LIST_TOOLS, self._handle_list_tools)
        self.protocol.register_handler(MessageType.CALL_TOOL, self._handle_call_tool)
        self.protocol.register_handler(MessageType.SHUTDOWN, self._handle_shutdown)
    
    async def _handle_initialize(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        logger.info("Handling initialize request")
        
        # Get client info
        client_info = message.get("params", {}).get("clientInfo", {})
        logger.info(f"Client: {client_info.get('name', 'Unknown')} {client_info.get('version', '')}")
        
        # Create response
        server_info = {
            "name": self.settings.get_server_name(),
            "version": "0.1.0",
            "protocolVersion": "2024-11-05",
        }
        
        capabilities = {
            "tools": {
                "listTools": True,
                "callTool": True
            },
            "prompts": {
                "listPrompts": False,
                "getPrompt": False
            },
            "resources": {
                "listResources": False,
                "readResource": False
            },
            "logging": {
                "setLevel": False
            }
        }
        
        return self.protocol.create_response(
            message.get("id"),
            {
                "serverInfo": server_info,
                "capabilities": capabilities
            }
        )
    
    async def _handle_list_tools(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request."""
        logger.debug("Listing available tools")
        
        tools = self.tool_registry.get_mcp_tool_list()
        logger.info(f"Available tools: {len(tools)}")
        
        return self.protocol.create_response(
            message.get("id"),
            {"tools": tools}
        )
    
    async def _handle_call_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        params = message.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Calling tool: {tool_name}")
        
        try:
            # Execute tool
            result = await self.tool_registry.execute_tool(tool_name, arguments)
            
            # Format response
            if isinstance(result, dict):
                content = [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            else:
                content = [TextContent(
                    type="text",
                    text=str(result)
                )]
            
            return self.protocol.create_response(
                message.get("id"),
                {"content": content}
            )
            
        except ValueError as e:
            raise ProtocolError(ErrorCode.TOOL_NOT_FOUND, str(e))
        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_name}")
            raise ProtocolError(
                ErrorCode.TOOL_ERROR,
                f"Tool execution failed: {str(e)}",
                {"tool": tool_name, "error": str(e)}
            )
    
    async def _handle_shutdown(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shutdown request."""
        logger.info("Received shutdown request")
        
        # Schedule shutdown
        asyncio.create_task(self._shutdown())
        
        return self.protocol.create_response(
            message.get("id"),
            {"status": "shutting_down"}
        )
    
    async def _shutdown(self):
        """Perform graceful shutdown."""
        logger.info("Starting graceful shutdown...")
        
        # Stop accepting new requests
        self._running = False
        
        # Notify plugins
        await self.plugin_manager.shutdown()
        
        # Set shutdown event
        self._shutdown_event.set()
        
        logger.info("Shutdown complete")
    
    async def start_stdio_server(self):
        """Start the MCP server using stdio transport."""
        logger.info(f"Starting {self.settings.get_server_name()}")
        
        # Create MCP server instance
        self._server = Server(self.settings.get_server_name())
        
        # Register handlers with MCP server
        @self._server.list_tools()
        async def list_tools() -> List[MCPTool]:
            """List available tools."""
            tools = []
            for tool in self.tool_registry.list_tools():
                mcp_tool = MCPTool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.to_mcp_format()["inputSchema"]
                )
                tools.append(mcp_tool)
            return tools
        
        @self._server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Execute a tool."""
            try:
                result = await self.tool_registry.execute_tool(name, arguments or {})
                
                if isinstance(result, dict):
                    text = json.dumps(result, indent=2)
                else:
                    text = str(result)
                
                return [TextContent(type="text", text=text)]
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
        
        # Setup signal handlers
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            asyncio.create_task(self._shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run server
        self._running = True
        logger.info("Server ready to accept connections")
        
        async with stdio_server() as (read_stream, write_stream):
            try:
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options()
                )
            except Exception as e:
                logger.error(f"Server error: {e}")
                raise
    
    async def start_health_server(self):
        """Start HTTP health check endpoint if enabled."""
        if not self.settings.server.health_check_enabled:
            return
        
        from aiohttp import web
        
        async def health_check(request):
            """Health check endpoint."""
            status = {
                "status": "healthy" if self._running else "shutting_down",
                "timestamp": datetime.utcnow().isoformat(),
                "edition": self.settings.edition.value,
                "version": "0.1.0"
            }
            return web.json_response(status)
        
        app = web.Application()
        app.router.add_get(self.settings.server.health_check_path, health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(
            runner,
            self.settings.server.host,
            self.settings.server.port + 1  # Health check on next port
        )
        
        await site.start()
        logger.info(
            f"Health check endpoint available at "
            f"http://{self.settings.server.host}:{self.settings.server.port + 1}"
            f"{self.settings.server.health_check_path}"
        )
        
        # Keep health server running until shutdown
        await self._shutdown_event.wait()
        await runner.cleanup()
    
    async def run(self):
        """Run the server."""
        try:
            # Validate configuration
            validate_config(self.settings)
            
            # Start health check server
            health_task = asyncio.create_task(self.start_health_server())
            
            # Start MCP server
            await self.start_stdio_server()
            
            # Wait for health server to complete
            await health_task
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.exception(f"Server failed: {e}")
            raise
        finally:
            await self._shutdown()


def create_server(
    config_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None
) -> SignalHubServer:
    """
    Create a Signal Hub server instance.
    
    Args:
        config_path: Optional configuration file path
        host: Optional host override
        port: Optional port override
        
    Returns:
        Server instance
    """
    # Load configuration
    overrides = {}
    if host:
        overrides["server"] = {"host": host}
    if port:
        overrides.setdefault("server", {})["port"] = port
    
    settings = load_config(
        Path(config_path) if config_path else None,
        overrides
    )
    
    return SignalHubServer(settings)


async def run_server(
    config_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None
):
    """
    Run the Signal Hub server.
    
    Args:
        config_path: Optional configuration file path
        host: Optional host override
        port: Optional port override
    """
    server = create_server(config_path, host, port)
    await server.run()