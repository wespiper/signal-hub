# Contributing to Signal Hub

Thank you for your interest in contributing to Signal Hub! We welcome contributions from the community and are grateful for any help you can provide.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat all contributors with respect and kindness.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in our [issue tracker](https://github.com/wespiper/signal-hub/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (if applicable)
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)

### Suggesting Features

1. Check our [roadmap](docs/INITIAL_mcp_rag_plan.md) and existing issues
2. Open a discussion in the GitHub Discussions tab
3. Provide detailed use case and benefits

### Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding standards
4. Write or update tests as needed
5. Run the test suite (`make test`)
6. Commit your changes with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/wespiper/signal-hub.git
cd signal-hub

# Install development dependencies
make dev-install

# Run tests
make test

# Check code quality
make lint
make type-check
```

## Coding Standards

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines
- Write tests for new functionality

## Testing

- Write unit tests for all new code
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use meaningful test names that describe what's being tested

## Pull Request Process

1. Update documentation for any changed functionality
2. Ensure all tests pass and coverage doesn't decrease
3. Update the CHANGELOG.md with your changes
4. Get review from at least one maintainer
5. Squash commits before merging

## Questions?

Feel free to reach out:
- Discord: [Signal Hub Community](https://discord.gg/signalhub)
- GitHub Discussions
- Email: contribute@signalhub.ai

Thank you for helping make Signal Hub better!