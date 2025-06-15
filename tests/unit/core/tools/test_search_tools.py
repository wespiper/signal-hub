"""Tests for MCP search tools."""

import pytest
from typing import Dict, Any

from signal_hub.core.tools import SearchCodeTool, ExplainCodeTool, FindSimilarTool, GetContextTool
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery
from signal_hub.storage.interfaces import VectorStore


class MockSearchEngine:
    """Mock search engine for testing."""
    
    def __init__(self):
        self.last_query = None
        
    async def search(self, query: SearchQuery):
        """Mock search."""
        self.last_query = query
        
        # Return mock results based on query
        from signal_hub.retrieval.search import SearchResult
        
        if "error" in query.text:
            raise Exception("Search error")
            
        return [
            SearchResult(
                id="1",
                text="def authenticate_user(username, password):\n    # Auth logic here",
                score=0.95,
                metadata={
                    "file_path": "auth.py",
                    "function_name": "authenticate_user",
                    "start_line": 10,
                    "end_line": 15
                }
            ),
            SearchResult(
                id="2",
                text="class UserAuth:\n    def __init__(self):\n        pass",
                score=0.85,
                metadata={
                    "file_path": "auth.py",
                    "class_name": "UserAuth",
                    "start_line": 20,
                    "end_line": 25
                }
            )
        ]


class TestSearchCodeTool:
    """Test search_code MCP tool."""
    
    @pytest.fixture
    def tool(self):
        """Create search tool with mock engine."""
        search_engine = MockSearchEngine()
        return SearchCodeTool(search_engine)
        
    def test_tool_metadata(self, tool):
        """Test tool metadata."""
        assert tool.name == "search_code"
        assert "search" in tool.description.lower()
        assert "query" in tool.input_schema["required"]
        
    @pytest.mark.asyncio
    async def test_basic_search(self, tool):
        """Test basic code search."""
        params = {
            "query": "user authentication",
            "limit": 5
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) > 0
        
        # Check result structure
        first_result = result["results"][0]
        assert "text" in first_result
        assert "location" in first_result
        assert "score" in first_result
        
    @pytest.mark.asyncio
    async def test_search_with_filters(self, tool):
        """Test search with language filter."""
        params = {
            "query": "authentication",
            "language": "python",
            "limit": 10
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert tool.search_engine.last_query.language_filter == "python"
        
    @pytest.mark.asyncio
    async def test_search_with_file_pattern(self, tool):
        """Test search with file pattern."""
        params = {
            "query": "test functions",
            "file_pattern": "*test*.py"
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert tool.search_engine.last_query.file_pattern == "*test*.py"
        
    @pytest.mark.asyncio
    async def test_search_error_handling(self, tool):
        """Test error handling."""
        params = {
            "query": "error"  # Triggers mock error
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert "error" in result
        
    @pytest.mark.asyncio
    async def test_missing_query(self, tool):
        """Test missing required parameter."""
        params = {}
        
        result = await tool.execute(params)
        
        assert result["success"] is False
        assert "query" in result["error"].lower()


class TestExplainCodeTool:
    """Test explain_code MCP tool."""
    
    @pytest.fixture
    def tool(self):
        """Create explain tool with mocks."""
        search_engine = MockSearchEngine()
        from signal_hub.retrieval.assembly import ContextAssembler
        assembler = ContextAssembler()
        return ExplainCodeTool(search_engine, assembler)
        
    def test_tool_metadata(self, tool):
        """Test tool metadata."""
        assert tool.name == "explain_code"
        assert "explain" in tool.description.lower()
        assert "file_path" in tool.input_schema["required"]
        
    @pytest.mark.asyncio
    async def test_explain_file(self, tool):
        """Test explaining a file."""
        params = {
            "file_path": "auth.py"
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert "explanation" in result
        assert "context" in result
        
    @pytest.mark.asyncio
    async def test_explain_function(self, tool):
        """Test explaining a specific function."""
        params = {
            "file_path": "auth.py",
            "function_name": "authenticate_user"
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        # Should search for specific function
        assert "authenticate_user" in tool.search_engine.last_query.text
        
    @pytest.mark.asyncio
    async def test_include_dependencies(self, tool):
        """Test including dependencies."""
        params = {
            "file_path": "auth.py",
            "include_dependencies": True
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert "dependencies" in result or "context" in result


class TestFindSimilarTool:
    """Test find_similar MCP tool."""
    
    @pytest.fixture
    def tool(self):
        """Create find similar tool."""
        search_engine = MockSearchEngine()
        return FindSimilarTool(search_engine)
        
    def test_tool_metadata(self, tool):
        """Test tool metadata."""
        assert tool.name == "find_similar"
        assert "similar" in tool.description.lower()
        assert "code_snippet" in tool.input_schema["required"]
        
    @pytest.mark.asyncio
    async def test_find_similar_code(self, tool):
        """Test finding similar code."""
        params = {
            "code_snippet": "def authenticate(user, pass):\n    return check_password(user, pass)",
            "limit": 5
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert "results" in result
        
        # Should use code snippet as query
        assert "authenticate" in tool.search_engine.last_query.text


class TestGetContextTool:
    """Test get_context MCP tool."""
    
    @pytest.fixture
    def tool(self):
        """Create context tool."""
        search_engine = MockSearchEngine()
        from signal_hub.retrieval.assembly import ContextAssembler
        assembler = ContextAssembler()
        return GetContextTool(search_engine, assembler)
        
    def test_tool_metadata(self, tool):
        """Test tool metadata."""
        assert tool.name == "get_context"
        assert "context" in tool.description.lower()
        assert "task_description" in tool.input_schema["required"]
        
    @pytest.mark.asyncio
    async def test_get_context_for_task(self, tool):
        """Test getting context for a task."""
        params = {
            "task_description": "I need to implement user authentication with JWT tokens"
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        assert "context" in result
        assert "summary" in result
        
    @pytest.mark.asyncio
    async def test_get_context_with_current_file(self, tool):
        """Test getting context with current file context."""
        params = {
            "task_description": "Add password hashing to this authentication class",
            "current_file": "auth/user_auth.py"
        }
        
        result = await tool.execute(params)
        
        assert result["success"] is True
        # Should include current file in search
        query = tool.search_engine.last_query
        assert query is not None