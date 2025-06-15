"""JavaScript/TypeScript parser using regex-based approach."""

import re
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from signal_hub.indexing.parsers.base import Parser, ParseError
from signal_hub.indexing.parsers.models import Chunk, ChunkType


logger = logging.getLogger(__name__)


class JavaScriptParser(Parser):
    """Parser for JavaScript and TypeScript files."""
    
    languages = ["javascript", "typescript"]
    extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
    
    # Regex patterns for different constructs
    FUNCTION_PATTERN = re.compile(
        r'^(\s*)(export\s+)?(async\s+)?function\s+(\w+)\s*\([^)]*\)',
        re.MULTILINE
    )
    ARROW_FUNCTION_PATTERN = re.compile(
        r'^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>', 
        re.MULTILINE
    )
    CLASS_PATTERN = re.compile(
        r'^(\s*)(export\s+)?(abstract\s+)?class\s+(\w+)(\s+extends\s+\w+)?(\s+implements\s+[^{]+)?',
        re.MULTILINE
    )
    METHOD_PATTERN = re.compile(
        r'^(\s*)(async\s+)?(\w+)\s*\([^)]*\)\s*[{:]',
        re.MULTILINE
    )
    IMPORT_PATTERN = re.compile(
        r'^(\s*)(import|export)\s+.*?(from\s+[\'"][^\'"]+[\'"])?;?$',
        re.MULTILINE
    )
    
    def parse(self, content: str, file_path: Optional[Path] = None) -> List[Chunk]:
        """Parse JavaScript/TypeScript content into chunks.
        
        Args:
            content: JavaScript/TypeScript source code
            file_path: Optional file path for context
            
        Returns:
            List of code chunks
        """
        chunks = []
        lines = content.split('\n')
        
        # Extract imports/exports first
        chunks.extend(self._extract_imports(content, lines, file_path))
        
        # Extract classes
        for match in self.CLASS_PATTERN.finditer(content):
            chunk = self._extract_class(match, content, lines, file_path)
            if chunk:
                chunks.append(chunk)
        
        # Extract functions (not methods)
        for match in self.FUNCTION_PATTERN.finditer(content):
            if not self._is_inside_class(match.start(), content):
                chunk = self._extract_function(match, content, lines, file_path)
                if chunk:
                    chunks.append(chunk)
        
        # Extract arrow functions
        for match in self.ARROW_FUNCTION_PATTERN.finditer(content):
            if not self._is_inside_class(match.start(), content):
                chunk = self._extract_arrow_function(match, content, lines, file_path)
                if chunk:
                    chunks.append(chunk)
        
        # Split large chunks
        final_chunks = []
        for chunk in chunks:
            final_chunks.extend(self.split_large_chunk(chunk))
        
        return final_chunks
    
    def _extract_class(
        self,
        match: re.Match,
        content: str,
        lines: List[str],
        file_path: Optional[Path]
    ) -> Optional[Chunk]:
        """Extract a class definition."""
        try:
            class_name = match.group(4)
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            
            # Find the class body
            brace_count = 0
            end_pos = match.end()
            
            # Find opening brace
            while end_pos < len(content) and content[end_pos] != '{':
                end_pos += 1
            
            if end_pos >= len(content):
                return None
            
            # Match braces to find end
            for i in range(end_pos, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            end_line = content[:end_pos].count('\n') + 1
            class_content = content[start_pos:end_pos]
            
            # Extract method signatures from class
            methods = []
            for method_match in self.METHOD_PATTERN.finditer(class_content):
                method_name = method_match.group(3)
                if method_name not in ['if', 'for', 'while', 'switch', 'catch']:
                    methods.append(method_name)
            
            return Chunk(
                type=ChunkType.CLASS,
                name=class_name,
                content=self.clean_content(class_content),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="javascript",
                metadata={
                    "exported": bool(match.group(2)),
                    "abstract": bool(match.group(3)),
                    "extends": match.group(5).strip() if match.group(5) else None,
                    "methods": methods
                }
            )
        except Exception as e:
            logger.error(f"Error extracting class: {e}")
            return None
    
    def _extract_function(
        self,
        match: re.Match,
        content: str,
        lines: List[str],
        file_path: Optional[Path]
    ) -> Optional[Chunk]:
        """Extract a function definition."""
        try:
            function_name = match.group(4)
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            
            # Find function body
            end_pos = self._find_block_end(content, match.end())
            if end_pos == -1:
                return None
            
            end_line = content[:end_pos].count('\n') + 1
            function_content = content[start_pos:end_pos]
            
            return Chunk(
                type=ChunkType.FUNCTION,
                name=function_name,
                content=self.clean_content(function_content),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="javascript",
                metadata={
                    "exported": bool(match.group(2)),
                    "async": bool(match.group(3))
                }
            )
        except Exception as e:
            logger.error(f"Error extracting function: {e}")
            return None
    
    def _extract_arrow_function(
        self,
        match: re.Match,
        content: str,
        lines: List[str],
        file_path: Optional[Path]
    ) -> Optional[Chunk]:
        """Extract an arrow function definition."""
        try:
            function_name = match.group(4)
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            
            # Find function body end
            # Arrow functions can be single expression or block
            end_pos = match.end()
            
            # Skip whitespace
            while end_pos < len(content) and content[end_pos] in ' \t':
                end_pos += 1
            
            if end_pos < len(content) and content[end_pos] == '{':
                # Block body
                end_pos = self._find_block_end(content, end_pos)
            else:
                # Expression body - find the end (semicolon or newline)
                while end_pos < len(content):
                    if content[end_pos] in ';\n':
                        end_pos += 1
                        break
                    end_pos += 1
            
            if end_pos == -1:
                return None
            
            end_line = content[:end_pos].count('\n') + 1
            function_content = content[start_pos:end_pos]
            
            return Chunk(
                type=ChunkType.FUNCTION,
                name=function_name,
                content=self.clean_content(function_content),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="javascript",
                metadata={
                    "exported": bool(match.group(2)),
                    "async": bool(match.group(5)),
                    "arrow": True
                }
            )
        except Exception as e:
            logger.error(f"Error extracting arrow function: {e}")
            return None
    
    def _extract_imports(
        self,
        content: str,
        lines: List[str],
        file_path: Optional[Path]
    ) -> List[Chunk]:
        """Extract import and export statements."""
        chunks = []
        
        for match in self.IMPORT_PATTERN.finditer(content):
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            end_line = start_line
            
            # Handle multi-line imports
            import_text = match.group(0)
            if '{' in import_text and '}' not in import_text:
                # Multi-line import
                for i in range(start_line, len(lines)):
                    if '}' in lines[i]:
                        end_line = i + 1
                        import_text = '\n'.join(lines[start_line-1:end_line])
                        break
            
            chunks.append(Chunk(
                type=ChunkType.IMPORT,
                name=f"import_line_{start_line}",
                content=import_text.strip(),
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="javascript"
            ))
        
        return chunks
    
    def _find_block_end(self, content: str, start_pos: int) -> int:
        """Find the end of a code block starting from a position."""
        # Find opening brace
        pos = start_pos
        while pos < len(content) and content[pos] != '{':
            pos += 1
        
        if pos >= len(content):
            return -1
        
        # Count braces
        brace_count = 0
        in_string = False
        string_char = None
        escaped = False
        
        for i in range(pos, len(content)):
            char = content[i]
            
            # Handle string literals
            if not escaped:
                if char in '"\'`' and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
            
            # Handle escapes
            escaped = (char == '\\' and not escaped)
            
            # Count braces outside strings
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return i + 1
        
        return -1
    
    def _is_inside_class(self, pos: int, content: str) -> bool:
        """Check if a position is inside a class definition."""
        # Simple heuristic: count class/{ before position
        before = content[:pos]
        
        # Find all class definitions before this position
        class_count = 0
        brace_count = 0
        
        for match in self.CLASS_PATTERN.finditer(before):
            class_count += 1
        
        # Count braces to see if we're still inside
        for char in before:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
        
        # If we have unclosed classes, we're likely inside one
        return class_count > 0 and brace_count > 0