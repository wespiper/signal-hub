"""Unit tests for Markdown parser."""

import pytest
from pathlib import Path

from signal_hub.indexing.parsers.markdown import MarkdownParser
from signal_hub.indexing.parsers.models import ChunkType


class TestMarkdownParser:
    """Test MarkdownParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create Markdown parser."""
        return MarkdownParser()
    
    def test_parse_headings(self, parser):
        """Test parsing markdown with headings."""
        content = """# Main Title

This is the introduction.

## Section 1

Content for section 1.

## Section 2

Content for section 2.

### Subsection 2.1

Detailed content here.
"""
        chunks = parser.parse(content.strip())
        
        # Check headings
        headings = [c for c in chunks if c.type == ChunkType.HEADING]
        assert len(headings) == 1  # Only H1 is HEADING
        assert headings[0].name == "Main Title"
        
        # Check sections
        sections = [c for c in chunks if c.type == ChunkType.SECTION]
        assert len(sections) >= 3
        
        section_names = {s.name for s in sections}
        assert "Section 1" in section_names
        assert "Section 2" in section_names
        assert "Subsection 2.1" in section_names
    
    def test_parse_code_blocks(self, parser):
        """Test parsing code blocks."""
        content = '''# Code Examples

Here's some Python code:

```python
def hello():
    print("Hello, World!")
```

And some JavaScript:

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```

Some inline `code` too.
'''
        chunks = parser.parse(content.strip())
        
        # Check code blocks
        code_blocks = [c for c in chunks if c.type == ChunkType.CODE_BLOCK]
        assert len(code_blocks) == 2
        
        # Check Python code block
        python_block = next(c for c in code_blocks if "python" in c.name)
        assert 'print("Hello, World!")' in python_block.content
        assert python_block.metadata["code_language"] == "python"
        
        # Check JavaScript code block
        js_block = next(c for c in code_blocks if "javascript" in c.name)
        assert "console.log" in js_block.content
        assert js_block.metadata["code_language"] == "javascript"
    
    def test_parse_nested_sections(self, parser):
        """Test parsing nested heading levels."""
        content = """# Document

## Chapter 1

### Section 1.1

Content for 1.1

#### Subsection 1.1.1

Details here.

### Section 1.2

Content for 1.2

## Chapter 2

Different chapter.
"""
        chunks = parser.parse(content.strip())
        
        # Verify hierarchy is preserved
        sections = [c for c in chunks if c.type in (ChunkType.HEADING, ChunkType.SECTION)]
        
        # Check that sections contain appropriate content
        chapter1 = next(c for c in sections if c.name == "Chapter 1")
        assert "Section 1.1" in chapter1.content
        
        section11 = next(c for c in sections if c.name == "Section 1.1")
        assert "Content for 1.1" in section11.content
        assert "Subsection 1.1.1" in section11.content
    
    def test_parse_no_headings(self, parser):
        """Test parsing markdown without headings."""
        content = """This is just plain text.

With multiple paragraphs.

But no headings at all.
"""
        chunks = parser.parse(content.strip())
        
        # Should create one section for entire content
        assert len(chunks) == 1
        assert chunks[0].type == ChunkType.SECTION
        assert chunks[0].name == "main_content"
        assert "plain text" in chunks[0].content
    
    def test_parse_mixed_content(self, parser):
        """Test parsing markdown with mixed content."""
        content = '''# README

## Installation

```bash
npm install signal-hub
```

## Usage

```javascript
const hub = new SignalHub();
```

See [documentation](./docs) for more.

## Contributing

1. Fork the repo
2. Create a branch
3. Submit a PR
'''
        chunks = parser.parse(content.strip())
        
        # Should have heading, sections, and code blocks
        chunk_types = {c.type for c in chunks}
        assert ChunkType.HEADING in chunk_types
        assert ChunkType.SECTION in chunk_types
        assert ChunkType.CODE_BLOCK in chunk_types
        
        # Check code block languages
        code_blocks = [c for c in chunks if c.type == ChunkType.CODE_BLOCK]
        languages = {c.metadata["code_language"] for c in code_blocks}
        assert "bash" in languages
        assert "javascript" in languages
    
    def test_heading_metadata(self, parser):
        """Test heading level metadata."""
        content = """# H1
## H2
### H3
#### H4
##### H5
###### H6
"""
        chunks = parser.parse(content.strip())
        
        # Check heading levels
        h2 = next(c for c in chunks if c.name == "H2")
        assert h2.metadata["heading_level"] == 2
        
        h6 = next(c for c in chunks if c.name == "H6")
        assert h6.metadata["heading_level"] == 6
    
    def test_code_blocks_not_in_sections(self, parser):
        """Test that code blocks are extracted separately."""
        content = '''## Code Section

Here's the code:

```python
x = 42
```

More text after code.
'''
        chunks = parser.parse(content.strip())
        
        # Code block should be separate
        code_block = next(c for c in chunks if c.type == ChunkType.CODE_BLOCK)
        assert code_block.content == "x = 42"
        
        # Section should reference but not include code block content
        section = next(c for c in chunks if c.type == ChunkType.SECTION)
        assert "```python" not in section.content
    
    def test_parse_file_extensions(self, parser):
        """Test supported file extensions."""
        assert parser.can_parse("README.md")
        assert parser.can_parse("doc.markdown")
        assert parser.can_parse("component.mdx")
        assert not parser.can_parse("script.py")