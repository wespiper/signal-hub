"""JavaScript/TypeScript metadata extractor."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

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


class JavaScriptExtractor(BaseExtractor):
    """Extracts metadata from JavaScript/TypeScript source files."""
    
    def can_extract(self, file_path: Path) -> bool:
        """Check if this extractor can handle the file."""
        return file_path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs"}
        
    def extract(self, file_path: Path, content: str, metadata_type: MetadataType) -> CodeMetadata:
        """Extract metadata from JavaScript/TypeScript source code."""
        # Get file metadata
        stat = file_path.stat()
        language = "typescript" if file_path.suffix.lower() in {".ts", ".tsx"} else "javascript"
        
        file_metadata = FileMetadata(
            path=file_path,
            language=language,
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            encoding="utf-8",
            line_count=content.count('\n') + 1
        )
        
        # Extract metadata using regex patterns
        # Note: This is a simplified extractor. For production, consider using a proper JS/TS parser
        extractor = RegexJSExtractor(content, metadata_type)
        
        classes = extractor.extract_classes() if metadata_type != MetadataType.MINIMAL else []
        functions = extractor.extract_functions() if metadata_type != MetadataType.MINIMAL else []
        imports = extractor.extract_imports()
        variables = extractor.extract_variables() if metadata_type == MetadataType.FULL else []
        
        # Extract dependencies
        dependencies = extract_dependencies_from_imports(
            [imp.module for imp in imports if imp.module and not imp.module.startswith('.')]
        )
        
        return CodeMetadata(
            file=file_metadata,
            classes=classes,
            functions=functions,
            imports=imports,
            variables=variables,
            dependencies=dependencies,
            metadata_type=metadata_type
        )


class RegexJSExtractor:
    """Regex-based JavaScript metadata extractor."""
    
    def __init__(self, content: str, metadata_type: MetadataType):
        """Initialize extractor."""
        self.content = content
        self.lines = content.splitlines()
        self.metadata_type = metadata_type
        
    def extract_classes(self) -> List[ClassMetadata]:
        """Extract class definitions."""
        classes = []
        
        # Match class declarations
        class_pattern = re.compile(
            r'^(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?',
            re.MULTILINE
        )
        
        for match in class_pattern.finditer(self.content):
            class_name = match.group(1)
            base_class = match.group(2)
            line_start = self.content[:match.start()].count('\n') + 1
            
            # Find class body
            class_end = self._find_block_end(match.end(), '{', '}')
            line_end = self.content[:class_end].count('\n') + 1 if class_end else line_start
            
            # Extract methods
            methods = self._extract_class_methods(match.start(), class_end)
            
            # Extract docstring (JSDoc comment)
            docstring = self._extract_jsdoc(match.start())
            
            class_metadata = ClassMetadata(
                name=class_name,
                line_start=line_start,
                line_end=line_end,
                docstring=docstring,
                bases=[base_class] if base_class else [],
                methods=methods
            )
            classes.append(class_metadata)
            
        return classes
        
    def extract_functions(self) -> List[FunctionMetadata]:
        """Extract function definitions."""
        functions = []
        
        # Match various function patterns
        patterns = [
            # Regular functions
            re.compile(r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE),
            # Arrow functions assigned to const/let/var
            re.compile(r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', re.MULTILINE),
            # Method-style functions in objects
            re.compile(r'^(?:\s*)(\w+)\s*\(([^)]*)\)\s*{', re.MULTILINE),
        ]
        
        for pattern in patterns:
            for match in pattern.finditer(self.content):
                func_name = match.group(1)
                line_start = self.content[:match.start()].count('\n') + 1
                
                # Skip if inside a class (rough check)
                if self._is_inside_class(match.start()):
                    continue
                    
                # Find function end
                func_end = self._find_block_end(match.end(), '{', '}')
                line_end = self.content[:func_end].count('\n') + 1 if func_end else line_start
                
                # Extract parameters (simplified)
                params_str = match.group(2) if match.lastindex >= 2 else ""
                parameters = [p.strip().split(':')[0].strip() for p in params_str.split(',') if p.strip()]
                
                # Check if async
                is_async = 'async' in self.content[max(0, match.start()-20):match.start()]
                
                # Extract docstring
                docstring = self._extract_jsdoc(match.start())
                
                function_metadata = FunctionMetadata(
                    name=func_name,
                    line_start=line_start,
                    line_end=line_end,
                    docstring=docstring,
                    parameters=parameters,
                    is_async=is_async
                )
                functions.append(function_metadata)
                
        return functions
        
    def extract_imports(self) -> List[ImportMetadata]:
        """Extract import statements."""
        imports = []
        
        # ES6 imports
        es6_pattern = re.compile(
            r'^import\s+(?:(\w+)|{([^}]+)}|\*\s+as\s+(\w+))\s+from\s+[\'"]([^\'\"]+)[\'"]',
            re.MULTILINE
        )
        
        for match in es6_pattern.finditer(self.content):
            line_number = self.content[:match.start()].count('\n') + 1
            module = match.group(4)
            
            # Handle different import types
            if match.group(1):  # Default import
                names = [match.group(1)]
                alias = None
            elif match.group(2):  # Named imports
                names = [n.strip() for n in match.group(2).split(',')]
                alias = None
            elif match.group(3):  # Namespace import
                names = []
                alias = match.group(3)
            else:
                continue
                
            import_metadata = ImportMetadata(
                module=module,
                names=names,
                alias=alias,
                line_number=line_number,
                is_relative=module.startswith('.')
            )
            imports.append(import_metadata)
            
        # CommonJS requires
        require_pattern = re.compile(
            r'^(?:const|let|var)\s+(?:(\w+)|{([^}]+)})\s*=\s*require\s*\(\s*[\'"]([^\'\"]+)[\'"]\s*\)',
            re.MULTILINE
        )
        
        for match in require_pattern.finditer(self.content):
            line_number = self.content[:match.start()].count('\n') + 1
            module = match.group(3)
            
            if match.group(1):  # Simple require
                names = [match.group(1)]
            elif match.group(2):  # Destructured require
                names = [n.strip() for n in match.group(2).split(',')]
            else:
                continue
                
            import_metadata = ImportMetadata(
                module=module,
                names=names,
                line_number=line_number,
                is_relative=module.startswith('.')
            )
            imports.append(import_metadata)
            
        return imports
        
    def extract_variables(self) -> List[VariableMetadata]:
        """Extract module-level variable declarations."""
        variables = []
        
        # Match const/let/var declarations at module level
        var_pattern = re.compile(
            r'^(?:export\s+)?(?:const|let|var)\s+(\w+)(?:\s*:\s*([^=]+))?\s*=',
            re.MULTILINE
        )
        
        for match in var_pattern.finditer(self.content):
            # Skip if inside function or class
            if self._is_inside_block(match.start()):
                continue
                
            var_name = match.group(1)
            type_hint = match.group(2).strip() if match.group(2) else None
            line_number = self.content[:match.start()].count('\n') + 1
            
            # Determine if constant (const or UPPER_CASE)
            is_constant = 'const' in match.group(0) or var_name.isupper()
            
            variable_metadata = VariableMetadata(
                name=var_name,
                line_number=line_number,
                type_hint=type_hint,
                is_constant=is_constant,
                scope="module"
            )
            variables.append(variable_metadata)
            
        return variables
        
    def _find_block_end(self, start_pos: int, open_char: str, close_char: str) -> Optional[int]:
        """Find the end position of a code block."""
        count = 0
        pos = start_pos
        
        while pos < len(self.content):
            if self.content[pos] == open_char:
                count += 1
            elif self.content[pos] == close_char:
                count -= 1
                if count == 0:
                    return pos + 1
            pos += 1
            
        return None
        
    def _is_inside_class(self, pos: int) -> bool:
        """Check if position is inside a class definition."""
        # Simple heuristic: check if 'class' appears before position without closing brace
        before = self.content[:pos]
        last_class = before.rfind('class ')
        if last_class == -1:
            return False
            
        # Count braces between class and position
        between = before[last_class:]
        return between.count('{') > between.count('}')
        
    def _is_inside_block(self, pos: int) -> bool:
        """Check if position is inside any code block."""
        before = self.content[:pos]
        return before.count('{') > before.count('}')
        
    def _extract_jsdoc(self, pos: int) -> Optional[str]:
        """Extract JSDoc comment before position."""
        before = self.content[:pos]
        
        # Look for JSDoc pattern
        jsdoc_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        matches = list(jsdoc_pattern.finditer(before))
        
        if matches:
            # Get the last JSDoc before position
            last_match = matches[-1]
            # Check if it's close enough (within 5 lines)
            between = before[last_match.end():].strip()
            if between.count('\n') < 5:
                # Clean up the JSDoc
                doc = last_match.group(1)
                lines = doc.strip().split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('*'):
                        line = line[1:].strip()
                    if line and not line.startswith('@'):
                        cleaned_lines.append(line)
                return ' '.join(cleaned_lines) if cleaned_lines else None
                
        return None
        
    def _extract_class_methods(self, class_start: int, class_end: Optional[int]) -> List[str]:
        """Extract method names from a class."""
        if not class_end:
            return []
            
        class_content = self.content[class_start:class_end]
        methods = []
        
        # Match method definitions
        method_patterns = [
            re.compile(r'^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', re.MULTILINE),
            re.compile(r'^\s*(?:static\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', re.MULTILINE),
            re.compile(r'^\s*(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', re.MULTILINE),
        ]
        
        for pattern in method_patterns:
            for match in pattern.finditer(class_content):
                method_name = match.group(1)
                if method_name not in ['constructor', 'if', 'for', 'while', 'switch']:
                    methods.append(method_name)
                    
        return list(set(methods))  # Remove duplicates