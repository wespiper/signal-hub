"""Metadata models for code understanding."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class MetadataType(str, Enum):
    """Type of metadata extraction performed."""
    
    FULL = "full"
    BASIC = "basic"
    MINIMAL = "minimal"


class FileMetadata(BaseModel):
    """Metadata about a file."""
    
    path: Path
    language: str
    size_bytes: int
    last_modified: datetime
    encoding: str = "utf-8"
    line_count: int = 0
    hash: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True


class ClassMetadata(BaseModel):
    """Metadata about a class definition."""
    
    name: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    bases: List[str] = Field(default_factory=list)
    decorators: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)
    is_abstract: bool = False
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate class name is not empty."""
        if not v or not v.strip():
            raise ValueError("Class name cannot be empty")
        return v
        
    @field_validator('line_end')
    @classmethod
    def validate_line_range(cls, v: int, info) -> int:
        """Validate line range is valid."""
        if 'line_start' in info.data and v < info.data['line_start']:
            raise ValueError("line_end must be >= line_start")
        return v


class FunctionMetadata(BaseModel):
    """Metadata about a function definition."""
    
    name: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)
    returns: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    complexity: int = 0
    calls: List[str] = Field(default_factory=list)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate function name is not empty."""
        if not v or not v.strip():
            raise ValueError("Function name cannot be empty")
        return v
        
    @field_validator('line_end')
    @classmethod
    def validate_line_range(cls, v: int, info) -> int:
        """Validate line range is valid."""
        if 'line_start' in info.data and v < info.data['line_start']:
            raise ValueError("line_end must be >= line_start")
        return v


class ImportMetadata(BaseModel):
    """Metadata about an import statement."""
    
    module: str
    names: List[str] = Field(default_factory=list)
    alias: Optional[str] = None
    line_number: int
    is_relative: bool = False
    level: int = 0  # For relative imports


class VariableMetadata(BaseModel):
    """Metadata about a variable definition."""
    
    name: str
    line_number: int
    type_hint: Optional[str] = None
    value: Optional[str] = None
    is_constant: bool = False
    scope: str = "module"  # module, class, function


class CodeMetadata(BaseModel):
    """Aggregated metadata for a code file."""
    
    file: FileMetadata
    classes: List[ClassMetadata] = Field(default_factory=list)
    functions: List[FunctionMetadata] = Field(default_factory=list)
    imports: List[ImportMetadata] = Field(default_factory=list)
    variables: List[VariableMetadata] = Field(default_factory=list)
    dependencies: Set[str] = Field(default_factory=set)
    metadata_type: MetadataType = MetadataType.FULL
    extraction_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True
        
    def get_all_symbols(self) -> List[str]:
        """Get all symbol names defined in the file."""
        symbols = []
        symbols.extend(c.name for c in self.classes)
        symbols.extend(f.name for f in self.functions)
        symbols.extend(v.name for v in self.variables)
        return symbols
        
    def get_external_calls(self) -> Set[str]:
        """Get all external function calls."""
        calls = set()
        for func in self.functions:
            calls.update(func.calls)
        return calls
        
    def to_search_metadata(self) -> dict:
        """Convert to metadata suitable for search indexing."""
        return {
            "file_path": str(self.file.path),
            "language": self.file.language,
            "classes": [c.name for c in self.classes],
            "functions": [f.name for f in self.functions],
            "imports": list(self.dependencies),
            "symbols": self.get_all_symbols(),
            "line_count": self.file.line_count,
            "has_tests": any("test" in f.name.lower() for f in self.functions),
            "is_test_file": "test" in str(self.file.path).lower()
        }