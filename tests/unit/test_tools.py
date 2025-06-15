"""Unit tests for tool registry."""

import pytest
from typing import Dict, Any

from signal_hub.core.tools import (
    Tool, ToolParameter, ToolInputType, ToolRegistry, create_tool
)
from signal_hub.core.features import Feature
from signal_hub.core.plugins import PluginManager


class TestToolParameter:
    """Test ToolParameter class."""
    
    def test_parameter_creation(self):
        """Test creating a tool parameter."""
        param = ToolParameter(
            name="query",
            type=ToolInputType.STRING,
            description="Search query",
            required=True
        )
        
        assert param.name == "query"
        assert param.type == ToolInputType.STRING
        assert param.description == "Search query"
        assert param.required is True
        assert param.default is None
    
    def test_parameter_to_schema(self):
        """Test converting parameter to JSON schema."""
        param = ToolParameter(
            name="limit",
            type=ToolInputType.NUMBER,
            description="Result limit",
            required=False,
            default=10
        )
        
        schema = param.to_schema()
        assert schema["type"] == "number"
        assert schema["description"] == "Result limit"
        assert schema["default"] == 10


class TestTool:
    """Test Tool class."""
    
    @pytest.fixture
    def sample_tool(self):
        """Create a sample tool."""
        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": f"Searched for: {params.get('query')}"}
        
        return Tool(
            name="search",
            description="Search for code",
            handler=handler,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolInputType.STRING,
                    description="Search query",
                    required=True
                )
            ],
            required_feature=Feature.BASIC_SEARCH
        )
    
    def test_tool_creation(self, sample_tool):
        """Test creating a tool."""
        assert sample_tool.name == "search"
        assert sample_tool.description == "Search for code"
        assert len(sample_tool.parameters) == 1
        assert sample_tool.required_feature == Feature.BASIC_SEARCH
    
    def test_tool_to_mcp_format(self, sample_tool):
        """Test converting tool to MCP format."""
        mcp_format = sample_tool.to_mcp_format()
        
        assert mcp_format["name"] == "search"
        assert mcp_format["description"] == "Search for code"
        assert "inputSchema" in mcp_format
        assert mcp_format["inputSchema"]["type"] == "object"
        assert "query" in mcp_format["inputSchema"]["properties"]
        assert "query" in mcp_format["inputSchema"]["required"]
    
    def test_tool_availability_with_feature(self, sample_tool, edition_basic):
        """Test tool availability based on features."""
        # Basic edition should have BASIC_SEARCH enabled
        assert sample_tool.is_available() is True
    
    def test_tool_availability_without_feature(self, sample_tool, edition_basic):
        """Test tool unavailable when feature disabled."""
        # Change to a Pro feature
        sample_tool.required_feature = Feature.ML_ROUTING
        assert sample_tool.is_available() is False
    
    def test_tool_availability_no_feature(self, sample_tool):
        """Test tool always available when no feature required."""
        sample_tool.required_feature = None
        assert sample_tool.is_available() is True


class TestToolRegistry:
    """Test ToolRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a tool registry."""
        return ToolRegistry()
    
    def test_registry_initialization(self, registry):
        """Test registry initializes with basic tools."""
        tools = registry.list_tools()
        tool_names = [t.name for t in tools]
        
        # Should have basic tools
        assert "get_server_info" in tool_names
        assert len(tools) > 0
    
    def test_register_tool(self, registry):
        """Test registering a custom tool."""
        async def custom_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"custom": True}
        
        tool = Tool(
            name="custom_tool",
            description="Custom tool",
            handler=custom_handler
        )
        
        registry.register(tool)
        
        # Verify tool is registered
        retrieved = registry.get_tool("custom_tool")
        assert retrieved is not None
        assert retrieved.name == "custom_tool"
    
    def test_unregister_tool(self, registry):
        """Test unregistering a tool."""
        # First register a tool
        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {}
        
        tool = Tool(name="temp_tool", description="Temp", handler=handler)
        registry.register(tool)
        
        # Verify it exists
        assert registry.get_tool("temp_tool") is not None
        
        # Unregister
        registry.unregister("temp_tool")
        
        # Verify it's gone
        assert registry.get_tool("temp_tool") is None
    
    def test_get_tool_not_found(self, registry):
        """Test getting non-existent tool."""
        tool = registry.get_tool("non_existent")
        assert tool is None
    
    def test_list_tools_filters_by_availability(self, registry, edition_basic):
        """Test list_tools only returns available tools."""
        # Add a Pro-only tool
        async def pro_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"pro": True}
        
        pro_tool = Tool(
            name="pro_tool",
            description="Pro feature",
            handler=pro_handler,
            required_feature=Feature.ML_ROUTING  # Pro feature
        )
        
        registry.register(pro_tool)
        
        # List tools should not include pro tool in basic edition
        tools = registry.list_tools()
        tool_names = [t.name for t in tools]
        assert "pro_tool" not in tool_names
    
    def test_get_mcp_tool_list(self, registry):
        """Test getting tool list in MCP format."""
        mcp_tools = registry.get_mcp_tool_list()
        
        assert isinstance(mcp_tools, list)
        assert len(mcp_tools) > 0
        
        # Check format
        for tool in mcp_tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self, registry):
        """Test successful tool execution."""
        result = await registry.execute_tool("get_server_info", {})
        
        assert "version" in result
        assert "edition" in result
        assert "available_tools" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, registry):
        """Test executing non-existent tool."""
        with pytest.raises(ValueError) as exc_info:
            await registry.execute_tool("non_existent", {})
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_tool_missing_params(self, registry):
        """Test executing tool with missing required params."""
        # Register a tool with required params
        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"query": params["query"]}
        
        tool = Tool(
            name="test_params",
            description="Test params",
            handler=handler,
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolInputType.STRING,
                    description="Required query",
                    required=True
                )
            ]
        )
        
        registry.register(tool)
        
        # Try to execute without params
        with pytest.raises(ValueError) as exc_info:
            await registry.execute_tool("test_params", {})
        
        assert "Missing required parameter: query" in str(exc_info.value)


class TestCreateToolDecorator:
    """Test create_tool decorator."""
    
    def test_create_tool_decorator(self):
        """Test creating a tool with decorator."""
        @create_tool(
            name="decorated_tool",
            description="Tool created with decorator",
            required_feature=Feature.BASIC_SEARCH
        )
        async def my_tool(query: str, limit: int = 10) -> Dict[str, Any]:
            return {"query": query, "limit": limit}
        
        # Should return a Tool instance
        assert isinstance(my_tool, Tool)
        assert my_tool.name == "decorated_tool"
        assert my_tool.description == "Tool created with decorator"
        assert my_tool.required_feature == Feature.BASIC_SEARCH
        
        # Should have extracted parameters
        assert len(my_tool.parameters) == 2
        
        # Query should be required
        query_param = next(p for p in my_tool.parameters if p.name == "query")
        assert query_param.required is True
        assert query_param.type == ToolInputType.STRING
        
        # Limit should be optional with default
        limit_param = next(p for p in my_tool.parameters if p.name == "limit")
        assert limit_param.required is False
        assert limit_param.type == ToolInputType.NUMBER
        assert limit_param.default == 10