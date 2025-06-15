"""Unit tests for parser registry."""

import pytest
from pathlib import Path

from signal_hub.indexing.parsers.registry import ParserRegistry
from signal_hub.indexing.parsers.base import Parser
from signal_hub.indexing.parsers.models import Chunk, ChunkType


class CustomParser(Parser):
    """Custom parser for testing."""
    
    languages = ["custom"]
    extensions = [".custom", ".cst"]
    
    def parse(self, content: str, file_path=None):
        return [
            Chunk(
                type=ChunkType.BLOCK,
                name="custom_block",
                content=content,
                start_line=1,
                end_line=1,
                language="custom"
            )
        ]


class TestParserRegistry:
    """Test ParserRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create parser registry."""
        return ParserRegistry()
    
    def test_default_parsers_registered(self, registry):
        """Test that default parsers are registered."""
        # Check languages
        languages = registry.list_supported_languages()
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "markdown" in languages
        
        # Check extensions
        extensions = registry.list_supported_extensions()
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".md" in extensions
    
    def test_get_parser_by_extension(self, registry):
        """Test getting parser by file extension."""
        # Python files
        assert registry.get_parser("test.py") is not None
        assert registry.get_parser(Path("dir/module.py")) is not None
        
        # JavaScript files
        assert registry.get_parser("app.js") is not None
        assert registry.get_parser("component.jsx") is not None
        
        # TypeScript files
        assert registry.get_parser("types.ts") is not None
        assert registry.get_parser("App.tsx") is not None
        
        # Markdown files
        assert registry.get_parser("README.md") is not None
        
        # Unknown extension
        assert registry.get_parser("file.unknown") is None
    
    def test_get_parser_by_language(self, registry):
        """Test getting parser by language name."""
        python_parser = registry.get_parser_by_language("python")
        assert python_parser is not None
        assert python_parser.__class__.__name__ == "PythonParser"
        
        js_parser = registry.get_parser_by_language("javascript")
        assert js_parser is not None
        
        # Case insensitive
        assert registry.get_parser_by_language("PYTHON") is not None
        
        # Unknown language
        assert registry.get_parser_by_language("cobol") is None
    
    def test_register_custom_parser(self, registry):
        """Test registering a custom parser."""
        custom_parser = CustomParser()
        registry.register("custom", custom_parser)
        
        # Check it's registered
        assert "custom" in registry.list_supported_languages()
        assert ".custom" in registry.list_supported_extensions()
        assert ".cst" in registry.list_supported_extensions()
        
        # Can get parser
        assert registry.get_parser("file.custom") is not None
        assert registry.get_parser_by_language("custom") == custom_parser
    
    def test_unregister_parser(self, registry):
        """Test unregistering a parser."""
        # Register custom parser
        custom_parser = CustomParser()
        registry.register("custom", custom_parser)
        
        # Unregister it
        registry.unregister("custom")
        
        # Check it's gone
        assert "custom" not in registry.list_supported_languages()
        assert ".custom" not in registry.list_supported_extensions()
        assert registry.get_parser("file.custom") is None
    
    def test_parse_file(self, registry, tmp_path):
        """Test parsing a file through registry."""
        # Create Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("""
def test_function():
    return 42
""")
        
        chunks = registry.parse_file(py_file)
        
        assert len(chunks) > 0
        assert any(c.name == "test_function" for c in chunks)
    
    def test_parse_file_no_parser(self, registry):
        """Test parsing file with no available parser."""
        with pytest.raises(ValueError) as exc_info:
            registry.parse_file("unknown.xyz")
        
        assert "No parser available" in str(exc_info.value)
    
    def test_parse_content(self, registry):
        """Test parsing content with specified language."""
        python_code = """
class TestClass:
    pass
"""
        
        chunks = registry.parse_content(python_code, "python")
        
        assert len(chunks) > 0
        assert any(c.name == "TestClass" for c in chunks)
    
    def test_parse_content_with_context(self, registry):
        """Test parsing content with file context."""
        js_code = """
function main() {
    console.log("test");
}
"""
        
        file_path = Path("app.js")
        chunks = registry.parse_content(js_code, "javascript", file_path)
        
        assert len(chunks) > 0
        assert chunks[0].file_path == file_path
    
    def test_parse_content_no_parser(self, registry):
        """Test parsing content with unknown language."""
        with pytest.raises(ValueError) as exc_info:
            registry.parse_content("code", "unknown_lang")
        
        assert "No parser available for language" in str(exc_info.value)
    
    def test_can_parse(self, registry):
        """Test checking if file can be parsed."""
        assert registry.can_parse("test.py") is True
        assert registry.can_parse("app.js") is True
        assert registry.can_parse("README.md") is True
        assert registry.can_parse("binary.exe") is False
        assert registry.can_parse("data.csv") is False
    
    def test_typescript_shares_parser(self, registry):
        """Test that TypeScript uses same parser as JavaScript."""
        js_parser = registry.get_parser_by_language("javascript")
        ts_parser = registry.get_parser_by_language("typescript")
        
        # Should be the same instance
        assert js_parser is ts_parser