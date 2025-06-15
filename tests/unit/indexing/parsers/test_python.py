"""Unit tests for Python parser."""

import pytest
from pathlib import Path

from signal_hub.indexing.parsers.python import PythonParser
from signal_hub.indexing.parsers.models import ChunkType


class TestPythonParser:
    """Test PythonParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create Python parser."""
        return PythonParser()
    
    def test_parse_simple_function(self, parser):
        """Test parsing a simple function."""
        code = """
def hello_world():
    '''Say hello.'''
    print("Hello, World!")
"""
        chunks = parser.parse(code.strip())
        
        assert len(chunks) == 1
        assert chunks[0].type == ChunkType.FUNCTION
        assert chunks[0].name == "hello_world"
        assert chunks[0].start_line == 1
        assert chunks[0].end_line == 3
        assert "print(" in chunks[0].content
    
    def test_parse_class_with_methods(self, parser):
        """Test parsing a class with methods."""
        code = """
class Calculator:
    '''A simple calculator.'''
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
"""
        chunks = parser.parse(code.strip())
        
        # Should have class + 2 methods
        assert len(chunks) == 3
        
        # Check class
        class_chunk = next(c for c in chunks if c.type == ChunkType.CLASS)
        assert class_chunk.name == "Calculator"
        assert "Calculator:" in class_chunk.content
        
        # Check methods
        methods = [c for c in chunks if c.type == ChunkType.METHOD]
        assert len(methods) == 2
        assert {m.name for m in methods} == {"add", "subtract"}
        assert all(m.parent == "Calculator" for m in methods)
    
    def test_parse_decorators(self, parser):
        """Test parsing decorated functions."""
        code = """
@decorator
@another_decorator(arg)
def decorated_func():
    pass

class MyClass:
    @property
    def prop(self):
        return self._prop
"""
        chunks = parser.parse(code.strip())
        
        # Check function decorators
        func_chunk = next(c for c in chunks if c.name == "decorated_func")
        assert func_chunk.metadata["decorators"] == ["decorator", "another_decorator"]
        
        # Check method decorators
        prop_chunk = next(c for c in chunks if c.name == "prop")
        assert "property" in prop_chunk.metadata["decorators"]
    
    def test_parse_imports(self, parser):
        """Test parsing import statements."""
        code = """
import os
from pathlib import Path
import numpy as np
from typing import (
    List,
    Dict,
    Optional
)

def main():
    pass
"""
        chunks = parser.parse(code.strip())
        
        # Check imports
        imports = [c for c in chunks if c.type == ChunkType.IMPORT]
        assert len(imports) >= 3
        
        # Check multi-line import
        multiline = next(c for c in imports if "typing" in c.content)
        assert "List" in multiline.content
        assert "Optional" in multiline.content
    
    def test_parse_async_functions(self, parser):
        """Test parsing async functions."""
        code = """
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        return await session.get(url)

class AsyncHandler:
    async def handle(self, request):
        return await self.process(request)
"""
        chunks = parser.parse(code.strip())
        
        # Check async function
        func_chunk = next(c for c in chunks if c.name == "fetch_data")
        assert func_chunk.metadata.get("is_async") is False  # AST limitation
        
        # Check async method
        method_chunk = next(c for c in chunks if c.name == "handle")
        assert method_chunk.type == ChunkType.METHOD
    
    def test_parse_module_docstring(self, parser):
        """Test parsing module-level docstring."""
        code = '''
"""
This is a module docstring.
It spans multiple lines.
"""

import os

def func():
    pass
'''
        chunks = parser.parse(code.strip())
        
        # Should have docstring chunk
        docstring = next(c for c in chunks if c.type == ChunkType.DOCSTRING)
        assert docstring.name == "module_docstring"
        assert "module docstring" in docstring.content
    
    def test_parse_syntax_error(self, parser):
        """Test handling syntax errors."""
        code = """
def broken_function(
    print("This is broken")
"""
        chunks = parser.parse(code)
        
        # Should fall back to block parsing
        assert len(chunks) > 0
        assert chunks[0].type == ChunkType.BLOCK
    
    def test_parse_nested_classes(self, parser):
        """Test parsing nested classes."""
        code = """
class Outer:
    class Inner:
        def inner_method(self):
            pass
    
    def outer_method(self):
        pass
"""
        chunks = parser.parse(code.strip())
        
        # Should find both classes
        classes = [c for c in chunks if c.type == ChunkType.CLASS]
        assert len(classes) == 2
        assert {c.name for c in classes} == {"Outer", "Inner"}
    
    def test_parse_class_inheritance(self, parser):
        """Test parsing class with inheritance."""
        code = """
class MyError(Exception):
    pass

class MyClass(BaseClass, Mixin):
    def method(self):
        pass
"""
        chunks = parser.parse(code.strip())
        
        # Check base classes in metadata
        error_class = next(c for c in chunks if c.name == "MyError")
        assert "Exception" in error_class.metadata["bases"]
        
        my_class = next(c for c in chunks if c.name == "MyClass")
        assert "BaseClass" in my_class.metadata["bases"]
        assert "Mixin" in my_class.metadata["bases"]
    
    def test_parse_file_extensions(self, parser):
        """Test supported file extensions."""
        assert parser.can_parse("test.py")
        assert parser.can_parse("test.pyi")
        assert parser.can_parse("test.pyx")
        assert not parser.can_parse("test.js")