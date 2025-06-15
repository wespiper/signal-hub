"""JavaScript/TypeScript chunking strategy."""

import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from signal_hub.indexing.chunking.strategy import (
    ChunkingStrategy,
    CodeChunk,
    ChunkType,
    ChunkingContext
)

logger = logging.getLogger(__name__)


class JavaScriptChunkingStrategy(ChunkingStrategy):
    """Chunks JavaScript/TypeScript code using regex patterns."""
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this strategy can handle the file."""
        return file_path.suffix.lower() in {'.js', '.jsx', '.ts', '.tsx', '.mjs'}
        
    def chunk_file(self, file_path: Path, content: Optional[str] = None) -> List[CodeChunk]:
        """Chunk a JavaScript file into logical pieces."""
        if content is None:
            content = file_path.read_text(encoding='utf-8')
            
        language = "typescript" if file_path.suffix.lower() in {'.ts', '.tsx'} else "javascript"
        metadata = {"file_path": str(file_path), "language": language}
        
        return self.chunk_text(content, metadata)
        
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CodeChunk]:
        """Chunk JavaScript text into logical pieces."""
        if not text.strip():
            return []
            
        metadata = metadata or {}
        chunker = JavaScriptChunker(text, self.context)
        
        chunks = chunker.extract_chunks()
        
        # Add file-level metadata to all chunks
        for chunk in chunks:
            chunk.metadata.update(metadata)
            
        # Apply overlap if configured
        chunks = self.apply_overlap(chunks)
        
        return chunks


class JavaScriptChunker:
    """Regex-based JavaScript/TypeScript chunker."""
    
    def __init__(self, source_code: str, context: ChunkingContext):
        """Initialize the chunker."""
        self.source_code = source_code
        self.lines = source_code.split('\n')
        self.context = context
        self.chunks: List[CodeChunk] = []
        
    def extract_chunks(self) -> List[CodeChunk]:
        """Extract all chunks from the source code."""
        # Extract in order of precedence
        self._extract_imports()
        self._extract_classes()
        self._extract_functions()
        self._extract_exports()
        
        # Sort chunks by start line
        self.chunks.sort(key=lambda c: c.start_line)
        
        # Remove duplicates and overlapping chunks
        self.chunks = self._remove_overlapping_chunks(self.chunks)
        
        return self.chunks
        
    def _extract_imports(self):
        """Extract import statements as a single chunk."""
        import_lines = []
        
        # ES6 imports
        es6_pattern = re.compile(r'^import\s+.*?from\s+[\'"].*?[\'"];?\s*$', re.MULTILINE)
        for match in es6_pattern.finditer(self.source_code):
            line_no = self.source_code[:match.start()].count('\n') + 1
            import_lines.append(line_no)
            
        # CommonJS requires
        require_pattern = re.compile(r'^(?:const|let|var)\s+.*?=\s*require\s*\([\'"].*?[\'"]\);?\s*$', re.MULTILINE)
        for match in require_pattern.finditer(self.source_code):
            line_no = self.source_code[:match.start()].count('\n') + 1
            import_lines.append(line_no)
            
        if import_lines:
            # Group consecutive import lines
            import_lines.sort()
            start_line = import_lines[0]
            end_line = import_lines[0]
            
            for line in import_lines[1:]:
                if line <= end_line + 2:  # Allow 1 blank line
                    end_line = line
                else:
                    # Create chunk for previous group
                    self._create_import_chunk(start_line, end_line)
                    start_line = line
                    end_line = line
                    
            # Create final import chunk
            self._create_import_chunk(start_line, end_line)
            
    def _extract_classes(self):
        """Extract class definitions."""
        # Match class declarations
        class_pattern = re.compile(
            r'^(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?.*?{',
            re.MULTILINE
        )
        
        for match in class_pattern.finditer(self.source_code):
            class_name = match.group(1)
            start_line = self.source_code[:match.start()].count('\n') + 1
            
            # Find the end of the class
            end_pos = self._find_block_end(match.end() - 1)
            if end_pos:
                end_line = self.source_code[:end_pos].count('\n') + 1
                
                # Extract methods within the class
                class_content = self.source_code[match.start():end_pos]
                methods = self._extract_class_methods(class_content, class_name, start_line)
                
                # Check if class should be chunked as a whole or split
                class_size = end_pos - match.start()
                
                if class_size <= self.context.max_chunk_size or not methods:
                    # Single chunk for the entire class
                    chunk = CodeChunk(
                        content=self._get_lines(start_line, end_line),
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type=ChunkType.CLASS,
                        metadata={"class_name": class_name}
                    )
                    self.chunks.append(chunk)
                else:
                    # Add class header
                    header_lines = []
                    for i in range(start_line - 1, min(start_line + 5, len(self.lines))):
                        if i < len(self.lines) and '{' in self.lines[i]:
                            header_lines.append(i)
                            break
                        header_lines.append(i)
                        
                    if header_lines:
                        header_chunk = CodeChunk(
                            content=self._get_lines(start_line, header_lines[-1] + 1),
                            start_line=start_line,
                            end_line=header_lines[-1] + 1,
                            chunk_type=ChunkType.CLASS,
                            metadata={"class_name": class_name, "header_only": True}
                        )
                        self.chunks.append(header_chunk)
                        
                    # Add method chunks
                    self.chunks.extend(methods)
                    
    def _extract_functions(self):
        """Extract function definitions."""
        # Various function patterns
        patterns = [
            # Regular function declaration
            (re.compile(r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\).*?{', re.MULTILINE), "function"),
            # Arrow function assigned to const/let/var
            (re.compile(r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*{', re.MULTILINE), "arrow"),
            # Object method shorthand
            (re.compile(r'^(?:\s*)(\w+)\s*\([^)]*\)\s*{', re.MULTILINE), "method"),
        ]
        
        for pattern, func_type in patterns:
            for match in pattern.finditer(self.source_code):
                func_name = match.group(1)
                
                # Skip if inside a class
                if self._is_inside_class(match.start()):
                    continue
                    
                start_line = self.source_code[:match.start()].count('\n') + 1
                
                # Find function end
                if func_type == "arrow":
                    # Arrow functions might not have braces
                    if '{' in match.group():
                        end_pos = self._find_block_end(match.end() - 1)
                    else:
                        # Single expression arrow function
                        end_pos = self.source_code.find('\n', match.end())
                else:
                    end_pos = self._find_block_end(match.end() - 1)
                    
                if end_pos:
                    end_line = self.source_code[:end_pos].count('\n') + 1
                    
                    # Check for decorators/comments before function
                    actual_start = self._find_function_start(start_line)
                    
                    chunk = CodeChunk(
                        content=self._get_lines(actual_start, end_line),
                        start_line=actual_start,
                        end_line=end_line,
                        chunk_type=ChunkType.FUNCTION,
                        metadata={
                            "function_name": func_name,
                            "function_type": func_type,
                            "is_async": "async" in match.group()
                        }
                    )
                    self.chunks.append(chunk)
                    
    def _extract_exports(self):
        """Extract export statements that aren't already captured."""
        # Named exports
        export_pattern = re.compile(r'^export\s*{[^}]+}\s*(?:from\s+[\'"][^\'"]+[\'"])?\s*;?', re.MULTILINE)
        
        for match in export_pattern.finditer(self.source_code):
            start_line = self.source_code[:match.start()].count('\n') + 1
            end_line = self.source_code[:match.end()].count('\n') + 1
            
            # Check if already part of another chunk
            if not self._is_line_in_chunks(start_line):
                chunk = CodeChunk(
                    content=self._get_lines(start_line, end_line),
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type=ChunkType.MODULE,
                    metadata={"contains": "exports"}
                )
                self.chunks.append(chunk)
                
    def _extract_class_methods(self, class_content: str, class_name: str, class_start_line: int) -> List[CodeChunk]:
        """Extract methods from within a class."""
        methods = []
        
        # Method patterns
        method_patterns = [
            re.compile(r'(?:^\s*(?:static\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*{)', re.MULTILINE),
            re.compile(r'(?:^\s*(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)', re.MULTILINE),
        ]
        
        for pattern in method_patterns:
            for match in pattern.finditer(class_content):
                method_name = match.group(1)
                
                # Skip constructor in single chunk mode
                if method_name == "constructor" and len(class_content) <= self.context.max_chunk_size:
                    continue
                    
                # Calculate line number relative to file
                rel_start = class_content[:match.start()].count('\n')
                start_line = class_start_line + rel_start
                
                # Find method end
                end_pos = self._find_block_end_in_string(class_content, match.end() - 1)
                if end_pos:
                    rel_end = class_content[:end_pos].count('\n')
                    end_line = class_start_line + rel_end
                    
                    method_chunk = CodeChunk(
                        content=self._get_lines(start_line, end_line),
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type=ChunkType.METHOD,
                        parent_context=class_name,
                        metadata={
                            "method_name": method_name,
                            "class_name": class_name,
                            "is_static": "static" in match.group(),
                            "is_async": "async" in match.group()
                        }
                    )
                    methods.append(method_chunk)
                    
        return methods
        
    def _find_block_end(self, start_pos: int) -> Optional[int]:
        """Find the end position of a code block starting with {."""
        return self._find_block_end_in_string(self.source_code, start_pos)
        
    def _find_block_end_in_string(self, text: str, start_pos: int) -> Optional[int]:
        """Find the end position of a code block in a string."""
        count = 0
        pos = start_pos
        in_string = False
        string_char = None
        
        while pos < len(text):
            char = text[pos]
            
            # Handle strings
            if char in ['"', "'", '`'] and (pos == 0 or text[pos-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    
            # Count braces when not in string
            if not in_string:
                if char == '{':
                    count += 1
                elif char == '}':
                    count -= 1
                    if count == 0:
                        return pos + 1
                        
            pos += 1
            
        return None
        
    def _is_inside_class(self, pos: int) -> bool:
        """Check if position is inside a class definition."""
        before = self.source_code[:pos]
        
        # Count class declarations and closing braces
        class_count = len(re.findall(r'\bclass\s+\w+', before))
        
        # This is a simplification - proper parsing would be better
        open_braces = before.count('{')
        close_braces = before.count('}')
        
        return class_count > 0 and open_braces > close_braces
        
    def _find_function_start(self, line_no: int) -> int:
        """Find the actual start of a function including decorators/comments."""
        start = line_no
        
        # Look backwards for decorators or JSDoc comments
        for i in range(line_no - 2, max(0, line_no - 10), -1):
            if i >= len(self.lines):
                continue
                
            line = self.lines[i].strip()
            
            # Check for decorators
            if line.startswith('@'):
                start = i + 1
            # Check for JSDoc
            elif line.startswith('/**') or line.startswith('*'):
                start = i + 1
            # Empty line or regular comment
            elif line == '' or line.startswith('//'):
                continue
            else:
                # Found non-decorator/comment line
                break
                
        return start
        
    def _create_import_chunk(self, start_line: int, end_line: int):
        """Create a chunk for import statements."""
        # Extend to include any constants after imports
        extended_end = end_line
        
        for i in range(end_line, min(end_line + 20, len(self.lines))):
            if i >= len(self.lines):
                break
                
            line = self.lines[i].strip()
            
            # Check for constants
            if re.match(r'^(?:const|let|var)\s+[A-Z_]+\s*=', line):
                extended_end = i + 1
            # Check for empty lines or comments
            elif line == '' or line.startswith('//') or line.startswith('/*'):
                continue
            else:
                # Found non-constant line
                break
                
        chunk = CodeChunk(
            content=self._get_lines(start_line, extended_end),
            start_line=start_line,
            end_line=extended_end,
            chunk_type=ChunkType.MODULE,
            metadata={"contains": "imports_and_constants"}
        )
        self.chunks.append(chunk)
        
    def _get_lines(self, start: int, end: int) -> str:
        """Get lines from source code (1-indexed)."""
        start_idx = max(0, start - 1)
        end_idx = min(len(self.lines), end)
        return '\n'.join(self.lines[start_idx:end_idx])
        
    def _is_line_in_chunks(self, line_no: int) -> bool:
        """Check if a line is already part of any chunk."""
        for chunk in self.chunks:
            if chunk.start_line <= line_no <= chunk.end_line:
                return True
        return False
        
    def _remove_overlapping_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Remove overlapping chunks, keeping the most specific."""
        if not chunks:
            return chunks
            
        # Sort by start line, then by size (smaller first)
        sorted_chunks = sorted(chunks, key=lambda c: (c.start_line, c.size))
        
        result = []
        for chunk in sorted_chunks:
            # Check if this chunk overlaps with any existing
            overlaps = False
            for existing in result:
                if (chunk.start_line >= existing.start_line and 
                    chunk.end_line <= existing.end_line):
                    overlaps = True
                    break
                    
            if not overlaps:
                result.append(chunk)
                
        return result