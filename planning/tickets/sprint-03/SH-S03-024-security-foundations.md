# SH-S03-024: Security Foundations

## Summary
Implement foundational security features including API key management, rate limiting, and basic authentication to ensure Signal Hub is production-ready and secure.

## Background
As Signal Hub moves toward production use, we need basic security measures in place. This includes secure API key storage, rate limiting to prevent abuse, and authentication for the dashboard and management APIs.

## Requirements

### Functional Requirements
1. **API Key Management**
   - Secure storage of API keys (encrypted)
   - Support multiple providers (OpenAI, Anthropic)
   - Key rotation capability
   - Environment variable support

2. **Rate Limiting**
   - Per-user rate limits
   - Per-model rate limits
   - Configurable limits
   - Graceful limit handling

3. **Authentication**
   - Basic auth for dashboard
   - API token for management endpoints
   - Session management
   - Optional authentication

4. **Security Best Practices**
   - Input validation
   - SQL injection prevention
   - XSS protection
   - Secure headers

### Non-Functional Requirements
- Zero performance impact for normal use
- Clear security documentation
- Easy configuration
- Future-proof for Pro/Enterprise features

## Acceptance Criteria
- [ ] API keys stored securely
- [ ] Rate limiting working correctly
- [ ] Dashboard authentication implemented
- [ ] Management API protected
- [ ] Security headers configured
- [ ] Input validation complete
- [ ] Security documentation written
- [ ] Unit tests with >90% coverage
- [ ] Security scan passing

## Technical Design

### Components
```python
# src/signal_hub/security/
├── __init__.py
├── keys/
│   ├── __init__.py
│   ├── manager.py      # API key management
│   ├── storage.py      # Secure storage
│   └── rotation.py     # Key rotation
├── rate_limit/
│   ├── __init__.py
│   ├── limiter.py      # Rate limiting logic
│   ├── backends.py     # Storage backends
│   └── middleware.py   # HTTP middleware
├── auth/
│   ├── __init__.py
│   ├── basic.py        # Basic authentication
│   ├── tokens.py       # API tokens
│   └── session.py      # Session management
└── validation/
    ├── __init__.py
    └── inputs.py       # Input validation
```

### API Key Storage
```python
class SecureKeyManager:
    def __init__(self, key_file: Path):
        self.key_file = key_file
        self.cipher = Fernet(self._get_or_create_master_key())
    
    def set_key(self, provider: str, key: str):
        """Encrypt and store API key."""
        encrypted = self.cipher.encrypt(key.encode())
        self._save_key(provider, encrypted)
    
    def get_key(self, provider: str) -> str:
        """Retrieve and decrypt API key."""
        encrypted = self._load_key(provider)
        return self.cipher.decrypt(encrypted).decode()
```

### Rate Limiting
```python
class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.backend = self._create_backend()
    
    async def check_limit(self, key: str, cost: int = 1) -> bool:
        """Check if request is within rate limit."""
        current = await self.backend.get_usage(key)
        limit = self.config.get_limit(key)
        
        if current + cost > limit:
            raise RateLimitExceeded(key, limit, current)
            
        await self.backend.increment(key, cost)
        return True
```

## Implementation Tasks
- [ ] Create security module structure
- [ ] Implement secure key storage
- [ ] Build key rotation system
- [ ] Create rate limiter
- [ ] Implement rate limit backends
- [ ] Add authentication system
- [ ] Build session management
- [ ] Create input validators
- [ ] Add security middleware
- [ ] Configure security headers
- [ ] Write security tests
- [ ] Security documentation
- [ ] Security audit

## Dependencies
- Cryptography library (Fernet)
- Redis or in-memory cache for rate limiting
- Session storage

## Configuration
```yaml
security:
  api_keys:
    storage: "encrypted_file"
    key_file: "~/.signal-hub/keys.enc"
    rotation_days: 90
    
  rate_limiting:
    enabled: true
    backend: "memory"  # or "redis"
    limits:
      default: 1000  # requests per hour
      by_model:
        haiku: 5000
        sonnet: 1000
        opus: 100
        
  authentication:
    dashboard:
      enabled: true
      type: "basic"  # or "disabled"
      users:
        admin: "$2b$12$..."  # bcrypt hash
    api:
      enabled: true
      token_header: "X-API-Token"
```

## Security Checklist
- [ ] API keys never logged
- [ ] Rate limits documented
- [ ] Auth bypass not possible
- [ ] Input validation complete
- [ ] SQL injection prevented
- [ ] XSS protection enabled
- [ ] CORS configured correctly
- [ ] Security headers set

## Testing Strategy
1. **Unit Tests**: Each security component
2. **Integration Tests**: Full auth flow
3. **Security Tests**: Penetration testing
4. **Load Tests**: Rate limiter under load

## Risks & Mitigations
- **Risk**: API key exposure
  - **Mitigation**: Encryption, secure storage, rotation
- **Risk**: Rate limit bypass
  - **Mitigation**: Multiple check points, fail closed
- **Risk**: Authentication weakness
  - **Mitigation**: Industry standards, regular updates

## Success Metrics
- Zero security incidents
- <1ms security check overhead
- 100% of endpoints protected
- Clear security documentation

## Notes
- Keep security simple but effective
- Design for Pro/Enterprise enhancements
- Regular security audits
- Clear documentation critical