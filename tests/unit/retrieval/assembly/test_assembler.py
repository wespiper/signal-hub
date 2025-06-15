"""Tests for context assembly."""

import pytest
from typing import List

from signal_hub.retrieval.assembly import (
    ContextAssembler,
    AssemblyConfig,
    AssembledContext,
    ContextSection
)
from signal_hub.retrieval.search import SearchResult


class TestContextAssembler:
    """Test context assembly functionality."""
    
    @pytest.fixture
    def assembler(self):
        """Create context assembler with default config."""
        config = AssemblyConfig(
            max_tokens=8000,
            dedup_threshold=0.85,
            preserve_relationships=True,
            include_imports=True,
            format_style="claude_optimized"
        )
        return ContextAssembler(config)
        
    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results for testing."""
        return [
            SearchResult(
                id="1",
                text='def authenticate_user(username: str, password: str) -> Optional[User]:\n    """Authenticate a user."""\n    user = get_user(username)\n    if verify_password(password, user.password_hash):\n        return user\n    return None',
                score=0.95,
                metadata={
                    "file_path": "auth/authenticator.py",
                    "start_line": 45,
                    "end_line": 52,
                    "chunk_type": "function",
                    "function_name": "authenticate_user"
                }
            ),
            SearchResult(
                id="2",
                text='import hashlib\nimport secrets\nfrom typing import Optional\nfrom models import User',
                score=0.75,
                metadata={
                    "file_path": "auth/authenticator.py",
                    "start_line": 1,
                    "end_line": 4,
                    "chunk_type": "module",
                    "contains": "imports"
                }
            ),
            SearchResult(
                id="3",
                text='def verify_password(password: str, password_hash: str) -> bool:\n    """Verify a password against its hash."""\n    return hashlib.sha256(password.encode()).hexdigest() == password_hash',
                score=0.85,
                metadata={
                    "file_path": "auth/utils.py",
                    "start_line": 12,
                    "end_line": 15,
                    "chunk_type": "function",
                    "function_name": "verify_password"
                }
            ),
            SearchResult(
                id="4",
                text='class User:\n    """User model."""\n    def __init__(self, username: str, password_hash: str):\n        self.username = username\n        self.password_hash = password_hash',
                score=0.70,
                metadata={
                    "file_path": "models.py",
                    "start_line": 5,
                    "end_line": 10,
                    "chunk_type": "class",
                    "class_name": "User"
                }
            ),
        ]
        
    def test_basic_assembly(self, assembler, sample_search_results):
        """Test basic context assembly."""
        query = "user authentication flow"
        context = assembler.assemble(sample_search_results, query)
        
        assert isinstance(context, AssembledContext)
        assert len(context.sections) > 0
        assert context.token_count > 0
        assert context.token_count <= assembler.config.max_tokens
        
    def test_deduplication(self, assembler):
        """Test deduplication of similar content."""
        # Create results with duplicate content
        results = [
            SearchResult(
                id="1",
                text="def foo():\n    return 42",
                score=0.9,
                metadata={"file_path": "a.py", "start_line": 1}
            ),
            SearchResult(
                id="2",
                text="def foo():\n    return 42",  # Exact duplicate
                score=0.85,
                metadata={"file_path": "b.py", "start_line": 10}
            ),
            SearchResult(
                id="3",
                text="def foo():\n    return 42\n    # Extra comment",  # Near duplicate
                score=0.8,
                metadata={"file_path": "c.py", "start_line": 20}
            ),
        ]
        
        context = assembler.assemble(results, "foo function")
        
        # Should deduplicate exact and near duplicates
        assert len(context.sections) < len(results)
        
    def test_relationship_detection(self, assembler, sample_search_results):
        """Test detection of relationships between chunks."""
        context = assembler.assemble(sample_search_results, "authentication")
        
        # Should find relationships
        assert len(context.relationships) > 0
        
        # Should detect that authenticate_user calls verify_password
        auth_relationships = [r for r in context.relationships 
                            if r.from_entity == "authenticate_user"]
        assert len(auth_relationships) > 0
        
    def test_file_grouping(self, assembler, sample_search_results):
        """Test that chunks from same file are grouped."""
        context = assembler.assemble(sample_search_results, "authentication")
        
        # Find sections from auth/authenticator.py
        auth_file_sections = [s for s in context.sections 
                            if s.source_file == "auth/authenticator.py"]
        
        # Should group imports with functions from same file
        assert len(auth_file_sections) >= 2
        
    def test_ordering(self, assembler, sample_search_results):
        """Test proper ordering of context sections."""
        context = assembler.assemble(sample_search_results, "authentication")
        
        # Imports should come before implementations
        import_indices = [i for i, s in enumerate(context.sections) 
                         if s.content_type == "imports"]
        function_indices = [i for i, s in enumerate(context.sections) 
                          if s.content_type == "function"]
        
        if import_indices and function_indices:
            # At least one import should come before functions
            assert min(import_indices) < max(function_indices)
            
    def test_token_limit(self, assembler):
        """Test respecting token limits."""
        # Create many large results
        results = []
        for i in range(100):
            results.append(SearchResult(
                id=str(i),
                text="x" * 1000,  # 1000 chars each
                score=0.9 - i * 0.001,
                metadata={"file_path": f"file{i}.py"}
            ))
            
        context = assembler.assemble(results, "test")
        
        # Should respect token limit
        assert context.token_count <= assembler.config.max_tokens
        
        # Should prioritize higher scoring results
        assert len(context.sections) < len(results)
        
    def test_format_styles(self, assembler, sample_search_results):
        """Test different formatting styles."""
        # Claude optimized format
        assembler.config.format_style = "claude_optimized"
        context_claude = assembler.assemble(sample_search_results, "auth")
        
        # Markdown format
        assembler.config.format_style = "markdown"
        context_markdown = assembler.assemble(sample_search_results, "auth")
        
        # Should have different formatting
        assert context_claude.format_style == "claude_optimized"
        assert context_markdown.format_style == "markdown"
        
    def test_imports_handling(self, assembler, sample_search_results):
        """Test special handling of imports."""
        # With imports
        assembler.config.include_imports = True
        context_with = assembler.assemble(sample_search_results, "auth")
        
        # Without imports
        assembler.config.include_imports = False
        context_without = assembler.assemble(sample_search_results, "auth")
        
        # Should have different number of sections
        import_sections_with = [s for s in context_with.sections 
                              if "import" in s.content_type]
        import_sections_without = [s for s in context_without.sections 
                                 if "import" in s.content_type]
        
        assert len(import_sections_with) > len(import_sections_without)
        
    def test_empty_results(self, assembler):
        """Test handling empty search results."""
        context = assembler.assemble([], "test query")
        
        assert len(context.sections) == 0
        assert context.token_count == 0
        assert len(context.relationships) == 0
        
    def test_metadata_preservation(self, assembler, sample_search_results):
        """Test that metadata is preserved in assembly."""
        context = assembler.assemble(sample_search_results, "auth")
        
        # Check that sections preserve metadata
        for section in context.sections:
            assert section.source_file is not None
            assert section.start_line is not None
            assert section.end_line is not None
            
    def test_context_summary(self, assembler, sample_search_results):
        """Test context summary generation."""
        context = assembler.assemble(sample_search_results, "authentication")
        
        # Should generate summary
        assert context.summary is not None
        assert len(context.summary) > 0
        
        # Summary should mention key components
        assert "authenticate" in context.summary.lower() or "auth" in context.summary.lower()