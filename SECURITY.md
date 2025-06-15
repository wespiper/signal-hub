# Security Policy

## Supported Versions

Signal Hub is currently in active development. We support the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in Signal Hub, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security@signalhub.ai with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### What to Expect

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Timeline**: Varies based on severity

### Security Best Practices

When using Signal Hub:

1. **API Keys**: Never commit API keys or credentials
2. **Environment Variables**: Use `.env` files (never commit them)
3. **Dependencies**: Keep dependencies updated
4. **Access Control**: Follow principle of least privilege
5. **Data Storage**: Be mindful of what data you index

### Vulnerability Handling Process

1. **Assessment**: We'll assess the severity and impact
2. **Fix Development**: Create a fix without revealing the vulnerability
3. **Testing**: Thoroughly test the fix
4. **Release**: Deploy fix and notify users
5. **Disclosure**: Coordinate disclosure after users have updated

### Recognition

We appreciate responsible disclosure and will acknowledge security researchers who help improve Signal Hub's security.

## Security Features

Signal Hub includes several security features:

- Secure API key handling
- Input validation and sanitization
- Rate limiting capabilities
- Audit logging support
- Encrypted data storage options

For questions about security features, please refer to our documentation or contact security@signalhub.ai.