"""Get context MCP tool implementation."""

import logging
from typing import Dict, Any, Optional, List

from signal_hub.core.tools.base import Tool
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery, ContextAssembler

logger = logging.getLogger(__name__)


class GetContextTool(Tool):
    """MCP tool for getting relevant context for a coding task."""
    
    def __init__(
        self,
        search_engine: SemanticSearchEngine,
        context_assembler: ContextAssembler
    ):
        """Initialize get context tool.
        
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
        return "get_context"
        
    @property
    def description(self) -> str:
        """Get tool description."""
        return "Get relevant code context for a specific task or question"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool inputs."""
        return {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Description of the task or question"
                },
                "current_file": {
                    "type": "string",
                    "description": "Current file being worked on (optional)"
                },
                "related_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of related files to prioritize"
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens for context",
                    "default": 4000,
                    "minimum": 1000,
                    "maximum": 16000
                },
                "include_examples": {
                    "type": "boolean",
                    "description": "Include usage examples",
                    "default": True
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Include related test files",
                    "default": False
                },
                "context_type": {
                    "type": "string",
                    "description": "Type of context needed",
                    "enum": ["implementation", "debugging", "refactoring", "documentation"],
                    "default": "implementation"
                }
            },
            "required": ["task_description"]
        }
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the get context tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Assembled context for the task
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
            task_description = params["task_description"]
            current_file = params.get("current_file")
            related_files = params.get("related_files", [])
            max_tokens = params.get("max_tokens", 4000)
            include_examples = params.get("include_examples", True)
            include_tests = params.get("include_tests", False)
            context_type = params.get("context_type", "implementation")
            
            # Build intelligent queries based on task
            queries = self._build_queries(
                task_description,
                current_file,
                related_files,
                context_type
            )
            
            # Execute searches
            all_results = []
            for query in queries:
                logger.info(f"Searching: {query.text}")
                results = await self.search_engine.search(query)
                all_results.extend(results)
                
            # Filter based on preferences
            filtered_results = self._filter_results(
                all_results,
                include_examples,
                include_tests,
                context_type
            )
            
            # Configure assembly based on context type
            assembly_config = self._get_assembly_config(context_type, max_tokens)
            
            # Assemble context
            self.context_assembler.config = assembly_config
            assembled_context = self.context_assembler.assemble(
                filtered_results,
                task_description,
                additional_context={
                    "task": task_description,
                    "current_file": current_file,
                    "related_files": related_files,
                    "context_type": context_type
                }
            )
            
            # Generate actionable summary
            summary = self._generate_actionable_summary(
                assembled_context,
                task_description,
                context_type
            )
            
            # Format for MCP response
            response = {
                "success": True,
                "context": self._format_context(assembled_context),
                "summary": summary,
                "statistics": {
                    "sections_found": len(assembled_context.sections),
                    "token_count": assembled_context.token_count,
                    "files_included": len(set(s.source_file for s in assembled_context.sections)),
                    "relationships_found": len(assembled_context.relationships)
                }
            }
            
            # Add suggestions based on context type
            suggestions = self._generate_suggestions(
                assembled_context,
                task_description,
                context_type
            )
            if suggestions:
                response["suggestions"] = suggestions
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_context tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _build_queries(
        self,
        task_description: str,
        current_file: Optional[str],
        related_files: List[str],
        context_type: str
    ) -> List[SearchQuery]:
        """Build intelligent search queries based on the task."""
        queries = []
        
        # Main task query
        main_query = SearchQuery(
            text=task_description,
            k=30,
            search_mode="hybrid"  # Use both semantic and keyword
        )
        queries.append(main_query)
        
        # Extract key terms from task
        key_terms = self._extract_key_terms(task_description)
        
        # Add specific queries based on context type
        if context_type == "implementation":
            # Look for similar implementations
            for term in key_terms[:3]:  # Top 3 terms
                impl_query = SearchQuery(
                    text=f"def {term} OR class {term} OR function {term}",
                    k=10,
                    search_mode="keyword"
                )
                queries.append(impl_query)
                
        elif context_type == "debugging":
            # Look for error handling and edge cases
            debug_query = SearchQuery(
                text="error handling exception try catch raise throw",
                k=10,
                filters={"file_path": {"$regex": "test|spec"}} if not current_file else None
            )
            queries.append(debug_query)
            
        elif context_type == "refactoring":
            # Look for patterns and best practices
            pattern_query = SearchQuery(
                text=f"pattern design {' '.join(key_terms[:2])}",
                k=10
            )
            queries.append(pattern_query)
            
        # Add current file context if provided
        if current_file:
            context_query = SearchQuery(
                text=f"related to {current_file}",
                k=15,
                filters={"file_path": {"$ne": current_file}}
            )
            queries.append(context_query)
            
        # Prioritize related files
        if related_files:
            for file in related_files[:3]:  # Limit to avoid too many queries
                file_query = SearchQuery(
                    text=task_description,
                    k=5,
                    filters={"file_path": file}
                )
                queries.append(file_query)
                
        return queries
        
    def _filter_results(
        self,
        results: List,
        include_examples: bool,
        include_tests: bool,
        context_type: str
    ) -> List:
        """Filter results based on preferences."""
        filtered = []
        
        for result in results:
            metadata = result.metadata
            file_path = metadata.get("file_path", "")
            
            # Skip tests if not requested
            if not include_tests and ("test" in file_path or "spec" in file_path):
                continue
                
            # Skip examples if not requested
            if not include_examples and "example" in file_path:
                continue
                
            # Apply context-specific filtering
            if context_type == "implementation":
                # Prefer actual implementations over docs
                if metadata.get("chunk_type") in ["function", "class", "method"]:
                    result.score *= 1.2  # Boost score
                    
            elif context_type == "debugging":
                # Prefer error handling code
                if any(term in result.text.lower() for term in ["error", "exception", "raise", "catch"]):
                    result.score *= 1.1
                    
            elif context_type == "documentation":
                # Prefer comments and docstrings
                if metadata.get("chunk_type") == "documentation":
                    result.score *= 1.3
                    
            filtered.append(result)
            
        return filtered
        
    def _get_assembly_config(self, context_type: str, max_tokens: int):
        """Get assembly configuration based on context type."""
        from signal_hub.retrieval.assembly import AssemblyConfig
        
        config = AssemblyConfig(
            max_tokens=max_tokens,
            dedup_threshold=0.8,
            min_score_threshold=0.5
        )
        
        if context_type == "implementation":
            config.prioritize_definitions = True
            config.group_by_file = True
            config.include_imports = True
            
        elif context_type == "debugging":
            config.preserve_relationships = True
            config.include_imports = True
            config.min_score_threshold = 0.4  # Include more potential issues
            
        elif context_type == "refactoring":
            config.prioritize_definitions = True
            config.preserve_relationships = True
            config.group_by_file = False  # Mix different approaches
            
        elif context_type == "documentation":
            config.group_by_file = True
            config.format_style = "markdown"
            
        return config
        
    def _format_context(self, assembled_context) -> str:
        """Format assembled context for MCP response."""
        parts = []
        
        # Group sections by file
        file_sections = {}
        for section in assembled_context.sections:
            file = section.source_file
            if file not in file_sections:
                file_sections[file] = []
            file_sections[file].append(section)
            
        # Format each file's sections
        for file, sections in file_sections.items():
            parts.append(f"\n### {file}\n")
            
            for section in sections:
                if section.title:
                    parts.append(f"#### {section.title}")
                    
                # Add line numbers for reference
                if section.start_line > 0:
                    parts.append(f"*Lines {section.start_line}-{section.end_line}*")
                    
                # Add the code
                parts.append("```")
                parts.append(section.content)
                parts.append("```\n")
                
        return "\n".join(parts)
        
    def _generate_actionable_summary(
        self,
        context,
        task_description: str,
        context_type: str
    ) -> str:
        """Generate an actionable summary for the developer."""
        parts = []
        
        # Task understanding
        parts.append(f"**Task**: {task_description}")
        
        # Key findings
        if context.sections:
            parts.append(f"\n**Found**: {len(context.sections)} relevant code sections")
            
            # Highlight most relevant
            top_sections = sorted(context.sections, key=lambda s: s.score, reverse=True)[:3]
            parts.append("\n**Most relevant**:")
            for section in top_sections:
                location = f"{section.source_file}:{section.start_line}"
                parts.append(f"- {section.title or 'Code'} at {location}")
                
        # Context-specific insights
        if context_type == "implementation":
            # Look for patterns
            functions = [s for s in context.sections if s.content_type == "function"]
            if functions:
                parts.append(f"\n**Similar implementations**: Found {len(functions)} related functions")
                
        elif context_type == "debugging":
            # Look for error patterns
            error_sections = [s for s in context.sections 
                            if any(term in s.content.lower() 
                                  for term in ["error", "exception", "raise"])]
            if error_sections:
                parts.append(f"\n**Error handling**: Found {len(error_sections)} error handling patterns")
                
        # Relationships
        if context.relationships:
            parts.append(f"\n**Dependencies**: {len(context.relationships)} code relationships identified")
            
        return "\n".join(parts)
        
    def _generate_suggestions(
        self,
        context,
        task_description: str,
        context_type: str
    ) -> Optional[List[str]]:
        """Generate actionable suggestions based on context."""
        suggestions = []
        
        if context_type == "implementation":
            # Suggest patterns found
            patterns = set()
            for section in context.sections:
                if section.content_type == "function":
                    # Extract common patterns
                    if "async def" in section.content:
                        patterns.add("Use async/await pattern")
                    if "@" in section.content:
                        patterns.add("Consider using decorators")
                        
            suggestions.extend(list(patterns)[:3])
            
        elif context_type == "debugging":
            # Suggest error handling approaches
            if any("try" in s.content for s in context.sections):
                suggestions.append("Add try-except blocks for error handling")
            if any("logging" in s.content for s in context.sections):
                suggestions.append("Add logging for better debugging")
                
        elif context_type == "refactoring":
            # Suggest refactoring patterns
            if len(context.sections) > 5:
                suggestions.append("Consider breaking into smaller functions")
            if any(s.content_type == "class" for s in context.sections):
                suggestions.append("Consider object-oriented approach")
                
        return suggestions if suggestions else None
        
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from task description."""
        import re
        
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "been", "be",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "must", "can", "need", "want", "i", "me",
            "my", "we", "our", "you", "your", "it", "its", "this", "that"
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Prioritize technical terms
        technical_terms = []
        other_terms = []
        
        for term in key_terms:
            # Common programming terms get priority
            if term in {"function", "class", "method", "api", "database", "auth",
                       "authentication", "user", "data", "model", "view", "controller",
                       "service", "repository", "handler", "manager", "factory"}:
                technical_terms.append(term)
            else:
                other_terms.append(term)
                
        # Return technical terms first, then others
        return technical_terms + other_terms