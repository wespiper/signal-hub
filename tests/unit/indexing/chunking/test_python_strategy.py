"""Tests for Python chunking strategy."""

import pytest
from pathlib import Path

from signal_hub.indexing.chunking import ChunkingContext, ChunkType
from signal_hub.indexing.chunking.strategies import PythonChunkingStrategy


class TestPythonChunkingStrategy:
    """Test Python-specific chunking."""
    
    @pytest.fixture
    def strategy(self):
        """Create Python chunking strategy."""
        context = ChunkingContext(
            max_chunk_size=500,
            min_chunk_size=50,
            overlap_size=2,  # 2 lines overlap
            preserve_context=True
        )
        return PythonChunkingStrategy(context)
        
    @pytest.fixture
    def python_code(self):
        """Sample Python code for testing."""
        return '''
"""Module docstring explaining the purpose."""

import os
import sys
from typing import List, Optional

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


class DataProcessor:
    """Process data with various transformations."""
    
    def __init__(self, config: dict):
        """Initialize processor with configuration."""
        self.config = config
        self._cache = {}
        
    def process(self, data: List[str]) -> List[str]:
        """Process a list of data items.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data items
        """
        results = []
        for item in data:
            processed = self._transform(item)
            results.append(processed)
        return results
        
    def _transform(self, item: str) -> str:
        """Transform a single item."""
        # Apply transformations
        item = item.strip().lower()
        item = item.replace(' ', '_')
        return item
        
    @staticmethod
    def validate(data: List[str]) -> bool:
        """Validate input data."""
        return all(isinstance(item, str) for item in data)


def main():
    """Main entry point."""
    processor = DataProcessor({'debug': True})
    
    test_data = ["Hello World", "Test Data", "Python Code"]
    results = processor.process(test_data)
    
    for result in results:
        print(f"Processed: {result}")
        

if __name__ == "__main__":
    main()
'''
        
    def test_can_handle_python_files(self, strategy):
        """Test file type detection."""
        assert strategy.can_handle(Path("test.py"))
        assert strategy.can_handle(Path("test.pyi"))
        assert not strategy.can_handle(Path("test.js"))
        assert not strategy.can_handle(Path("test.txt"))
        
    def test_chunk_simple_function(self, strategy):
        """Test chunking a simple function."""
        code = '''
def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
'''
        chunks = strategy.chunk_text(code)
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.FUNCTION
        assert "def hello" in chunks[0].content
        assert chunks[0].metadata.get("function_name") == "hello"
        
    def test_chunk_class_with_methods(self, strategy, python_code):
        """Test chunking a class into separate methods."""
        chunks = strategy.chunk_text(python_code)
        
        # Should have chunks for imports, class, methods, and top-level function
        chunk_types = [c.chunk_type for c in chunks]
        assert ChunkType.MODULE in chunk_types  # Module docstring + imports
        assert ChunkType.CLASS in chunk_types
        assert ChunkType.METHOD in chunk_types
        assert ChunkType.FUNCTION in chunk_types
        
        # Find the class chunk
        class_chunks = [c for c in chunks if c.chunk_type == ChunkType.CLASS]
        assert len(class_chunks) >= 1
        assert "class DataProcessor" in class_chunks[0].content
        
        # Find method chunks
        method_chunks = [c for c in chunks if c.chunk_type == ChunkType.METHOD]
        assert len(method_chunks) >= 3  # __init__, process, _transform
        
        # Check parent context
        for method in method_chunks:
            assert method.parent_context == "DataProcessor"
            
    def test_chunk_size_limits(self, strategy):
        """Test respecting chunk size limits."""
        # Create a very long function
        long_function = '''
def very_long_function():
    """This is a very long function."""
''' + '\n'.join([f'    print("Line {i}")' for i in range(100)])
        
        chunks = strategy.chunk_text(long_function)
        
        # Should be split into multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should respect size limits
        for chunk in chunks:
            assert chunk.size <= strategy.context.max_chunk_size
            
    def test_preserve_context_with_overlap(self, strategy):
        """Test context preservation with overlap."""
        code = '''
class MyClass:
    def method1(self):
        line1()
        line2()
        
    def method2(self):
        line3()
        line4()
'''
        chunks = strategy.chunk_text(code)
        
        # Apply overlap
        overlapped = strategy.apply_overlap(chunks)
        
        # Check that overlap was applied
        for i, chunk in enumerate(overlapped):
            if i > 0:
                # Should have some overlap with previous
                assert chunk.overlap_with_previous > 0 or strategy.context.overlap_size == 0
                
    def test_handle_nested_classes(self, strategy):
        """Test handling nested classes."""
        code = '''
class Outer:
    """Outer class."""
    
    class Inner:
        """Inner class."""
        
        def inner_method(self):
            """Method in inner class."""
            pass
            
    def outer_method(self):
        """Method in outer class."""
        pass
'''
        chunks = strategy.chunk_text(code)
        
        # Should handle nested structure
        inner_methods = [c for c in chunks 
                        if c.chunk_type == ChunkType.METHOD 
                        and c.parent_context == "Outer.Inner"]
        assert len(inner_methods) == 1
        
    def test_handle_decorators(self, strategy):
        """Test handling decorated functions."""
        code = '''
@decorator
@another_decorator(param=True)
def decorated_function():
    """A decorated function."""
    return "result"
'''
        chunks = strategy.chunk_text(code)
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.FUNCTION
        # Decorators should be included
        assert "@decorator" in chunks[0].content
        assert "@another_decorator" in chunks[0].content
        
    def test_handle_async_functions(self, strategy):
        """Test handling async functions."""
        code = '''
async def async_function():
    """An async function."""
    await some_operation()
    return "done"
'''
        chunks = strategy.chunk_text(code)
        
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.FUNCTION
        assert chunks[0].metadata.get("is_async") is True
        
    def test_imports_and_constants_grouping(self, strategy):
        """Test that imports and constants are grouped."""
        code = '''
import os
import sys
from pathlib import Path

# Constants
TIMEOUT = 30
MAX_SIZE = 1000

# Another constant
DEBUG = True

def function():
    pass
'''
        chunks = strategy.chunk_text(code)
        
        # First chunk should contain imports and constants
        assert chunks[0].chunk_type == ChunkType.MODULE
        assert "import os" in chunks[0].content
        assert "TIMEOUT = 30" in chunks[0].content
        assert "DEBUG = True" in chunks[0].content
        
    def test_handle_multiline_strings(self, strategy):
        """Test handling functions with multiline strings."""
        code = '''
def sql_query():
    """Execute a SQL query."""
    query = """
        SELECT *
        FROM users
        WHERE active = true
        ORDER BY created_at DESC
    """
    return execute(query)
'''
        chunks = strategy.chunk_text(code)
        
        assert len(chunks) == 1
        # Multiline string should be kept intact
        assert "SELECT *" in chunks[0].content
        assert "ORDER BY created_at DESC" in chunks[0].content
        
    def test_syntax_validation(self, strategy):
        """Test syntax validation of chunks."""
        code = '''
def valid_function():
    return True
    
def another_function():
    return False
'''
        chunks = strategy.chunk_text(code)
        
        # Each chunk should be valid Python
        for chunk in chunks:
            if chunk.chunk_type == ChunkType.FUNCTION:
                # Should be able to compile
                try:
                    compile(chunk.content, '<string>', 'exec')
                    valid = True
                except SyntaxError:
                    valid = False
                assert valid or chunk.is_valid_syntax is False