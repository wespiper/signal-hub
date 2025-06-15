"""Tests for metadata extractor."""

import pytest
from pathlib import Path
from datetime import datetime

from signal_hub.indexing.metadata.extractor import MetadataExtractor
from signal_hub.indexing.metadata.models import MetadataType


class TestMetadataExtractor:
    """Test metadata extractor functionality."""
    
    @pytest.fixture
    def extractor(self):
        """Create metadata extractor instance."""
        return MetadataExtractor()
        
    @pytest.fixture
    def python_code(self):
        """Sample Python code for testing."""
        return '''
"""Module for user authentication."""

import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

from django.contrib.auth import authenticate
from .models import User, AuthToken

# Constants
TOKEN_EXPIRY_HOURS = 24
SECRET_KEY = "your-secret-key"


class AuthenticationError(Exception):
    """Custom authentication exception."""
    pass


class UserAuthenticator:
    """Handles user authentication and token management."""
    
    def __init__(self, secret_key: str = SECRET_KEY):
        """Initialize authenticator with secret key."""
        self.secret_key = secret_key
        self._cache: Dict[str, User] = {}
        
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with credentials.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Check cache first
        if username in self._cache:
            return self._cache[username]
            
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            self._cache[username] = user
            return user
        return None
        
    def generate_token(self, user: User) -> str:
        """Generate JWT token for authenticated user."""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()


def validate_token(token: str, secret_key: str = SECRET_KEY) -> Optional[dict]:
    """Validate JWT token and return payload."""
    try:
        return jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None
'''
        
    @pytest.fixture
    def javascript_code(self):
        """Sample JavaScript code for testing."""
        return '''
// User authentication module
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { User } from './models';

const TOKEN_EXPIRY = '24h';
const SECRET_KEY = process.env.JWT_SECRET || 'default-secret';

/**
 * Authentication service class
 */
export class AuthService {
    constructor(secretKey = SECRET_KEY) {
        this.secretKey = secretKey;
        this.userCache = new Map();
    }
    
    /**
     * Authenticate user with credentials
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<User|null>} User object or null
     */
    async authenticateUser(email, password) {
        // Check cache
        if (this.userCache.has(email)) {
            return this.userCache.get(email);
        }
        
        const user = await User.findOne({ email });
        if (!user) return null;
        
        const isValid = await bcrypt.compare(password, user.passwordHash);
        if (isValid) {
            this.userCache.set(email, user);
            return user;
        }
        
        return null;
    }
    
    /**
     * Generate JWT token
     * @param {User} user - User object
     * @returns {string} JWT token
     */
    generateToken(user) {
        const payload = {
            userId: user.id,
            email: user.email,
        };
        
        return jwt.sign(payload, this.secretKey, { expiresIn: TOKEN_EXPIRY });
    }
    
    static async hashPassword(password) {
        return bcrypt.hash(password, 10);
    }
}

export const validateToken = (token, secretKey = SECRET_KEY) => {
    try {
        return jwt.verify(token, secretKey);
    } catch (error) {
        return null;
    }
};
'''
        
    def test_extract_python_metadata(self, extractor, python_code, tmp_path):
        """Test extracting metadata from Python code."""
        # Create test file
        test_file = tmp_path / "auth.py"
        test_file.write_text(python_code)
        
        # Extract metadata
        metadata = extractor.extract(test_file)
        
        # Verify file metadata
        assert metadata.file.path == test_file
        assert metadata.file.language == "python"
        assert metadata.file.line_count > 0
        
        # Verify classes
        assert len(metadata.classes) == 2
        auth_class = next(c for c in metadata.classes if c.name == "UserAuthenticator")
        assert auth_class.docstring == "Handles user authentication and token management."
        assert "authenticate_user" in auth_class.methods
        assert "generate_token" in auth_class.methods
        
        # Verify functions
        assert len(metadata.functions) >= 4  # Including class methods
        validate_func = next(f for f in metadata.functions if f.name == "validate_token")
        assert validate_func.parameters == ["token", "secret_key"]
        assert validate_func.returns == "Optional[dict]"
        
        # Verify imports
        assert any(imp.module == "hashlib" for imp in metadata.imports)
        assert any(imp.module == "jwt" for imp in metadata.imports)
        assert any(imp.module == "django.contrib.auth" for imp in metadata.imports)
        
        # Verify dependencies
        assert "hashlib" in metadata.dependencies
        assert "jwt" in metadata.dependencies
        assert "django" in metadata.dependencies
        
    def test_extract_javascript_metadata(self, extractor, javascript_code, tmp_path):
        """Test extracting metadata from JavaScript code."""
        # Create test file
        test_file = tmp_path / "auth.js"
        test_file.write_text(javascript_code)
        
        # Extract metadata
        metadata = extractor.extract(test_file)
        
        # Verify file metadata
        assert metadata.file.path == test_file
        assert metadata.file.language == "javascript"
        
        # Verify classes
        assert len(metadata.classes) == 1
        auth_class = metadata.classes[0]
        assert auth_class.name == "AuthService"
        assert "authenticateUser" in auth_class.methods
        assert "generateToken" in auth_class.methods
        
        # Verify functions
        validate_func = next(f for f in metadata.functions if f.name == "validateToken")
        assert validate_func.parameters == ["token", "secretKey"]
        
        # Verify imports
        assert any(imp.module == "bcrypt" for imp in metadata.imports)
        assert any(imp.module == "jsonwebtoken" for imp in metadata.imports)
        
        # Verify dependencies
        assert "bcrypt" in metadata.dependencies
        assert "jsonwebtoken" in metadata.dependencies
        
    def test_extract_with_metadata_type(self, extractor, python_code, tmp_path):
        """Test extracting with different metadata types."""
        test_file = tmp_path / "auth.py"
        test_file.write_text(python_code)
        
        # Full metadata
        full_metadata = extractor.extract(test_file, metadata_type=MetadataType.FULL)
        assert full_metadata.metadata_type == MetadataType.FULL
        assert len(full_metadata.functions) > 0
        assert len(full_metadata.variables) > 0
        
        # Basic metadata
        basic_metadata = extractor.extract(test_file, metadata_type=MetadataType.BASIC)
        assert basic_metadata.metadata_type == MetadataType.BASIC
        assert len(basic_metadata.classes) > 0
        assert len(basic_metadata.functions) > 0
        
        # Minimal metadata
        minimal_metadata = extractor.extract(test_file, metadata_type=MetadataType.MINIMAL)
        assert minimal_metadata.metadata_type == MetadataType.MINIMAL
        assert minimal_metadata.file is not None
        
    def test_extract_nonexistent_file(self, extractor):
        """Test extracting from non-existent file."""
        with pytest.raises(FileNotFoundError):
            extractor.extract(Path("nonexistent.py"))
            
    def test_extract_unsupported_language(self, extractor, tmp_path):
        """Test extracting from unsupported language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("some content")
        
        metadata = extractor.extract(test_file)
        assert metadata.file.language == "unknown"
        assert len(metadata.classes) == 0
        assert len(metadata.functions) == 0
        
    def test_search_metadata_conversion(self, extractor, python_code, tmp_path):
        """Test converting metadata to search format."""
        test_file = tmp_path / "test_auth.py"
        test_file.write_text(python_code)
        
        metadata = extractor.extract(test_file)
        search_metadata = metadata.to_search_metadata()
        
        assert search_metadata["file_path"] == str(test_file)
        assert search_metadata["language"] == "python"
        assert "UserAuthenticator" in search_metadata["classes"]
        assert "authenticate_user" in search_metadata["functions"]
        assert search_metadata["is_test_file"] is True  # Contains 'test' in path
        
    def test_extract_with_syntax_errors(self, extractor, tmp_path):
        """Test extracting from file with syntax errors."""
        test_file = tmp_path / "broken.py"
        test_file.write_text("""
def broken_function(
    # Missing closing parenthesis
    pass
    
class ValidClass:
    def method(self):
        return True
""")
        
        # Should handle gracefully and extract what it can
        metadata = extractor.extract(test_file)
        assert metadata.file.path == test_file
        # Should still find the valid class
        assert any(c.name == "ValidClass" for c in metadata.classes)