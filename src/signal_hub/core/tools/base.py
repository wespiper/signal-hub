"""Base tool interface for MCP."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Base class for MCP tools."""
    
    def __init__(self):
        """Initialize tool."""
        self._validate_metadata()
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Get tool name."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Get tool description."""
        pass
        
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        pass
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass
        
    def _validate_metadata(self):
        """Validate tool metadata."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")
        if not isinstance(self.input_schema, dict):
            raise ValueError("Tool input_schema must be a dictionary")
            
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters against schema.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        required = self.input_schema.get("required", [])
        properties = self.input_schema.get("properties", {})
        
        # Check required parameters
        for param in required:
            if param not in params:
                return f"Missing required parameter: {param}"
                
        # Check parameter types
        for param, value in params.items():
            if param in properties:
                prop_schema = properties[param]
                expected_type = prop_schema.get("type")
                
                if expected_type:
                    if not self._check_type(value, expected_type):
                        return f"Parameter '{param}' must be of type {expected_type}"
                        
        return None
        
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
            
        return True
        
    async def __call__(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make tool callable."""
        return await self.execute(params)


class ToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool):
        """Register a tool.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
            
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        
    def unregister(self, name: str):
        """Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")
            
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self.tools.get(name)
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools.
        
        Returns:
            List of tool metadata
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
        
    async def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }
            
        # Validate parameters
        error = tool.validate_params(params)
        if error:
            return {
                "success": False,
                "error": error
            }
            
        try:
            # Execute tool
            result = await tool.execute(params)
            
            # Ensure result has success field
            if "success" not in result:
                result["success"] = True
                
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return {
                "success": False,
                "error": str(e)
            }