"""Input validation for security."""

import re
from pathlib import Path
from typing import Any, List, Optional, Union

from signal_hub.utils.logging import get_logger


logger = get_logger(__name__)


class ValidationError(Exception):
    """Input validation error."""
    pass


class InputValidator:
    """Validates and sanitizes user inputs."""
    
    # Patterns for validation
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\.[/\\]")
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|"
        r"script|declare|cast|convert|having|group by|order by)\b|--|;|'|\"|\\x00)",
        re.IGNORECASE
    )
    XSS_PATTERN = re.compile(
        r"(<script|<iframe|javascript:|onerror=|onload=|onclick=|<img\s+src=)",
        re.IGNORECASE
    )
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            Validated username
            
        Raises:
            ValidationError: If invalid
        """
        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3-32 characters, alphanumeric, underscore, or hyphen only"
            )
        return username
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Validated email (lowercase)
            
        Raises:
            ValidationError: If invalid
        """
        email = email.strip().lower()
        if not cls.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        return email
    
    @classmethod
    def validate_path(cls, path: Union[str, Path], base_path: Optional[Path] = None) -> Path:
        """
        Validate file path (prevent traversal).
        
        Args:
            path: Path to validate
            base_path: Base path to restrict to
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If invalid
        """
        path_str = str(path)
        
        # Check for path traversal
        if cls.PATH_TRAVERSAL_PATTERN.search(path_str):
            raise ValidationError("Path traversal detected")
        
        # Convert to Path
        path_obj = Path(path_str).resolve()
        
        # Check if within base path
        if base_path:
            base_path = Path(base_path).resolve()
            try:
                path_obj.relative_to(base_path)
            except ValueError:
                raise ValidationError(f"Path must be within {base_path}")
        
        return path_obj
    
    @classmethod
    def sanitize_query(cls, query: str, max_length: int = 10000) -> str:
        """
        Sanitize search query.
        
        Args:
            query: Query string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized query
            
        Raises:
            ValidationError: If suspicious patterns detected
        """
        # Check length
        if len(query) > max_length:
            raise ValidationError(f"Query too long (max {max_length} characters)")
        
        # Check for SQL injection patterns
        if cls.SQL_INJECTION_PATTERN.search(query):
            logger.warning(f"Potential SQL injection attempt: {query[:100]}")
            raise ValidationError("Invalid query syntax")
        
        # Check for XSS patterns
        if cls.XSS_PATTERN.search(query):
            logger.warning(f"Potential XSS attempt: {query[:100]}")
            raise ValidationError("Invalid query content")
        
        # Basic sanitization
        query = query.strip()
        
        return query
    
    @classmethod
    def validate_json_field(
        cls,
        data: dict,
        field: str,
        field_type: type,
        required: bool = True,
        default: Any = None
    ) -> Any:
        """
        Validate JSON field.
        
        Args:
            data: JSON data dict
            field: Field name
            field_type: Expected type
            required: Whether field is required
            default: Default value if not required
            
        Returns:
            Field value
            
        Raises:
            ValidationError: If invalid
        """
        if field not in data:
            if required:
                raise ValidationError(f"Missing required field: {field}")
            return default
        
        value = data[field]
        
        if not isinstance(value, field_type):
            raise ValidationError(
                f"Field '{field}' must be {field_type.__name__}, got {type(value).__name__}"
            )
        
        return value
    
    @classmethod
    def validate_enum(cls, value: str, allowed: List[str], field_name: str = "value") -> str:
        """
        Validate enum/choice field.
        
        Args:
            value: Value to validate
            allowed: List of allowed values
            field_name: Field name for error message
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If not in allowed list
        """
        if value not in allowed:
            raise ValidationError(
                f"Invalid {field_name}: '{value}'. Must be one of: {', '.join(allowed)}"
            )
        return value
    
    @classmethod
    def validate_integer(
        cls,
        value: Union[int, str],
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        field_name: str = "value"
    ) -> int:
        """
        Validate integer value.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Field name for error message
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If invalid
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
        
        return int_value
    
    @classmethod
    def escape_html(cls, text: str) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text