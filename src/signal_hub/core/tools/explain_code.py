"""Explain code MCP tool implementation."""

import logging
from typing import Dict, Any, Optional

from signal_hub.core.tools.base import Tool
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery, ContextAssembler

logger = logging.getLogger(__name__)


class ExplainCodeTool(Tool):
    """MCP tool for explaining code with relevant context."""
    
    def __init__(
        self,
        search_engine: SemanticSearchEngine,
        context_assembler: ContextAssembler
    ):
        """Initialize explain code tool.
        
        Args:
            search_engine: Semantic search engine instance
            context_assembler: Context assembler instance
        """
        self.search_engine = search_engine
        self.context_assembler = context_assembler
        super().__init__()
        
    @property
    def name(self) -> str:
        """Get tool name."""
        return "explain_code"
        
    @property
    def description(self) -> str:
        """Get tool description."""
        return "Explain code by providing relevant context and documentation"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to explain"
                },
                "function_name": {
                    "type": "string",
                    "description": "Specific function to explain (optional)"
                },
                "class_name": {
                    "type": "string",
                    "description": "Specific class to explain (optional)"
                },
                "line_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Line range to explain [start, end]"
                },
                "include_dependencies": {
                    "type": "boolean",
                    "description": "Include explanations of dependencies",
                    "default": True
                },
                "include_usages": {
                    "type": "boolean",
                    "description": "Include examples of how the code is used",
                    "default": True
                }
            },
            "required": ["file_path"]
        }
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the explain tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Code explanation with context
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
            file_path = params["file_path"]
            function_name = params.get("function_name")
            class_name = params.get("class_name")
            line_range = params.get("line_range")
            include_deps = params.get("include_dependencies", True)
            include_usages = params.get("include_usages", True)
            
            # Build search query
            query_parts = [f"file:{file_path}"]
            
            if function_name:
                query_parts.append(f"function:{function_name}")
            if class_name:
                query_parts.append(f"class:{class_name}")
                
            query_text = " ".join(query_parts)
            
            # Add filters
            filters = {"file_path": file_path}
            if line_range:
                filters["start_line"] = {"$gte": line_range[0]}
                filters["end_line"] = {"$lte": line_range[1]}
                
            # Search for the specific code
            query = SearchQuery(
                text=query_text,
                k=20,  # Get more results for context
                filters=filters
            )
            
            logger.info(f"Explaining code in: {file_path}")
            results = await self.search_engine.search(query)
            
            if not results:
                return {
                    "success": False,
                    "error": f"No code found in {file_path}"
                }
                
            # Find dependencies if requested
            dependency_results = []
            if include_deps:
                dep_query = await self._find_dependencies(results)
                if dep_query:
                    dependency_results = await self.search_engine.search(dep_query)
                    
            # Find usages if requested
            usage_results = []
            if include_usages:
                usage_query = await self._find_usages(results)
                if usage_query:
                    usage_results = await self.search_engine.search(usage_query)
                    
            # Assemble context
            all_results = results + dependency_results + usage_results
            assembled_context = self.context_assembler.assemble(
                all_results,
                f"Explain {file_path}",
                additional_context={
                    "target_file": file_path,
                    "function": function_name,
                    "class": class_name
                }
            )
            
            # Build explanation
            explanation = self._build_explanation(
                assembled_context,
                file_path,
                function_name,
                class_name
            )
            
            return {
                "success": True,
                "explanation": explanation,
                "context": assembled_context.to_dict(),
                "dependencies": len(dependency_results),
                "usages": len(usage_results)
            }
            
        except Exception as e:
            logger.error(f"Error in explain_code tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _find_dependencies(self, results) -> Optional[SearchQuery]:
        """Find dependencies of the code."""
        # Extract imports and function calls
        imports = set()
        calls = set()
        
        for result in results:
            metadata = result.metadata
            
            # Get imports
            if "imports" in metadata:
                for imp in metadata["imports"]:
                    imports.add(imp.get("name", ""))
                    
            # Get function calls
            if "calls" in metadata:
                calls.update(metadata["calls"])
                
        # Build dependency query
        if imports or calls:
            query_parts = []
            for imp in imports:
                if imp:
                    query_parts.append(f"class:{imp} OR function:{imp}")
            for call in calls:
                if call:
                    query_parts.append(f"function:{call}")
                    
            if query_parts:
                return SearchQuery(
                    text=" OR ".join(query_parts[:10]),  # Limit to avoid huge queries
                    k=10
                )
                
        return None
        
    async def _find_usages(self, results) -> Optional[SearchQuery]:
        """Find usages of the code."""
        # Extract entity names
        entities = set()
        
        for result in results:
            metadata = result.metadata
            
            if "function_name" in metadata:
                entities.add(metadata["function_name"])
            if "class_name" in metadata:
                entities.add(metadata["class_name"])
                
        # Build usage query
        if entities:
            query_parts = []
            for entity in entities:
                query_parts.append(f"calls:{entity} OR imports:{entity}")
                
            if query_parts:
                return SearchQuery(
                    text=" OR ".join(query_parts[:10]),  # Limit
                    k=10
                )
                
        return None
        
    def _build_explanation(
        self,
        context,
        file_path: str,
        function_name: Optional[str],
        class_name: Optional[str]
    ) -> str:
        """Build a structured explanation."""
        parts = []
        
        # Header
        if function_name:
            parts.append(f"## Function: {function_name} in {file_path}")
        elif class_name:
            parts.append(f"## Class: {class_name} in {file_path}")
        else:
            parts.append(f"## File: {file_path}")
            
        # Summary from context
        if context.summary:
            parts.append(f"\n{context.summary}")
            
        # Main code sections
        main_sections = [s for s in context.sections 
                        if s.source_file == file_path]
        
        if main_sections:
            parts.append("\n### Code:")
            for section in main_sections[:3]:  # Limit to avoid huge responses
                if section.title:
                    parts.append(f"\n#### {section.title}")
                parts.append(f"```{self._detect_language(file_path)}")
                parts.append(section.content)
                parts.append("```")
                
        # Dependencies
        dep_sections = [s for s in context.sections 
                       if s.source_file != file_path and 
                       s.content_type in ["function", "class"]]
        
        if dep_sections:
            parts.append("\n### Dependencies:")
            for section in dep_sections[:3]:
                parts.append(f"\n- **{section.title or 'Code'}** from `{section.source_file}`")
                
        # Usages
        usage_sections = [s for s in context.sections 
                         if s.source_file != file_path and 
                         any(entity in s.content for entity in [function_name, class_name] if entity)]
        
        if usage_sections:
            parts.append("\n### Used by:")
            for section in usage_sections[:3]:
                parts.append(f"\n- `{section.source_file}` at line {section.start_line}")
                
        # Relationships
        if context.relationships:
            parts.append("\n### Relationships:")
            for rel in context.relationships[:5]:
                parts.append(f"\n- {rel.from_entity} {rel.relationship_type.value} {rel.to_entity}")
                
        return "\n".join(parts)
        
    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".md": "markdown"
        }
        
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
                
        return "text"