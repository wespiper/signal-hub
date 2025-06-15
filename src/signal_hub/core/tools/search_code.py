"""Search code MCP tool implementation."""

import logging
from typing import Dict, Any, List

from signal_hub.core.tools.base import Tool
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery

logger = logging.getLogger(__name__)


class SearchCodeTool(Tool):
    """MCP tool for searching code in the indexed codebase."""
    
    def __init__(self, search_engine: SemanticSearchEngine):
        """Initialize search code tool.
        
        Args:
            search_engine: Semantic search engine instance
        """
        self.search_engine = search_engine
        super().__init__()
        
    @property
    def name(self) -> str:
        """Get tool name."""
        return "search_code"
        
    @property
    def description(self) -> str:
        """Get tool description."""
        return "Search for code snippets in the indexed codebase using semantic search"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (natural language or code snippet)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "language": {
                    "type": "string",
                    "description": "Filter by programming language",
                    "enum": ["python", "javascript", "typescript", "java", "go", "rust"]
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Filter by file pattern (glob syntax)"
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum relevance score (0-1)",
                    "default": 0.5,
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "required": ["query"]
        }
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Search results
        """
        try:
            # Validate parameters
            error = self.validate_params(params)
            if error:
                return {
                    "success": False,
                    "error": error
                }
                
            # Extract parameters
            query_text = params["query"]
            limit = params.get("limit", 10)
            language = params.get("language")
            file_pattern = params.get("file_pattern")
            min_score = params.get("min_score", 0.5)
            
            # Create search query
            query = SearchQuery(
                text=query_text,
                k=limit,
                language_filter=language,
                file_pattern=file_pattern,
                min_score=min_score
            )
            
            # Perform search
            logger.info(f"Searching for: {query_text}")
            results = await self.search_engine.search(query)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "text": result.text,
                    "score": result.score,
                    "location": {
                        "file": result.metadata.get("file_path", "unknown"),
                        "start_line": result.metadata.get("start_line", 0),
                        "end_line": result.metadata.get("end_line", 0)
                    }
                }
                
                # Add optional metadata
                if "function_name" in result.metadata:
                    formatted_result["function"] = result.metadata["function_name"]
                if "class_name" in result.metadata:
                    formatted_result["class"] = result.metadata["class_name"]
                if "chunk_type" in result.metadata:
                    formatted_result["type"] = result.metadata["chunk_type"]
                    
                formatted_results.append(formatted_result)
                
            return {
                "success": True,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "query": query_text
            }
            
        except Exception as e:
            logger.error(f"Error in search_code tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }