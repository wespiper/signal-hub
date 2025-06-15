"""Context assembler implementation."""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

from signal_hub.retrieval.assembly.models import (
    AssemblyConfig,
    AssembledContext,
    ContextSection,
    CodeRelationship,
    RelationshipType
)
from signal_hub.retrieval.search import SearchResult

logger = logging.getLogger(__name__)


class ContextAssembler:
    """Assembles coherent context from search results."""
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """Initialize context assembler.
        
        Args:
            config: Assembly configuration
        """
        self.config = config or AssemblyConfig()
        self.config.validate()
        
    def assemble(
        self,
        search_results: List[SearchResult],
        query: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> AssembledContext:
        """Assemble context from search results.
        
        Args:
            search_results: Results from semantic search
            query: Original search query
            additional_context: Optional additional context
            
        Returns:
            Assembled context ready for Claude
        """
        if not search_results:
            return AssembledContext(
                sections=[],
                relationships=[],
                query=query,
                token_count=0,
                format_style=self.config.format_style
            )
            
        # Filter by minimum score
        filtered_results = [
            r for r in search_results 
            if r.score >= self.config.min_score_threshold
        ]
        
        # Deduplicate results
        deduped_results = self._deduplicate(filtered_results)
        
        # Group by file if configured
        if self.config.group_by_file:
            grouped_results = self._group_by_file(deduped_results)
        else:
            grouped_results = {"": deduped_results}
            
        # Create sections
        sections = []
        for file_path, results in grouped_results.items():
            file_sections = self._create_sections(results, file_path)
            sections.extend(file_sections)
            
        # Order sections
        ordered_sections = self._order_sections(sections)
        
        # Apply token limit
        final_sections = self._apply_token_limit(ordered_sections)
        
        # Extract relationships if configured
        relationships = []
        if self.config.preserve_relationships:
            relationships = self._extract_relationships(final_sections)
            
        # Generate summary
        summary = self._generate_summary(final_sections, query)
        
        # Calculate total tokens
        token_count = sum(s.token_estimate for s in final_sections)
        
        return AssembledContext(
            sections=final_sections,
            relationships=relationships,
            query=query,
            token_count=token_count,
            format_style=self.config.format_style,
            summary=summary,
            metadata=additional_context or {}
        )
        
    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate or near-duplicate results."""
        if not results:
            return results
            
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Create content signature
            sig = self._get_content_signature(result.text)
            
            # Check similarity with seen content
            is_duplicate = False
            for seen_sig in seen_content:
                similarity = self._calculate_similarity(sig, seen_sig)
                if similarity >= self.config.dedup_threshold:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                unique_results.append(result)
                seen_content.add(sig)
                
        return unique_results
        
    def _group_by_file(self, results: List[SearchResult]) -> Dict[str, List[SearchResult]]:
        """Group results by source file."""
        grouped = defaultdict(list)
        
        for result in results:
            file_path = result.metadata.get("file_path", "unknown")
            grouped[file_path].append(result)
            
        return dict(grouped)
        
    def _create_sections(self, results: List[SearchResult], file_path: str) -> List[ContextSection]:
        """Create context sections from results."""
        sections = []
        
        # Handle imports specially if configured
        if self.config.include_imports:
            import_results = [r for r in results 
                            if r.metadata.get("chunk_type") == "module" 
                            or "import" in r.metadata.get("contains", "")]
            
            if import_results:
                # Merge import sections
                import_section = self._merge_imports(import_results, file_path)
                if import_section:
                    sections.append(import_section)
                    
                # Remove from main results
                results = [r for r in results if r not in import_results]
                
        # Create sections for remaining results
        for result in results:
            section = ContextSection(
                content=result.text,
                source_file=file_path or result.metadata.get("file_path", "unknown"),
                start_line=result.metadata.get("start_line", 0),
                end_line=result.metadata.get("end_line", 0),
                content_type=result.metadata.get("chunk_type", "code"),
                score=result.score,
                metadata=result.metadata,
                title=self._generate_section_title(result)
            )
            sections.append(section)
            
        return sections
        
    def _merge_imports(self, import_results: List[SearchResult], file_path: str) -> Optional[ContextSection]:
        """Merge import sections into a single section."""
        if not import_results:
            return None
            
        # Sort by line number
        sorted_results = sorted(
            import_results,
            key=lambda r: r.metadata.get("start_line", 0)
        )
        
        # Merge content
        merged_content = []
        seen_imports = set()
        
        for result in sorted_results:
            lines = result.text.strip().split('\n')
            for line in lines:
                if line.strip() and line not in seen_imports:
                    merged_content.append(line)
                    seen_imports.add(line)
                    
        if not merged_content:
            return None
            
        return ContextSection(
            content='\n'.join(merged_content),
            source_file=file_path,
            start_line=sorted_results[0].metadata.get("start_line", 1),
            end_line=sorted_results[-1].metadata.get("end_line", len(merged_content)),
            content_type="imports",
            score=max(r.score for r in sorted_results),
            metadata={"merged_from": len(sorted_results)},
            title="Imports and Dependencies"
        )
        
    def _order_sections(self, sections: List[ContextSection]) -> List[ContextSection]:
        """Order sections for optimal context."""
        if not sections:
            return sections
            
        # Separate by type
        imports = []
        definitions = []  # classes, functions
        implementations = []  # methods, blocks
        other = []
        
        for section in sections:
            content_type = section.content_type.lower()
            
            if content_type in ["imports", "module"]:
                imports.append(section)
            elif content_type in ["class", "function"]:
                definitions.append(section)
            elif content_type in ["method", "block"]:
                implementations.append(section)
            else:
                other.append(section)
                
        # Sort each group by score
        imports.sort(key=lambda s: s.score, reverse=True)
        definitions.sort(key=lambda s: s.score, reverse=True)
        implementations.sort(key=lambda s: s.score, reverse=True)
        other.sort(key=lambda s: s.score, reverse=True)
        
        # Combine in logical order
        ordered = []
        
        # Imports first
        ordered.extend(imports)
        
        # Then definitions (prioritized if configured)
        if self.config.prioritize_definitions:
            ordered.extend(definitions)
            ordered.extend(implementations)
        else:
            # Interleave by score
            all_code = definitions + implementations
            all_code.sort(key=lambda s: s.score, reverse=True)
            ordered.extend(all_code)
            
        # Finally other content
        ordered.extend(other)
        
        return ordered
        
    def _apply_token_limit(self, sections: List[ContextSection]) -> List[ContextSection]:
        """Apply token limit to sections."""
        if not sections:
            return sections
            
        final_sections = []
        total_tokens = 0
        
        for section in sections:
            section_tokens = section.token_estimate
            
            # Check if adding this section would exceed limit
            if total_tokens + section_tokens > self.config.max_tokens:
                # Try to add partial section
                remaining_tokens = self.config.max_tokens - total_tokens
                if remaining_tokens > 100:  # Minimum useful size
                    # Truncate content
                    truncated_content = self._truncate_to_tokens(
                        section.content,
                        remaining_tokens
                    )
                    
                    truncated_section = ContextSection(
                        content=truncated_content + "\n... (truncated)",
                        source_file=section.source_file,
                        start_line=section.start_line,
                        end_line=section.end_line,
                        content_type=section.content_type,
                        score=section.score,
                        metadata={**section.metadata, "truncated": True},
                        title=section.title
                    )
                    final_sections.append(truncated_section)
                    
                break
            else:
                final_sections.append(section)
                total_tokens += section_tokens
                
        return final_sections
        
    def _extract_relationships(self, sections: List[ContextSection]) -> List[CodeRelationship]:
        """Extract relationships between code entities."""
        relationships = []
        
        # Build entity map
        entities = {}
        for section in sections:
            # Extract function/class names
            if section.content_type == "function":
                name = section.metadata.get("function_name")
                if name:
                    entities[name] = section
            elif section.content_type == "class":
                name = section.metadata.get("class_name")
                if name:
                    entities[name] = section
                    
        # Look for relationships
        for section in sections:
            # Find function calls
            if section.content_type in ["function", "method"]:
                calls = self._find_function_calls(section.content)
                from_entity = section.metadata.get("function_name", "unknown")
                
                for called_func in calls:
                    if called_func in entities and called_func != from_entity:
                        rel = CodeRelationship(
                            from_entity=from_entity,
                            to_entity=called_func,
                            relationship_type=RelationshipType.CALLS,
                            confidence=0.9
                        )
                        relationships.append(rel)
                        
            # Find imports
            if section.content_type == "imports":
                imports = self._extract_imports(section.content)
                for module, names in imports.items():
                    for name in names:
                        if name in entities:
                            rel = CodeRelationship(
                                from_entity=section.source_file,
                                to_entity=name,
                                relationship_type=RelationshipType.IMPORTS,
                                confidence=1.0
                            )
                            relationships.append(rel)
                            
        # Filter by confidence threshold
        relationships = [
            r for r in relationships 
            if r.confidence >= self.config.relationship_confidence_threshold
        ]
        
        return relationships
        
    def _generate_summary(self, sections: List[ContextSection], query: str) -> str:
        """Generate a summary of the assembled context."""
        if not sections:
            return "No relevant code found."
            
        # Count types
        type_counts = defaultdict(int)
        for section in sections:
            type_counts[section.content_type] += 1
            
        # Get unique files
        files = set(s.source_file for s in sections)
        
        # Build summary
        parts = [f"Found {len(sections)} relevant code sections for '{query}'"]
        
        if len(files) == 1:
            parts.append(f"from {list(files)[0]}")
        else:
            parts.append(f"across {len(files)} files")
            
        # Add type breakdown
        type_parts = []
        for content_type, count in sorted(type_counts.items()):
            if count == 1:
                type_parts.append(f"1 {content_type}")
            else:
                type_parts.append(f"{count} {content_type}s")
                
        if type_parts:
            parts.append(f"including {', '.join(type_parts)}")
            
        return " ".join(parts) + "."
        
    def _generate_section_title(self, result: SearchResult) -> Optional[str]:
        """Generate a title for a section."""
        metadata = result.metadata
        
        if metadata.get("function_name"):
            return f"Function: {metadata['function_name']}"
        elif metadata.get("class_name"):
            return f"Class: {metadata['class_name']}"
        elif metadata.get("method_name"):
            class_name = metadata.get("class_name", "")
            if class_name:
                return f"Method: {class_name}.{metadata['method_name']}"
            return f"Method: {metadata['method_name']}"
        elif metadata.get("chunk_type") == "documentation":
            return "Documentation"
            
        return None
        
    def _get_content_signature(self, content: str) -> str:
        """Get a signature for content comparison."""
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', content.strip())
        
        # Take first 200 chars
        if len(normalized) > 200:
            return normalized[:200]
        return normalized
        
    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two signatures."""
        # Simple character-based similarity
        if sig1 == sig2:
            return 1.0
            
        # Calculate Jaccard similarity of character sets
        set1 = set(sig1.split())
        set2 = set(sig2.split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
        
    def _truncate_to_tokens(self, content: str, max_tokens: int) -> str:
        """Truncate content to approximately max tokens."""
        # Rough estimate: 1 token per 4 characters
        max_chars = max_tokens * 4
        
        if len(content) <= max_chars:
            return content
            
        # Try to truncate at a logical boundary
        truncated = content[:max_chars]
        
        # Look for last complete line
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.8:  # If we found a newline reasonably close
            return truncated[:last_newline]
            
        return truncated
        
    def _find_function_calls(self, content: str) -> Set[str]:
        """Find function calls in code."""
        # Simple regex-based approach
        # Matches: function_name( but not def function_name(
        pattern = r'(?<!def\s)(?<!class\s)\b(\w+)\s*\('
        
        calls = set()
        for match in re.finditer(pattern, content):
            func_name = match.group(1)
            # Filter out common built-ins and keywords
            if func_name not in {'if', 'for', 'while', 'with', 'except', 'return', 'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set'}:
                calls.add(func_name)
                
        return calls
        
    def _extract_imports(self, content: str) -> Dict[str, List[str]]:
        """Extract import statements."""
        imports = defaultdict(list)
        
        # Python imports
        # import module
        for match in re.finditer(r'^import\s+(\S+)', content, re.MULTILINE):
            imports[match.group(1)] = []
            
        # from module import names
        for match in re.finditer(r'^from\s+(\S+)\s+import\s+(.+)$', content, re.MULTILINE):
            module = match.group(1)
            names_str = match.group(2)
            
            # Parse names
            names = [n.strip() for n in names_str.split(',')]
            imports[module].extend(names)
            
        return dict(imports)