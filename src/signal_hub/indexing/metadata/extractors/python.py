"""Python-specific metadata extractor."""

import ast
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Union

from signal_hub.indexing.metadata.extractor import BaseExtractor
from signal_hub.indexing.metadata.extractors.base import extract_dependencies_from_imports
from signal_hub.indexing.metadata.models import (
    ClassMetadata,
    CodeMetadata,
    FileMetadata,
    FunctionMetadata,
    ImportMetadata,
    MetadataType,
    VariableMetadata,
)

logger = logging.getLogger(__name__)


class PythonExtractor(BaseExtractor):
    """Extracts metadata from Python source files."""
    
    def can_extract(self, file_path: Path) -> bool:
        """Check if this extractor can handle the file."""
        return file_path.suffix.lower() in {".py", ".pyi"}
        
    def extract(self, file_path: Path, content: str, metadata_type: MetadataType) -> CodeMetadata:
        """Extract metadata from Python source code."""
        # Get file metadata
        stat = file_path.stat()
        file_metadata = FileMetadata(
            path=file_path,
            language="python",
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            encoding="utf-8",
            line_count=content.count('\n') + 1
        )
        
        # Parse AST
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            # Return minimal metadata on parse error
            return CodeMetadata(
                file=file_metadata,
                metadata_type=MetadataType.MINIMAL
            )
            
        # Extract metadata based on type
        visitor = PythonASTVisitor(metadata_type)
        visitor.visit(tree)
        
        # Extract dependencies from imports
        dependencies = extract_dependencies_from_imports(
            [imp.module for imp in visitor.imports if imp.module]
        )
        
        return CodeMetadata(
            file=file_metadata,
            classes=visitor.classes,
            functions=visitor.functions,
            imports=visitor.imports,
            variables=visitor.variables if metadata_type == MetadataType.FULL else [],
            dependencies=dependencies,
            metadata_type=metadata_type
        )


class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for extracting Python metadata."""
    
    def __init__(self, metadata_type: MetadataType):
        """Initialize visitor."""
        self.metadata_type = metadata_type
        self.classes: List[ClassMetadata] = []
        self.functions: List[FunctionMetadata] = []
        self.imports: List[ImportMetadata] = []
        self.variables: List[VariableMetadata] = []
        self._current_class: Optional[str] = None
        self._current_function: Optional[str] = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if self.metadata_type == MetadataType.MINIMAL:
            return
            
        # Extract class metadata
        bases = [self._get_name(base) for base in node.bases]
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Get methods and attributes
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attributes.append(item.target.id)
                
        class_metadata = ClassMetadata(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            bases=bases,
            decorators=decorators,
            methods=methods,
            attributes=attributes,
            is_abstract=self._is_abstract_class(node)
        )
        
        self.classes.append(class_metadata)
        
        # Visit class body
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class
        
    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Visit function definition."""
        if self.metadata_type == MetadataType.MINIMAL:
            return
            
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)
            
        # Extract return type
        returns = None
        if node.returns:
            returns = self._get_annotation(node.returns)
            
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Extract function calls (basic - could be enhanced)
        calls = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                calls.append(n.func.id)
                
        function_metadata = FunctionMetadata(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            returns=returns,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_generator=self._is_generator(node),
            complexity=self._calculate_complexity(node),
            calls=list(set(calls))  # Unique calls
        )
        
        self.functions.append(function_metadata)
        
        # Visit function body
        old_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_function
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
        
    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            import_metadata = ImportMetadata(
                module=alias.name,
                names=[],
                alias=alias.asname,
                line_number=node.lineno,
                is_relative=False
            )
            self.imports.append(import_metadata)
            
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statement."""
        if node.module is None:
            return  # Skip relative imports without module
            
        names = [alias.name for alias in node.names]
        import_metadata = ImportMetadata(
            module=node.module,
            names=names,
            alias=None,  # From imports don't have module aliases
            line_number=node.lineno,
            is_relative=node.level > 0,
            level=node.level
        )
        self.imports.append(import_metadata)
        
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment (type hints)."""
        if self.metadata_type != MetadataType.FULL:
            self.generic_visit(node)
            return
            
        if isinstance(node.target, ast.Name):
            # Determine scope
            scope = "module"
            if self._current_class:
                scope = "class"
            elif self._current_function:
                scope = "function"
                
            variable_metadata = VariableMetadata(
                name=node.target.id,
                line_number=node.lineno,
                type_hint=self._get_annotation(node.annotation),
                value=None,  # Could extract if needed
                is_constant=node.target.id.isupper(),
                scope=scope
            )
            self.variables.append(variable_metadata)
            
        self.generic_visit(node)
        
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statement."""
        if self.metadata_type != MetadataType.FULL:
            self.generic_visit(node)
            return
            
        # Only track module-level constants in basic mode
        if self._current_class is None and self._current_function is None:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    variable_metadata = VariableMetadata(
                        name=target.id,
                        line_number=node.lineno,
                        type_hint=None,
                        value=self._get_value_repr(node.value),
                        is_constant=True,
                        scope="module"
                    )
                    self.variables.append(variable_metadata)
                    
        self.generic_visit(node)
        
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "Unknown"
        
    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return f"@{node.id}"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return f"@{node.func.id}"
        elif isinstance(node, ast.Attribute):
            return f"@{self._get_name(node.value)}.{node.attr}"
        return "@Unknown"
        
    def _get_annotation(self, node: ast.AST) -> str:
        """Get type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            slice_val = self._get_annotation(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation(elt) for elt in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "Any"
        
    def _get_value_repr(self, node: ast.AST) -> Optional[str]:
        """Get string representation of a value."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return f"[{len(node.elts)} items]"
        elif isinstance(node, ast.Dict):
            return f"{{{len(node.keys)} items}}"
        return None
        
    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        """Check if class is abstract."""
        # Check for ABC base class
        for base in node.bases:
            if self._get_name(base) in {"ABC", "abc.ABC"}:
                return True
                
        # Check for abstract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if self._get_decorator_name(decorator) in {"@abstractmethod", "@abc.abstractmethod"}:
                        return True
                        
        return False
        
    def _is_generator(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
        """Check if function is a generator."""
        for n in ast.walk(node):
            if isinstance(n, (ast.Yield, ast.YieldFrom)):
                return True
        return False
        
    def _calculate_complexity(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> int:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1  # Base complexity
        
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(n, ast.BoolOp):
                complexity += len(n.values) - 1
                
        return complexity