# Repository Settings Documentation

This document details the configuration and settings for the Signal Hub GitHub repository.

## Repository Information

- **URL**: https://github.com/wespiper/signal-hub
- **Visibility**: Public
- **License**: MIT
- **Default Branch**: main
- **Description**: Intelligent developer assistant that extends Claude's context through MCP+RAG

## Branch Protection Rules (main branch)

### Status Checks
- **Required status checks before merging**: Yes
- **Strict status checks**: Yes (must be up to date with base branch)
- **Required checks**: 
  - `test` - Must pass all tests before merge

### Pull Request Reviews
- **Required approving reviews**: 1
- **Dismiss stale reviews**: Yes (when new commits are pushed)
- **Require review from code owners**: No
- **Require approval of most recent push**: No

### Protection Settings
- **Include administrators**: No (admins can bypass)
- **Allow force pushes**: No
- **Allow deletions**: No
- **Require conversation resolution**: Yes
- **Require signed commits**: No
- **Require linear history**: No
- **Lock branch**: No

## GitHub Actions

### CI Workflow (.github/workflows/ci.yml)
The CI pipeline runs on:
- Every push to main branch
- Every pull request targeting main
- Daily at 2 AM UTC (for link checking)

#### Jobs:
1. **Test** - Runs on Python 3.11 and 3.12
   - Installs dependencies with Poetry
   - Runs pytest with coverage
   - Uploads coverage to Codecov

2. **Lint** - Code quality checks
   - Black (formatting)
   - Ruff (linting)
   - Mypy (type checking)

3. **Link Check** - Validates all links in documentation
   - Uses Lychee to check markdown and YAML files
   - Accepts 200, 204, 301, 302 status codes
   - Uploads report on failure

4. **Security** - Vulnerability scanning
   - Uses Trivy to scan for security issues
   - Reports CRITICAL and HIGH severity issues
   - Uploads results to GitHub Security tab

5. **Build** - Package distribution
   - Builds Python package with Poetry
   - Validates package with twine
   - Stores artifacts for release

## Issue Templates

### Bug Report (.github/ISSUE_TEMPLATE/bug_report.md)
- Title: [BUG] 
- Labels: bug
- Fields: Description, Steps to Reproduce, Expected Behavior, Environment

### Feature Request (.github/ISSUE_TEMPLATE/feature_request.md)
- Title: [FEATURE]
- Labels: enhancement
- Fields: Problem Statement, Proposed Solution, Alternatives, Additional Context

### Question (.github/ISSUE_TEMPLATE/question.md)
- Title: [QUESTION]
- Labels: question
- Fields: Question, Context, What You've Tried

## Pull Request Template

Located at `.github/PULL_REQUEST_TEMPLATE.md`:
- Checklist for code quality
- Test requirements
- Documentation updates
- Link to related issues

## Community Files

### Code of Conduct (CODE_OF_CONDUCT.md)
- Contributor Covenant v2.1
- Enforcement guidelines
- Reporting instructions

### Contributing Guidelines (CONTRIBUTING.md)
- Development setup instructions
- Code style requirements
- Testing requirements
- Pull request process

### Security Policy (SECURITY.md)
- Supported versions
- Vulnerability reporting process
- Security update policy

## Repository Features

### Enabled Features
- ✅ Issues
- ✅ Projects
- ✅ Wiki
- ✅ Discussions
- ✅ Actions
- ✅ Security advisories
- ✅ Dependency graph
- ✅ Dependabot alerts

### Merge Options
- ✅ Allow merge commits
- ✅ Allow squash merging
- ✅ Allow rebase merging
- ✅ Automatically delete head branches

## Access and Permissions

### Collaborators
- Repository owner: @wespiper
- Additional collaborators can be added as needed

### Team Access
- Currently individual repository
- Can be moved to organization for team management

## Webhooks and Integrations

### Current Integrations
- GitHub Actions (CI/CD)
- Codecov (test coverage)
- Dependabot (dependency updates)

### Recommended Future Integrations
- Discord webhook for community notifications
- Documentation hosting (GitHub Pages or ReadTheDocs)
- Package publishing automation (PyPI)

## Maintenance Schedule

### Automated Tasks
- Daily link checking (2 AM UTC)
- Dependabot security updates (weekly)
- Dependabot version updates (monthly)

### Manual Reviews
- Security advisories (as reported)
- Community health files (quarterly)
- CI/CD pipeline optimization (monthly)

## Repository Badges

Recommended badges for README:
```markdown
![CI](https://github.com/wespiper/signal-hub/workflows/CI/badge.svg)
![Coverage](https://codecov.io/gh/wespiper/signal-hub/branch/main/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/github/license/wespiper/signal-hub)
![GitHub release](https://img.shields.io/github/release/wespiper/signal-hub.svg)
```

## Backup and Recovery

### Backup Strategy
- Git distributed nature provides inherent backup
- Consider periodic full repository exports
- Document any external dependencies

### Recovery Plan
1. Clone from any developer's local copy
2. Re-enable branch protection
3. Restore CI/CD secrets
4. Verify all integrations

---

Last Updated: 2025-06-15