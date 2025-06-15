# SH-S04-030: Configuration Templates & Wizard

## Summary
Create configuration templates for common use cases and an interactive configuration wizard that guides users through setup, making Signal Hub accessible to developers of all experience levels.

## Background
While Signal Hub works with zero configuration, optimal performance requires project-specific settings. A configuration wizard and templates will help users get the best results without deep knowledge of all options.

## Requirements

### Functional Requirements
1. **Configuration Templates**
   - Small Python project
   - JavaScript/TypeScript app
   - Monorepo setup
   - Multi-language project
   - Enterprise deployment

2. **Interactive Wizard**
   - Project type detection
   - Guided configuration
   - Performance recommendations
   - Security setup
   - Validation and testing

3. **Template Library**
   - Pre-configured settings
   - Best practices included
   - Performance-optimized
   - Security-hardened

4. **Configuration Management**
   - Import/export configs
   - Merge configurations
   - Environment-specific settings
   - Version migration

### Non-Functional Requirements
- Works in terminal (CLI)
- Web-based option (stretch)
- Clear explanations
- Undo/redo support
- Non-destructive

## Acceptance Criteria
- [ ] 5+ configuration templates created
- [ ] Interactive wizard implemented
- [ ] Auto-detection of project type
- [ ] Configuration validation working
- [ ] Templates cover 80%+ use cases
- [ ] Wizard completes in < 3 minutes
- [ ] Generated configs are optimal
- [ ] Help text for all options

## Technical Design

### Configuration Templates
```yaml
# templates/python-webapp.yaml
name: "Python Web Application"
description: "Optimized for Django/Flask applications"

indexing:
  include_patterns:
    - "**/*.py"
    - "**/templates/**/*.html"
    - "**/static/**/*.js"
    - "**/static/**/*.css"
  exclude_patterns:
    - "**/migrations/**"
    - "**/__pycache__/**"
    - "**/venv/**"
    - "**/.env"
  
routing:
  rules:
    - name: "web_specific"
      patterns:
        - "view|controller|route": "sonnet"
        - "model|database|orm": "sonnet"
        - "template|render": "haiku"
        - "static|css|style": "haiku"

caching:
  ttl_hours: 24
  max_size_mb: 500
  
security:
  api_keys:
    storage: "encrypted_file"
  rate_limiting:
    enabled: true
    default_limit: 1000
```

### Configuration Wizard Flow
```python
class ConfigWizard:
    def run(self):
        # 1. Detect project type
        project_type = self.detect_project_type()
        
        # 2. Load base template
        config = self.load_template(project_type)
        
        # 3. Customize settings
        config = self.customize_indexing(config)
        config = self.customize_routing(config)
        config = self.customize_security(config)
        
        # 4. Validate configuration
        issues = self.validate_config(config)
        if issues:
            config = self.fix_issues(config, issues)
        
        # 5. Save configuration
        self.save_config(config)
        
        # 6. Test configuration
        self.test_config(config)
```

### CLI Interface
```bash
$ signal-hub config wizard

🚀 Signal Hub Configuration Wizard

Detecting project type... Python Web Application

📁 Indexing Configuration
Include patterns [**/*.py, **/*.html]: 
Exclude patterns [**/venv/**, **/__pycache__/**]: 
Maximum file size [10MB]: 

🔀 Routing Configuration
Prefer cost optimization? [Y/n]: Y
Enable manual escalation? [Y/n]: Y
Cache similarity threshold [0.85]: 

🔒 Security Configuration
Enable authentication? [Y/n]: Y
Username [admin]: 
Rate limiting [1000 requests/hour]: 

✅ Configuration Summary
- Will index 156 files
- Routing optimized for cost
- Security enabled with rate limiting

Save configuration? [Y/n]: Y
✨ Configuration saved to signal-hub.yaml

Test configuration? [Y/n]: Y
🎯 Running validation tests...
✅ All tests passed!

Ready to start! Run: signal-hub index
```

## Implementation Tasks
- [ ] Create configuration templates
- [ ] Build project type detector
- [ ] Implement CLI wizard
- [ ] Add configuration validator
- [ ] Create template library
- [ ] Build merge functionality
- [ ] Add import/export features
- [ ] Implement testing framework
- [ ] Write template documentation
- [ ] Add web interface (stretch)

## Dependencies
- Click/Typer for CLI
- PyYAML for configuration
- Rich for terminal UI
- Questionary for prompts

## Template Categories
1. **By Language**: Python, JavaScript, Go, Rust, Java
2. **By Framework**: Django, React, Vue, Spring
3. **By Size**: Small (<100 files), Medium, Large
4. **By Purpose**: Web app, API, Data science, CLI tool
5. **By Deployment**: Local, Cloud, Enterprise

## Testing Strategy
1. **Template Testing**: Validate all templates
2. **Wizard Testing**: Test all paths
3. **Integration Testing**: Generated configs work
4. **User Testing**: Real developers use wizard

## Success Metrics
- 80%+ users use templates/wizard
- Configuration time < 3 minutes
- 90%+ satisfaction with wizard
- Reduced configuration errors

## Notes
- Keep wizard simple and fast
- Provide sensible defaults
- Explain impact of choices
- Allow skipping sections
- Support re-running wizard