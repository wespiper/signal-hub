# SH-S04-026: Interactive Tutorials & Examples

## Summary
Create hands-on tutorials and real-world example projects that demonstrate Signal Hub's capabilities, helping users understand practical applications and best practices.

## Background
While documentation explains features, users learn best through practical examples. We need interactive tutorials that guide users through common use cases and showcase Signal Hub's power.

## Requirements

### Functional Requirements
1. **Interactive Tutorials**
   - "Index Your First Repository" (15 min)
   - "Smart Routing in Action" (20 min)
   - "Optimizing Costs with Caching" (15 min)
   - "Building Custom Tools" (30 min)

2. **Example Projects**
   - Small project indexing (Python web app)
   - Large monorepo handling
   - Multi-language project
   - Custom tool integration

3. **Video Tutorials**
   - Installation walkthrough (5 min)
   - Feature overview (10 min)
   - Advanced configuration (15 min)

4. **Jupyter Notebooks**
   - Data analysis of routing decisions
   - Cost optimization strategies
   - Cache performance analysis

### Non-Functional Requirements
- Self-contained examples
- Progressive difficulty
- Clear learning objectives
- Runnable without modifications
- Well-commented code

## Acceptance Criteria
- [ ] 4+ interactive tutorials created
- [ ] 3+ example projects with documentation
- [ ] 3+ video tutorials recorded
- [ ] 2+ Jupyter notebooks for analysis
- [ ] All examples tested on fresh install
- [ ] Examples cover all major features
- [ ] Clear README for each example
- [ ] Examples work offline

## Technical Design

### Tutorial Structure
```
examples/
├── tutorials/
│   ├── 01-first-indexing/
│   │   ├── README.md
│   │   ├── sample-code/
│   │   ├── config.yaml
│   │   └── expected-output.md
│   ├── 02-smart-routing/
│   │   ├── README.md
│   │   ├── queries.md
│   │   └── analysis.ipynb
│   ├── 03-cost-optimization/
│   │   ├── README.md
│   │   ├── before-after.md
│   │   └── savings-report.md
│   └── 04-custom-tools/
│       ├── README.md
│       ├── my_tool.py
│       └── integration.md
├── projects/
│   ├── python-webapp/
│   ├── javascript-monorepo/
│   ├── mixed-language/
│   └── enterprise-setup/
├── notebooks/
│   ├── routing-analysis.ipynb
│   ├── cost-tracking.ipynb
│   └── cache-performance.ipynb
└── videos/
    └── links.md
```

### Example Projects

#### Python Web App
- Django/Flask application
- 50-100 files
- Shows basic indexing and search
- Demonstrates routing decisions

#### JavaScript Monorepo
- Multiple packages
- 500+ files
- Complex dependency tracking
- Performance optimization

#### Mixed Language Project
- Python + JavaScript + Go
- Language-specific chunking
- Cross-language search
- Metadata utilization

## Implementation Tasks
- [ ] Design tutorial progression
- [ ] Create sample repositories
- [ ] Write step-by-step tutorials
- [ ] Build example projects
- [ ] Record video tutorials
- [ ] Create Jupyter notebooks
- [ ] Test all examples
- [ ] Write tutorial READMEs
- [ ] Package examples properly
- [ ] Create online playground (stretch)

## Dependencies
- Sample code repositories
- Video recording/editing tools
- Jupyter notebook environment
- Testing infrastructure

## Example Tutorial: "Index Your First Repository"

```markdown
# Tutorial 1: Index Your First Repository

## Learning Objectives
- Set up Signal Hub for a project
- Configure indexing parameters
- Perform your first semantic search
- Understand routing decisions

## Prerequisites
- Signal Hub installed
- Python project to index

## Steps

### 1. Initialize Signal Hub (2 min)
```bash
signal-hub init my-project
cd my-project
```

### 2. Configure Indexing (3 min)
Edit `signal-hub.yaml`:
```yaml
indexing:
  include_patterns:
    - "**/*.py"
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/venv/**"
```

### 3. Run Indexing (5 min)
```bash
signal-hub index .
```
Expected output: X files indexed, Y chunks created

### 4. Test Semantic Search (5 min)
```bash
signal-hub search "function that handles user authentication"
```

## What You Learned
- Basic Signal Hub workflow
- Configuration options
- How semantic search works
```

## Success Metrics
- 90%+ tutorial completion rate
- Users complete first tutorial in < 20 min
- Positive feedback on examples
- Examples frequently referenced

## Notes
- Keep tutorials focused and short
- Provide expected outputs
- Include troubleshooting tips
- Make examples realistic
- Progressive complexity