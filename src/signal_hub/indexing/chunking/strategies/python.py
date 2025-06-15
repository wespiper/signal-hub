"""Python-specific chunking strategy using AST."""

import ast
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from signal_hub.indexing.chunking.strategy import (
    ChunkingStrategy,
    CodeChunk,
    ChunkType,
    ChunkingContext
)

logger = logging.getLogger(__name__)


class PythonChunkingStrategy(ChunkingStrategy):
    """Chunks Python code using AST analysis."""
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this strategy can handle the file."""
        return file_path.suffix.lower() in {'.py', '.pyi'}
        
    def chunk_file(self, file_path: Path, content: Optional[str] = None) -> List[CodeChunk]:
        """Chunk a Python file into logical pieces."""
        if content is None:
            content = file_path.read_text(encoding='utf-8')
            
        metadata = {"file_path": str(file_path), "language": "python"}
        return self.chunk_text(content, metadata)
        
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CodeChunk]:
        """Chunk Python text into logical pieces."""
        if not text.strip():
            return []
            
        metadata = metadata or {}
        
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python code: {e}")
            # Fall back to line-based chunking
            return self._fallback_chunking(text, metadata)
            
        # Extract chunks using AST visitor
        visitor = PythonASTChunker(text, self.context)
        visitor.visit(tree)
        
        chunks = visitor.get_chunks()
        
        # Add file-level metadata to all chunks
        for chunk in chunks:
            chunk.metadata.update(metadata)
            
        # Apply overlap if configured
        chunks = self.apply_overlap(chunks)
        
        return chunks
        
    def _fallback_chunking(self, text: str, metadata: Dict[str, Any]) -> List[CodeChunk]:
        """Fallback to simple line-based chunking."""
        lines = text.split('\n')
        chunks = []
        
        current_chunk = []
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            current_chunk.append(line)
            
            # Check if we should create a chunk
            chunk_text = '\n'.join(current_chunk)
            if (len(chunk_text) >= self.context.max_chunk_size or 
                i == len(lines)):
                
                chunk = CodeChunk(
                    content=chunk_text,
                    start_line=current_start,
                    end_line=i,
                    chunk_type=ChunkType.BLOCK,
                    metadata=metadata
                )
                chunks.append(chunk)
                
                current_chunk = []
                current_start = i + 1
                
        return chunks


class PythonASTChunker(ast.NodeVisitor):
    """AST visitor that creates chunks from Python code."""
    
    def __init__(self, source_code: str, context: ChunkingContext):
        """Initialize the chunker."""
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.context = context
        self.chunks: List[CodeChunk] = []
        self._current_class: Optional[str] = None
        self._module_chunk_lines: List[int] = []
        
    def get_chunks(self) -> List[CodeChunk]:
        """Get all extracted chunks."""
        # First, create module-level chunk if needed
        if self._module_chunk_lines:
            self._create_module_chunk()
            
        # Sort chunks by start line
        self.chunks.sort(key=lambda c: c.start_line)
        
        return self.chunks
        
    def visit_Module(self, node: ast.Module):
        """Visit module node."""
        # Collect module-level statements (imports, constants, etc.)
        for child in node.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                # Add import lines to module chunk
                start = child.lineno
                end = child.end_lineno or child.lineno
                self._module_chunk_lines.extend(range(start, end + 1))
                
            elif isinstance(child, ast.Assign):
                # Check if it's a constant (UPPER_CASE names)
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        start = child.lineno
                        end = child.end_lineno or child.lineno
                        self._module_chunk_lines.extend(range(start, end + 1))
                        
        # Continue visiting children
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        # Check if class is small enough to be a single chunk
        class_size = self._calculate_node_size(node)
        
        if class_size <= self.context.max_chunk_size:
            # Create single chunk for the entire class
            chunk = self._create_chunk_from_node(
                node,
                ChunkType.CLASS,
                metadata={
                    "class_name": node.name,
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "bases": [self._get_name(base) for base in node.bases]
                }
            )
            self.chunks.append(chunk)
        else:
            # Chunk the class header separately
            header_end = node.body[0].lineno - 1 if node.body else node.end_lineno
            
            header_chunk = CodeChunk(
                content=self._get_lines(node.lineno, header_end),
                start_line=node.lineno,
                end_line=header_end,
                chunk_type=ChunkType.CLASS,
                metadata={"class_name": node.name}
            )
            self.chunks.append(header_chunk)
            
            # Visit methods separately
            old_class = self._current_class
            self._current_class = node.name
            
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.visit(item)
                    
            self._current_class = old_class
            
    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Visit function/method definition."""
        chunk_type = ChunkType.METHOD if self._current_class else ChunkType.FUNCTION
        
        metadata = {
            "function_name": node.name,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "parameters": [arg.arg for arg in node.args.args]
        }
        
        # Add return type if available
        if node.returns:
            metadata["return_type"] = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
            
        chunk = self._create_chunk_from_node(
            node,
            chunk_type,
            metadata=metadata,
            parent_context=self._current_class
        )
        
        # Check if chunk is too large
        if chunk.size > self.context.max_chunk_size:
            # Split the function into smaller chunks
            self._split_large_function(node, chunk)
        else:
            self.chunks.append(chunk)
            
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
        
    def _create_chunk_from_node(
        self,
        node: ast.AST,
        chunk_type: ChunkType,
        metadata: Optional[Dict[str, Any]] = None,
        parent_context: Optional[str] = None
    ) -> CodeChunk:
        """Create a chunk from an AST node."""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Include decorators if present
        if hasattr(node, 'decorator_list') and node.decorator_list:
            start_line = min(d.lineno for d in node.decorator_list)
            
        content = self._get_lines(start_line, end_line)
        
        # Validate syntax if configured
        is_valid_syntax = None
        if self.context.syntax_validation:
            try:
                compile(content, '<string>', 'exec')
                is_valid_syntax = True
            except SyntaxError:
                is_valid_syntax = False
                
        return CodeChunk(
            content=content,
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            metadata=metadata or {},
            parent_context=parent_context,
            is_valid_syntax=is_valid_syntax
        )
        
    def _create_module_chunk(self):
        """Create a chunk for module-level code."""
        if not self._module_chunk_lines:
            return
            
        # Sort and group consecutive lines
        sorted_lines = sorted(set(self._module_chunk_lines))
        
        # Group consecutive lines
        groups = []
        current_group = [sorted_lines[0]]
        
        for line in sorted_lines[1:]:
            if line == current_group[-1] + 1:
                current_group.append(line)
            else:
                groups.append(current_group)
                current_group = [line]
                
        groups.append(current_group)
        
        # Create chunks for each group
        for group in groups:
            content = self._get_lines(group[0], group[-1])
            chunk = CodeChunk(
                content=content,
                start_line=group[0],
                end_line=group[-1],
                chunk_type=ChunkType.MODULE,
                metadata={"contains": "imports_and_constants"}
            )
            self.chunks.append(chunk)
            
    def _split_large_function(self, node: ast.FunctionDef, original_chunk: CodeChunk):
        """Split a large function into smaller chunks."""
        # For now, just add the whole function
        # TODO: Implement smart splitting based on logical blocks
        self.chunks.append(original_chunk)
        
    def _calculate_node_size(self, node: ast.AST) -> int:
        """Calculate the size of an AST node in characters."""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            content = self._get_lines(node.lineno, node.end_lineno or node.lineno)
            return len(content)
        return 0
        
    def _get_lines(self, start: int, end: int) -> str:
        """Get lines from source code."""
        # Convert to 0-based indexing
        start_idx = max(0, start - 1)
        end_idx = min(len(self.source_lines), end)
        
        return '\n'.join(self.source_lines[start_idx:end_idx])
        
    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"
        
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"