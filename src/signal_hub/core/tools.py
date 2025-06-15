"""Tool registry for Signal Hub MCP server."""

from typing import Dict, Any, List, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from enum import Enum
import inspect

from signal_hub.core.features import Feature, require_feature, is_feature_enabled
from signal_hub.core.plugins import Plugin, PluginManager
from signal_hub.utils.logging import get_logger

logger = get_logger(__name__)


class ToolInputType(str, Enum):
    """Tool input parameter types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: ToolInputType
    description: str
    required: bool = True
    default: Any = None
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format."""
        schema = {
            "type": self.type.value,
            "description": self.description
        }
        
        if not self.required and self.default is not None:
            schema["default"] = self.default
        
        return schema


@dataclass
class Tool:
    """MCP tool definition."""
    name: str
    description: str
    handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    parameters: List[ToolParameter] = field(default_factory=list)
    required_feature: Optional[Feature] = None
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        tool_def = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add parameters
        for param in self.parameters:
            tool_def["inputSchema"]["properties"][param.name] = param.to_schema()
            if param.required:
                tool_def["inputSchema"]["required"].append(param.name)
        
        return tool_def
    
    def is_available(self) -> bool:
        """Check if tool is available based on feature flags."""
        if self.required_feature:
            return is_feature_enabled(self.required_feature)
        return True


class ToolRegistry:
    """Registry for MCP tools with plugin support."""
    
    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        self._tools: Dict[str, Tool] = {}
        self._plugin_manager = plugin_manager
        self._register_basic_tools()
        
        # Register plugin tools if available
        if plugin_manager:
            self._register_plugin_tools()
    
    def _register_basic_tools(self):
        """Register basic Signal Hub tools."""
        # These will be implemented in Sprint 2, but we'll add placeholders
        
        @require_feature(Feature.BASIC_SEARCH)
        async def search_codebase(params: Dict[str, Any]) -> Dict[str, Any]:
            """Search the indexed codebase."""
            query = params.get("query", "")
            limit = params.get("limit", 10)
            
            # Placeholder implementation
            return {
                "status": "not_implemented",
                "message": "Search will be implemented in Sprint 2",
                "query": query,
                "limit": limit
            }
        
        self.register(Tool(
            name="search_codebase",
            description="Search the indexed codebase for relevant code",
            handler=search_codebase,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolInputType.STRING,
                    description="Search query",
                    required=True
                ),
                ToolParameter(
                    name="limit",
                    type=ToolInputType.NUMBER,
                    description="Maximum number of results",
                    required=False,
                    default=10
                )
            ],
            required_feature=Feature.BASIC_SEARCH
        ))
        
        @require_feature(Feature.BASIC_SEARCH)
        async def explain_code(params: Dict[str, Any]) -> Dict[str, Any]:
            """Explain code functionality."""
            file_path = params.get("file_path", "")
            
            return {
                "status": "not_implemented",
                "message": "Code explanation will be implemented in Sprint 2",
                "file_path": file_path
            }
        
        self.register(Tool(
            name="explain_code",
            description="Get explanation of code functionality",
            handler=explain_code,
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ToolInputType.STRING,
                    description="Path to file to explain",
                    required=True
                )
            ],
            required_feature=Feature.BASIC_SEARCH
        ))
        
        # System tool - always available
        async def get_server_info(params: Dict[str, Any]) -> Dict[str, Any]:
            """Get Signal Hub server information."""
            from signal_hub import get_version_string
            from signal_hub.core.features import get_edition
            
            edition = get_edition()
            available_tools = [
                tool.name for tool in self._tools.values()
                if tool.is_available()
            ]
            
            return {
                "version": get_version_string(),
                "edition": edition.value,
                "available_tools": available_tools,
                "tool_count": len(available_tools)
            }
        
        self.register(Tool(
            name="get_server_info",
            description="Get information about the Signal Hub server",
            handler=get_server_info,
            parameters=[]
        ))
    
    def _register_plugin_tools(self):
        """Register tools from plugins."""
        if not self._plugin_manager:
            return
        
        for plugin in self._plugin_manager.get_plugins():
            if hasattr(plugin, 'get_tools'):
                plugin_tools = plugin.get_tools()
                for tool in plugin_tools:
                    logger.info(f"Registering tool from plugin: {tool.name}")
                    self.register(tool)
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")
        
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool if found and available, None otherwise
        """
        tool = self._tools.get(name)
        if tool and tool.is_available():
            return tool
        return None
    
    def list_tools(self) -> List[Tool]:
        """
        List all available tools.
        
        Returns:
            List of available tools
        """
        return [
            tool for tool in self._tools.values()
            if tool.is_available()
        ]
    
    def get_mcp_tool_list(self) -> List[Dict[str, Any]]:
        """
        Get tool list in MCP format.
        
        Returns:
            List of tools in MCP format
        """
        return [tool.to_mcp_format() for tool in self.list_tools()]
    
    async def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found or not available
            Exception: If tool execution fails
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found or not available: {name}")
        
        # Validate required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        # Execute tool
        logger.info(f"Executing tool: {name}")
        try:
            result = await tool.handler(params)
            logger.debug(f"Tool {name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            raise


def create_tool(
    name: str,
    description: str,
    required_feature: Optional[Feature] = None
) -> Callable:
    """
    Decorator to create a tool from a function.
    
    Args:
        name: Tool name
        description: Tool description
        required_feature: Optional required feature
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Tool:
        # Extract parameters from function signature
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "params":
                continue  # Skip the params dict itself
            
            # Try to infer type from annotation
            param_type = ToolInputType.STRING  # Default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = ToolInputType.NUMBER
                elif param.annotation == bool:
                    param_type = ToolInputType.BOOLEAN
                elif param.annotation == list:
                    param_type = ToolInputType.ARRAY
                elif param.annotation == dict:
                    param_type = ToolInputType.OBJECT
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            ))
        
        return Tool(
            name=name,
            description=description,
            handler=func,
            parameters=parameters,
            required_feature=required_feature
        )
    
    return decorator