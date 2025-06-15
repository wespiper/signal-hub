"""Python file parser using AST."""

import ast
from pathlib import Path
from typing import List, Optional, Union
import logging

from signal_hub.indexing.parsers.base import Parser, ParseError
from signal_hub.indexing.parsers.models import Chunk, ChunkType


logger = logging.getLogger(__name__)


class PythonParser(Parser):
    """Parser for Python source files."""
    
    languages = ["python"]
    extensions = [".py", ".pyi", ".pyx"]
    
    def parse(self, content: str, file_path: Optional[Path] = None) -> List[Chunk]:
        """Parse Python content into chunks.
        
        Args:
            content: Python source code
            file_path: Optional file path for context
            
        Returns:
            List of code chunks
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python file: {e}")
            # Fall back to simple text chunks
            return self._fallback_parse(content, file_path)
        
        chunks = []
        lines = content.split('\n')
        
        # Extract module-level docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            chunks.append(Chunk(
                type=ChunkType.DOCSTRING,
                name="module_docstring",
                content=module_docstring,
                start_line=1,
                end_line=self._count_docstring_lines(module_docstring, 1, lines),
                file_path=file_path,
                language="python"
            ))
        
        # Extract imports
        imports = self._extract_imports(tree, lines, file_path)
        chunks.extend(imports)
        
        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                chunk = self._extract_class(node, lines, file_path)
                if chunk:
                    chunks.append(chunk)
                    
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_chunk = self._extract_function(
                            item, lines, file_path, parent_class=node.name
                        )
                        if method_chunk:
                            chunks.append(method_chunk)
            
            elif isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                chunk = self._extract_function(node, lines, file_path)
                if chunk:
                    chunks.append(chunk)
        
        # Split large chunks if needed
        final_chunks = []
        for chunk in chunks:
            final_chunks.extend(self.split_large_chunk(chunk))
        
        return final_chunks
    
    def _extract_class(
        self, 
        node: ast.ClassDef, 
        lines: List[str], 
        file_path: Optional[Path]
    ) -> Optional[Chunk]:
        """Extract a class definition."""
        try:
            # Get class definition including decorators
            start_line = node.lineno
            if node.decorator_list:
                start_line = min(d.lineno for d in node.decorator_list)
            
            # Find the last line of the class signature
            # This is tricky with multi-line definitions
            end_line = node.lineno
            
            # Get class docstring
            docstring = ast.get_docstring(node)
            
            # Extract just the class definition (not the body)
            class_lines = []
            for i in range(start_line - 1, min(end_line + 5, len(lines))):
                class_lines.append(lines[i])
                if lines[i].rstrip().endswith(':'):
                    end_line = i + 1
                    break
            
            # Add docstring if present
            if docstring:
                docstring_lines = docstring.split('\n')
                for line in docstring_lines[:3]:  # First few lines
                    if line.strip():
                        class_lines.append(f"    {line}")
                if len(docstring_lines) > 3:
                    class_lines.append("    ...")
            
            content = '\n'.join(class_lines)
            
            return Chunk(
                type=ChunkType.CLASS,
                name=node.name,
                content=self.clean_content(content),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="python",
                metadata={
                    "bases": [self._get_name(base) for base in node.bases],
                    "decorators": [self._get_name(d) for d in node.decorator_list],
                    "has_docstring": docstring is not None
                }
            )
        except Exception as e:
            logger.error(f"Error extracting class {node.name}: {e}")
            return None
    
    def _extract_function(
        self, 
        node: ast.FunctionDef,
        lines: List[str],
        file_path: Optional[Path],
        parent_class: Optional[str] = None
    ) -> Optional[Chunk]:
        """Extract a function or method definition."""
        try:
            # Get function including decorators
            start_line = node.lineno
            if node.decorator_list:
                start_line = min(d.lineno for d in node.decorator_list)
            
            # Get the function body's last line
            if node.body:
                end_line = max(
                    self._get_node_end_line(child) 
                    for child in node.body
                )
            else:
                end_line = node.lineno + 1
            
            # Extract content
            content = '\n'.join(lines[start_line - 1:end_line])
            
            # Determine chunk type
            chunk_type = ChunkType.METHOD if parent_class else ChunkType.FUNCTION
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            return Chunk(
                type=chunk_type,
                name=node.name,
                content=self.clean_content(content),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="python",
                parent=parent_class,
                metadata={
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [self._get_name(d) for d in node.decorator_list],
                    "has_docstring": docstring is not None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
            )
        except Exception as e:
            logger.error(f"Error extracting function {node.name}: {e}")
            return None
    
    def _extract_imports(
        self,
        tree: ast.AST,
        lines: List[str],
        file_path: Optional[Path]
    ) -> List[Chunk]:
        """Extract import statements."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                content = lines[node.lineno - 1]
                
                # Handle multi-line imports
                if content.rstrip().endswith('\\') or '(' in content:
                    end_line = node.lineno
                    import_lines = [content]
                    
                    for i in range(node.lineno, len(lines)):
                        import_lines.append(lines[i])
                        if not lines[i].rstrip().endswith('\\') and ')' in lines[i]:
                            end_line = i + 1
                            break
                    
                    content = '\n'.join(import_lines)
                else:
                    end_line = node.lineno
                
                imports.append(Chunk(
                    type=ChunkType.IMPORT,
                    name=f"import_line_{node.lineno}",
                    content=content.strip(),
                    start_line=node.lineno,
                    end_line=end_line,
                    file_path=file_path,
                    language="python"
                ))
        
        return imports
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if a function is a method inside a class."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False
    
    def _get_name(self, node: ast.AST) -> str:
        """Get the name/string representation of an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
    
    def _get_node_end_line(self, node: ast.AST) -> int:
        """Get the last line number of an AST node."""
        if hasattr(node, 'end_lineno'):
            return node.end_lineno or node.lineno
        elif hasattr(node, 'lineno'):
            return node.lineno
        else:
            # Recursively find the maximum line number
            max_line = 0
            for child in ast.walk(node):
                if hasattr(child, 'lineno'):
                    max_line = max(max_line, child.lineno)
            return max_line or 1
    
    def _count_docstring_lines(
        self, 
        docstring: str, 
        start_line: int, 
        lines: List[str]
    ) -> int:
        """Count how many lines a docstring spans."""
        # Simple heuristic - count lines until we find the closing quotes
        docstring_lines = docstring.count('\n') + 1
        
        # Look for the closing quotes
        for i in range(start_line - 1, min(start_line + docstring_lines + 5, len(lines))):
            if '"""' in lines[i] or "'''" in lines[i]:
                # Check if this is the closing quotes
                if i > start_line - 1:  # Not the opening line
                    return i + 1
        
        return start_line + docstring_lines
    
    def _fallback_parse(self, content: str, file_path: Optional[Path]) -> List[Chunk]:
        """Simple fallback parser when AST parsing fails."""
        chunks = []
        lines = content.split('\n')
        
        current_chunk_start = 0
        current_chunk_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect simple function/class definitions
            if (stripped.startswith('def ') or stripped.startswith('class ')) and current_chunk_lines:
                # Save previous chunk
                if current_chunk_lines:
                    content = '\n'.join(current_chunk_lines)
                    chunks.append(Chunk(
                        type=ChunkType.BLOCK,
                        name=f"block_{current_chunk_start}",
                        content=self.clean_content(content),
                        start_line=current_chunk_start + 1,
                        end_line=i,
                        file_path=file_path,
                        language="python"
                    ))
                
                current_chunk_start = i
                current_chunk_lines = [line]
            else:
                current_chunk_lines.append(line)
        
        # Add final chunk
        if current_chunk_lines:
            content = '\n'.join(current_chunk_lines)
            chunks.append(Chunk(
                type=ChunkType.BLOCK,
                name=f"block_{current_chunk_start}",
                content=self.clean_content(content),
                start_line=current_chunk_start + 1,
                end_line=len(lines),
                file_path=file_path,
                language="python"
            ))
        
        return chunks