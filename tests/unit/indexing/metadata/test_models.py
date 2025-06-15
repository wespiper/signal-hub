"""Tests for metadata models."""

import pytest
from datetime import datetime
from pathlib import Path

from signal_hub.indexing.metadata.models import (
    FileMetadata,
    ClassMetadata,
    FunctionMetadata,
    ImportMetadata,
    VariableMetadata,
    CodeMetadata,
    MetadataType
)


class TestMetadataModels:
    """Test metadata model validation and serialization."""
    
    def test_file_metadata_creation(self):
        """Test FileMetadata model creation."""
        metadata = FileMetadata(
            path=Path("src/example.py"),
            language="python",
            size_bytes=1024,
            last_modified=datetime.now(),
            encoding="utf-8",
            line_count=50
        )
        
        assert metadata.path == Path("src/example.py")
        assert metadata.language == "python"
        assert metadata.size_bytes == 1024
        assert metadata.line_count == 50
        
    def test_class_metadata_creation(self):
        """Test ClassMetadata model creation."""
        metadata = ClassMetadata(
            name="UserAuthentication",
            line_start=10,
            line_end=50,
            docstring="Handles user authentication.",
            bases=["BaseAuth", "Mixin"],
            decorators=["@dataclass"],
            methods=["login", "logout", "validate"]
        )
        
        assert metadata.name == "UserAuthentication"
        assert metadata.line_start == 10
        assert metadata.line_end == 50
        assert "BaseAuth" in metadata.bases
        assert "login" in metadata.methods
        
    def test_function_metadata_creation(self):
        """Test FunctionMetadata model creation."""
        metadata = FunctionMetadata(
            name="authenticate_user",
            line_start=15,
            line_end=30,
            docstring="Authenticate a user with credentials.",
            parameters=["username", "password"],
            returns="AuthToken",
            decorators=["@require_auth"],
            is_async=True,
            complexity=5
        )
        
        assert metadata.name == "authenticate_user"
        assert metadata.is_async is True
        assert metadata.complexity == 5
        assert "username" in metadata.parameters
        
    def test_import_metadata_creation(self):
        """Test ImportMetadata model creation."""
        metadata = ImportMetadata(
            module="django.contrib.auth",
            names=["authenticate", "login"],
            alias="auth",
            line_number=3,
            is_relative=False
        )
        
        assert metadata.module == "django.contrib.auth"
        assert "authenticate" in metadata.names
        assert metadata.alias == "auth"
        assert metadata.is_relative is False
        
    def test_code_metadata_aggregation(self):
        """Test CodeMetadata aggregation model."""
        file_metadata = FileMetadata(
            path=Path("src/auth.py"),
            language="python",
            size_bytes=2048,
            last_modified=datetime.now()
        )
        
        class_metadata = ClassMetadata(
            name="Authenticator",
            line_start=20,
            line_end=100
        )
        
        function_metadata = FunctionMetadata(
            name="login",
            line_start=25,
            line_end=40
        )
        
        code_metadata = CodeMetadata(
            file=file_metadata,
            classes=[class_metadata],
            functions=[function_metadata],
            imports=[],
            variables=[],
            dependencies={"django", "requests"},
            metadata_type=MetadataType.FULL
        )
        
        assert code_metadata.file.path == Path("src/auth.py")
        assert len(code_metadata.classes) == 1
        assert len(code_metadata.functions) == 1
        assert "django" in code_metadata.dependencies
        
    def test_metadata_serialization(self):
        """Test metadata serialization to dict."""
        metadata = FunctionMetadata(
            name="test_function",
            line_start=1,
            line_end=10,
            parameters=["arg1", "arg2"]
        )
        
        data = metadata.model_dump()
        assert data["name"] == "test_function"
        assert data["line_start"] == 1
        assert data["parameters"] == ["arg1", "arg2"]
        
    def test_metadata_validation(self):
        """Test metadata validation rules."""
        # Test invalid line range
        with pytest.raises(ValueError):
            FunctionMetadata(
                name="invalid",
                line_start=10,
                line_end=5  # End before start
            )
            
        # Test empty name
        with pytest.raises(ValueError):
            ClassMetadata(
                name="",  # Empty name
                line_start=1,
                line_end=10
            )