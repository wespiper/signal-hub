"""Find similar code MCP tool implementation."""

import logging
from typing import Dict, Any, List

from signal_hub.core.tools.base import Tool
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery

logger = logging.getLogger(__name__)


class FindSimilarTool(Tool):
    """MCP tool for finding similar code snippets."""
    
    def __init__(self, search_engine: SemanticSearchEngine):
        """Initialize find similar tool.
        
        Args:
            search_engine: Semantic search engine instance
        """
        self.search_engine = search_engine
        super().__init__()
        
    @property
    def name(self) -> str:
        """Get tool name."""
        return "find_similar"
        
    @property
    def description(self) -> str:
        """Get tool description."""
        return "Find code similar to a given snippet using semantic similarity"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        return {
            "type": "object",
            "properties": {
                "code_snippet": {
                    "type": "string",
                    "description": "Code snippet to find similar code for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of similar results",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "min_similarity": {
                    "type": "number",
                    "description": "Minimum similarity score (0-1)",
                    "default": 0.7,
                    "minimum": 0,
                    "maximum": 1
                },
                "language": {
                    "type": "string",
                    "description": "Filter by programming language",
                    "enum": ["python", "javascript", "typescript", "java", "go", "rust"]
                },
                "exclude_file": {
                    "type": "string",
                    "description": "File path to exclude from results"
                },
                "scope": {
                    "type": "string",
                    "description": "Search scope",
                    "enum": ["all", "same_project", "same_directory"],
                    "default": "all"
                }
            },
            "required": ["code_snippet"]
        }
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the find similar tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Similar code results
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
            code_snippet = params["code_snippet"]
            limit = params.get("limit", 10)
            min_similarity = params.get("min_similarity", 0.7)
            language = params.get("language")
            exclude_file = params.get("exclude_file")
            scope = params.get("scope", "all")
            
            # Create search query
            # Use the code snippet directly as the query for semantic search
            query = SearchQuery(
                text=code_snippet,
                k=limit * 2,  # Get more results to filter
                search_mode="semantic",  # Force semantic mode
                language_filter=language,
                min_score=min_similarity
            )
            
            # Add scope filters
            filters = {}
            if exclude_file:
                filters["file_path"] = {"$ne": exclude_file}
                
            if scope == "same_project":
                # Extract project root from exclude_file if provided
                if exclude_file and "/" in exclude_file:
                    project_root = exclude_file.split("/")[0]
                    filters["file_path"] = {"$regex": f"^{project_root}/"}
                    
            elif scope == "same_directory":
                # Extract directory from exclude_file if provided
                if exclude_file and "/" in exclude_file:
                    directory = "/".join(exclude_file.split("/")[:-1])
                    filters["file_path"] = {"$regex": f"^{directory}/"}
                    
            if filters:
                query.filters = filters
                
            # Perform similarity search
            logger.info(f"Finding similar code to snippet of {len(code_snippet)} chars")
            results = await self.search_engine.search(query)
            
            # Filter and format results
            formatted_results = []
            seen_signatures = set()
            
            for result in results:
                # Skip if below minimum similarity
                if result.score < min_similarity:
                    continue
                    
                # Create signature to detect duplicates
                sig = self._create_signature(result.text)
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                
                # Check if it's too similar to the input
                if self._is_exact_match(code_snippet, result.text):
                    continue
                    
                formatted_result = {
                    "code": result.text,
                    "similarity": result.score,
                    "location": {
                        "file": result.metadata.get("file_path", "unknown"),
                        "start_line": result.metadata.get("start_line", 0),
                        "end_line": result.metadata.get("end_line", 0)
                    },
                    "type": result.metadata.get("chunk_type", "code")
                }
                
                # Add context information
                if "function_name" in result.metadata:
                    formatted_result["function"] = result.metadata["function_name"]
                if "class_name" in result.metadata:
                    formatted_result["class"] = result.metadata["class_name"]
                    
                # Add difference analysis
                formatted_result["differences"] = self._analyze_differences(
                    code_snippet,
                    result.text
                )
                
                formatted_results.append(formatted_result)
                
                # Stop if we have enough results
                if len(formatted_results) >= limit:
                    break
                    
            # Sort by similarity
            formatted_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "success": True,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "snippet_length": len(code_snippet),
                "search_scope": scope
            }
            
        except Exception as e:
            logger.error(f"Error in find_similar tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_signature(self, code: str) -> str:
        """Create a signature for duplicate detection."""
        # Normalize whitespace and remove comments
        import re
        
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code).strip()
        
        # Take first 100 chars as signature
        return code[:100] if len(code) > 100 else code
        
    def _is_exact_match(self, snippet1: str, snippet2: str) -> bool:
        """Check if two snippets are essentially the same."""
        sig1 = self._create_signature(snippet1)
        sig2 = self._create_signature(snippet2)
        
        # Check exact match after normalization
        if sig1 == sig2:
            return True
            
        # Check if one is contained in the other (with some tolerance)
        if len(sig1) > 20 and len(sig2) > 20:
            if sig1 in sig2 or sig2 in sig1:
                return True
                
        return False
        
    def _analyze_differences(self, snippet1: str, snippet2: str) -> Dict[str, Any]:
        """Analyze differences between two code snippets."""
        lines1 = snippet1.strip().split('\n')
        lines2 = snippet2.strip().split('\n')
        
        differences = {
            "line_count_diff": len(lines2) - len(lines1),
            "common_patterns": [],
            "notable_differences": []
        }
        
        # Find common patterns
        import re
        
        # Extract function/method names
        func_pattern = r'def\s+(\w+)|function\s+(\w+)|func\s+(\w+)'
        
        funcs1 = set()
        funcs2 = set()
        
        for line in lines1:
            matches = re.findall(func_pattern, line)
            for match in matches:
                funcs1.add(next(m for m in match if m))
                
        for line in lines2:
            matches = re.findall(func_pattern, line)
            for match in matches:
                funcs2.add(next(m for m in match if m))
                
        common_funcs = funcs1 & funcs2
        if common_funcs:
            differences["common_patterns"].append(f"Functions: {', '.join(common_funcs)}")
            
        # Note major structural differences
        has_class1 = any('class ' in line for line in lines1)
        has_class2 = any('class ' in line for line in lines2)
        
        if has_class1 != has_class2:
            differences["notable_differences"].append(
                "One has class definition, other doesn't"
            )
            
        # Check for different languages
        py_keywords1 = sum(1 for line in lines1 if 'def ' in line or 'import ' in line)
        py_keywords2 = sum(1 for line in lines2 if 'def ' in line or 'import ' in line)
        js_keywords1 = sum(1 for line in lines1 if 'function ' in line or 'const ' in line)
        js_keywords2 = sum(1 for line in lines2 if 'function ' in line or 'const ' in line)
        
        if (py_keywords1 > 0) != (py_keywords2 > 0) or (js_keywords1 > 0) != (js_keywords2 > 0):
            differences["notable_differences"].append("Different programming languages")
            
        return differences