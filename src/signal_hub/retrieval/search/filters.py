"""Metadata filtering for search results."""

import re
from typing import Dict, Any, List, Union, Optional


class MetadataFilter:
    """Filter search results based on metadata."""
    
    def matches(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches all filters.
        
        Args:
            metadata: Result metadata
            filters: Filter criteria
            
        Returns:
            True if all filters match
        """
        if not filters:
            return True
            
        for key, filter_value in filters.items():
            if not self._matches_single(metadata.get(key), filter_value):
                return False
                
        return True
        
    def _matches_single(self, value: Any, filter_value: Any) -> bool:
        """Check if a single value matches filter."""
        if value is None:
            return False
            
        # Handle different filter types
        if isinstance(filter_value, dict):
            return self._matches_complex(value, filter_value)
        elif isinstance(filter_value, list):
            # OR operation - value must match any in list
            return value in filter_value
        elif isinstance(filter_value, str) and filter_value.startswith("~"):
            # Regex match
            pattern = filter_value[1:]
            return bool(re.match(pattern, str(value)))
        else:
            # Exact match
            return value == filter_value
            
    def _matches_complex(self, value: Any, filter_dict: Dict[str, Any]) -> bool:
        """Handle complex filter operations."""
        for op, op_value in filter_dict.items():
            if op == "$gt":
                if not (value > op_value):
                    return False
            elif op == "$gte":
                if not (value >= op_value):
                    return False
            elif op == "$lt":
                if not (value < op_value):
                    return False
            elif op == "$lte":
                if not (value <= op_value):
                    return False
            elif op == "$ne":
                if value == op_value:
                    return False
            elif op == "$in":
                if value not in op_value:
                    return False
            elif op == "$nin":
                if value in op_value:
                    return False
            elif op == "$exists":
                exists = value is not None
                if exists != op_value:
                    return False
            elif op == "$regex":
                if not re.match(op_value, str(value)):
                    return False
                    
        return True


class QueryParser:
    """Parse natural language queries to extract filters."""
    
    def parse(self, query_text: str) -> Dict[str, Any]:
        """Extract filters from natural language query.
        
        Args:
            query_text: Natural language query
            
        Returns:
            Dictionary of extracted filters
        """
        filters = {}
        
        # Language detection
        language = self._detect_language(query_text)
        if language:
            filters["language"] = language
            
        # Type detection
        chunk_type = self._detect_type(query_text)
        if chunk_type:
            filters["chunk_type"] = chunk_type
            
        # File pattern detection
        file_pattern = self._detect_file_pattern(query_text)
        if file_pattern:
            filters["file_pattern"] = file_pattern
            
        return filters
        
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect programming language mentioned in query."""
        language_patterns = {
            "python": r"\b(python|py)\b",
            "javascript": r"\b(javascript|js|node)\b",
            "typescript": r"\b(typescript|ts)\b",
            "java": r"\b(java)\b",
            "go": r"\b(go|golang)\b",
            "rust": r"\b(rust)\b",
            "c++": r"\b(c\+\+|cpp)\b",
            "c#": r"\b(c#|csharp)\b",
            "ruby": r"\b(ruby)\b",
            "php": r"\b(php)\b",
        }
        
        text_lower = text.lower()
        for lang, pattern in language_patterns.items():
            if re.search(pattern, text_lower):
                return lang
                
        return None
        
    def _detect_type(self, text: str) -> Optional[str]:
        """Detect chunk type mentioned in query."""
        type_patterns = {
            "function": r"\b(function|method|func)\b",
            "class": r"\b(class|classes)\b",
            "import": r"\b(import|require|include)\b",
            "documentation": r"\b(doc|documentation|comment)\b",
        }
        
        text_lower = text.lower()
        for chunk_type, pattern in type_patterns.items():
            if re.search(pattern, text_lower):
                return chunk_type
                
        return None
        
    def _detect_file_pattern(self, text: str) -> Optional[str]:
        """Detect file pattern in query."""
        # Look for patterns like "in *.py files" or "from test files"
        patterns = [
            r"in\s+(\*\.\w+)\s+files?",
            r"from\s+(\*\.\w+)\s+files?",
            r"\.(\w+)\s+files?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1).startswith("*."):
                    return match.group(1)
                else:
                    return f"*.{match.group(1)}"
                    
        # Check for test files
        if re.search(r"\b(test|spec)\s+files?\b", text, re.IGNORECASE):
            return "*test*"
            
        return None