# Contributing to Signal Hub

Thank you for your interest in contributing to Signal Hub! We're excited to have you join our community. This guide will help you get started.

## 🎯 Ways to Contribute

There are many ways to contribute to Signal Hub:

- **Report bugs** and help us improve stability
- **Suggest features** to make Signal Hub even better
- **Improve documentation** to help other users
- **Submit code** to fix bugs or add features
- **Answer questions** in discussions and issues
- **Share your experience** with blog posts or tutorials

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/signal-hub.git
cd signal-hub
git remote add upstream https://github.com/wespiper/signal-hub.git
```

### 2. Set Up Development Environment

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

## 📝 Development Workflow

### Code Style

We use automated formatting and linting:

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# All checks
make quality
```

### Testing

Always write tests for new features:

```bash
# Run all tests
make test

# Run specific test
pytest tests/unit/test_your_feature.py -v

# Check coverage
make test-coverage
```

### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Longer explanation if needed.

Closes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

## 🐛 Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug template** when creating issues
3. **Include minimal reproduction** steps
4. **Provide environment details**
5. **Attach relevant logs** or screenshots

## 💡 Suggesting Features

1. **Check the roadmap** in planning docs
2. **Search existing suggestions**
3. **Use feature request template**
4. **Explain the use case** clearly
5. **Consider Signal Hub's goals**

## 🔧 Submitting Pull Requests

### Before Submitting

- [ ] Tests pass locally (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Type hints added for new code
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md entry added
- [ ] Commit messages follow convention

### PR Process

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Describe changes clearly
   - Include screenshots if UI changes

3. **Respond to Reviews**
   - Address feedback promptly
   - Push additional commits
   - Mark conversations resolved

4. **After Merge**
   - Delete your feature branch
   - Update your local main
   - Celebrate! 🎉

## 🏗️ Architecture Guidelines

### Adding New Features

1. **Check if it belongs in Basic or Pro edition**
   - Basic: Core functionality, essential features
   - Pro: Advanced features, optimizations

2. **Use the plugin system for Pro features**
   ```python
   from signal_hub.core.plugins import PluginBase
   
   class MyProFeature(PluginBase):
       edition = "pro"
   ```

3. **Follow existing patterns**
   - Look at similar features
   - Maintain consistency
   - Use dependency injection

### Performance Considerations

- Profile before optimizing
- Batch operations when possible
- Use async/await appropriately
- Consider memory usage
- Add benchmarks for critical paths

## 📚 Documentation

### When to Update Docs

- Adding new features
- Changing behavior
- Fixing confusing sections
- Adding examples
- Updating configuration

### Documentation Style

- Use clear, simple language
- Include code examples
- Add screenshots for UI
- Link to related sections
- Test all examples

## 🧪 Testing Guidelines

### Test Structure

```python
class TestFeatureName:
    """Test suite for FeatureName."""
    
    def test_normal_case(self):
        """Test normal expected behavior."""
        pass
    
    def test_edge_case(self):
        """Test boundary conditions."""
        pass
    
    def test_error_handling(self):
        """Test error scenarios."""
        pass
```

### Test Coverage

- Aim for >80% coverage
- Test happy paths and errors
- Include integration tests
- Add performance tests for critical code

## 🤝 Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing private information
- Other unprofessional conduct

## 📞 Getting Help

- **Discord**: Join our [community server](https://discord.gg/signalhub)
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: For bugs and feature requests
- **Email**: core-team@signalhub.ai for sensitive matters

## 🏆 Recognition

We value all contributions! Contributors are:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in commits
- Invited to contributor events
- Eligible for swag (coming soon!)

## 📋 Checklist for New Contributors

- [ ] Read this guide completely
- [ ] Set up development environment
- [ ] Join Discord community
- [ ] Find a "good first issue"
- [ ] Make your first PR
- [ ] Celebrate your contribution!

## 🔗 Useful Links

- [Architecture Overview](docs/architecture/overview.md)
- [Development Setup](docs/development-setup.md)
- [Testing Strategy](planning/testing-strategy.md)
- [Sprint Planning](planning/README.md)
- [API Documentation](docs/api-reference/)

---

Thank you for contributing to Signal Hub! Every contribution, no matter how small, helps make the project better for everyone. 🙏