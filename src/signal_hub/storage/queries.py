"""Query builders and utilities for vector search."""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from signal_hub.storage.models import QueryFilter


class FilterOperator(Enum):
    """Filter operators for queries."""
    
    EQ = "$eq"      # Equal
    NE = "$ne"      # Not equal
    GT = "$gt"      # Greater than
    GTE = "$gte"    # Greater than or equal
    LT = "$lt"      # Less than
    LTE = "$lte"    # Less than or equal
    IN = "$in"      # In list
    NIN = "$nin"    # Not in list
    AND = "$and"    # Logical AND
    OR = "$or"      # Logical OR


class QueryBuilder:
    """Build complex queries for vector search."""
    
    def __init__(self):
        """Initialize query builder."""
        self._where: Dict[str, Any] = {}
        self._where_document: Dict[str, Any] = {}
    
    def where(self, field: str, operator: FilterOperator, value: Any) -> "QueryBuilder":
        """Add a metadata filter.
        
        Args:
            field: Field name
            operator: Filter operator
            value: Filter value
            
        Returns:
            Self for chaining
        """
        if operator in (FilterOperator.EQ, FilterOperator.NE):
            # Simple equality/inequality
            self._where[field] = {operator.value: value}
        elif operator in (FilterOperator.GT, FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE):
            # Comparison operators
            self._where[field] = {operator.value: value}
        elif operator in (FilterOperator.IN, FilterOperator.NIN):
            # List operators
            if not isinstance(value, list):
                value = [value]
            self._where[field] = {operator.value: value}
        else:
            raise ValueError(f"Unsupported operator for where: {operator}")
        
        return self
    
    def where_document(self, operator: FilterOperator, value: str) -> "QueryBuilder":
        """Add a document content filter.
        
        Args:
            operator: Filter operator (usually $contains)
            value: Search text
            
        Returns:
            Self for chaining
        """
        if operator == FilterOperator.EQ:
            # ChromaDB uses $contains for document search
            self._where_document = {"$contains": value}
        else:
            self._where_document[operator.value] = value
        
        return self
    
    def and_(self, *conditions: List[Dict[str, Any]]) -> "QueryBuilder":
        """Add AND conditions.
        
        Args:
            *conditions: List of condition dictionaries
            
        Returns:
            Self for chaining
        """
        if "$and" not in self._where:
            self._where["$and"] = []
        
        self._where["$and"].extend(conditions)
        return self
    
    def or_(self, *conditions: List[Dict[str, Any]]) -> "QueryBuilder":
        """Add OR conditions.
        
        Args:
            *conditions: List of condition dictionaries
            
        Returns:
            Self for chaining
        """
        if "$or" not in self._where:
            self._where["$or"] = []
        
        self._where["$or"].extend(conditions)
        return self
    
    def build(self) -> QueryFilter:
        """Build the final query filter.
        
        Returns:
            QueryFilter object
        """
        return QueryFilter(
            where=self._where if self._where else None,
            where_document=self._where_document if self._where_document else None
        )
    
    def reset(self) -> "QueryBuilder":
        """Reset the builder.
        
        Returns:
            Self for chaining
        """
        self._where = {}
        self._where_document = {}
        return self
    
    @staticmethod
    def eq(field: str, value: Any) -> Dict[str, Any]:
        """Create equality condition.
        
        Args:
            field: Field name
            value: Value to match
            
        Returns:
            Condition dictionary
        """
        return {field: {"$eq": value}}
    
    @staticmethod
    def ne(field: str, value: Any) -> Dict[str, Any]:
        """Create not-equal condition.
        
        Args:
            field: Field name
            value: Value to not match
            
        Returns:
            Condition dictionary
        """
        return {field: {"$ne": value}}
    
    @staticmethod
    def gt(field: str, value: Any) -> Dict[str, Any]:
        """Create greater-than condition.
        
        Args:
            field: Field name
            value: Value to compare
            
        Returns:
            Condition dictionary
        """
        return {field: {"$gt": value}}
    
    @staticmethod
    def gte(field: str, value: Any) -> Dict[str, Any]:
        """Create greater-than-or-equal condition.
        
        Args:
            field: Field name
            value: Value to compare
            
        Returns:
            Condition dictionary
        """
        return {field: {"$gte": value}}
    
    @staticmethod
    def lt(field: str, value: Any) -> Dict[str, Any]:
        """Create less-than condition.
        
        Args:
            field: Field name
            value: Value to compare
            
        Returns:
            Condition dictionary
        """
        return {field: {"$lt": value}}
    
    @staticmethod
    def lte(field: str, value: Any) -> Dict[str, Any]:
        """Create less-than-or-equal condition.
        
        Args:
            field: Field name
            value: Value to compare
            
        Returns:
            Condition dictionary
        """
        return {field: {"$lte": value}}
    
    @staticmethod
    def in_(field: str, values: List[Any]) -> Dict[str, Any]:
        """Create in-list condition.
        
        Args:
            field: Field name
            values: List of values
            
        Returns:
            Condition dictionary
        """
        return {field: {"$in": values}}
    
    @staticmethod
    def nin(field: str, values: List[Any]) -> Dict[str, Any]:
        """Create not-in-list condition.
        
        Args:
            field: Field name
            values: List of values
            
        Returns:
            Condition dictionary
        """
        return {field: {"$nin": values}}


@dataclass
class SearchQuery:
    """High-level search query."""
    
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    filter: Optional[QueryFilter] = None
    limit: int = 10
    offset: int = 0
    include_scores: bool = True
    
    def validate(self) -> None:
        """Validate the query.
        
        Raises:
            ValueError: If query is invalid
        """
        if self.text is None and self.embedding is None:
            raise ValueError("Either text or embedding must be provided")
        
        if self.text is not None and self.embedding is not None:
            raise ValueError("Only one of text or embedding should be provided")
        
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")