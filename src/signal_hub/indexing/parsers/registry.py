"""Parser registry for automatic parser selection."""

from pathlib import Path
from typing import Dict, List, Optional, Type, Union
import logging

from signal_hub.indexing.parsers.base import Parser
from signal_hub.indexing.parsers.python import PythonParser
from signal_hub.indexing.parsers.javascript import JavaScriptParser
from signal_hub.indexing.parsers.markdown import MarkdownParser
from signal_hub.indexing.parsers.models import Chunk


logger = logging.getLogger(__name__)


class ParserRegistry:
    """Registry for managing and selecting appropriate parsers."""
    
    def __init__(self):
        """Initialize the parser registry."""
        self._parsers: Dict[str, Parser] = {}
        self._extension_map: Dict[str, str] = {}
        
        # Register default parsers
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default parsers."""
        # Python parser
        python_parser = PythonParser()
        self.register("python", python_parser)
        
        # JavaScript/TypeScript parser
        js_parser = JavaScriptParser()
        self.register("javascript", js_parser)
        self.register("typescript", js_parser)  # Same parser for TS
        
        # Markdown parser
        markdown_parser = MarkdownParser()
        self.register("markdown", markdown_parser)
    
    def register(self, language: str, parser: Parser) -> None:
        """Register a parser for a language.
        
        Args:
            language: Language name
            parser: Parser instance
        """
        self._parsers[language.lower()] = parser
        
        # Update extension map
        for ext in parser.extensions:
            self._extension_map[ext.lower()] = language.lower()
        
        logger.info(f"Registered {parser.__class__.__name__} for {language}")
    
    def unregister(self, language: str) -> None:
        """Unregister a parser.
        
        Args:
            language: Language to unregister
        """
        language = language.lower()
        
        if language in self._parsers:
            parser = self._parsers[language]
            
            # Remove from extension map
            for ext in parser.extensions:
                self._extension_map.pop(ext.lower(), None)
            
            # Remove parser
            del self._parsers[language]
            
            logger.info(f"Unregistered parser for {language}")
    
    def get_parser(self, file_path: Union[str, Path]) -> Optional[Parser]:
        """Get appropriate parser for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Parser instance or None if no parser available
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Look up language by extension
        language = self._extension_map.get(extension)
        
        if language and language in self._parsers:
            return self._parsers[language]
        
        logger.warning(f"No parser found for file: {file_path}")
        return None
    
    def get_parser_by_language(self, language: str) -> Optional[Parser]:
        """Get parser by language name.
        
        Args:
            language: Language name
            
        Returns:
            Parser instance or None
        """
        return self._parsers.get(language.lower())
    
    def parse_file(self, file_path: Union[str, Path]) -> List[Chunk]:
        """Parse a file using the appropriate parser.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            List of chunks
            
        Raises:
            ValueError: If no parser available
            IOError: If file cannot be read
        """
        parser = self.get_parser(file_path)
        
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        return parser.parse_file(file_path)
    
    def parse_content(
        self,
        content: str,
        language: str,
        file_path: Optional[Path] = None
    ) -> List[Chunk]:
        """Parse content using specified language parser.
        
        Args:
            content: Content to parse
            language: Language to use
            file_path: Optional file path for context
            
        Returns:
            List of chunks
            
        Raises:
            ValueError: If no parser available for language
        """
        parser = self.get_parser_by_language(language)
        
        if not parser:
            raise ValueError(f"No parser available for language: {language}")
        
        return parser.parse(content, file_path)
    
    def list_supported_languages(self) -> List[str]:
        """Get list of supported languages.
        
        Returns:
            List of language names
        """
        return list(self._parsers.keys())
    
    def list_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of extensions
        """
        return list(self._extension_map.keys())
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if a file can be parsed.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file can be parsed
        """
        return self.get_parser(file_path) is not None