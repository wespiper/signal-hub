# SH-S03-023: Routing Configuration System

## Summary
Implement a flexible configuration system for the routing engine that allows users to customize routing rules while maintaining sensible defaults that work out of the box.

## Background
While Signal Hub Basic should work with zero configuration, power users need the ability to customize routing rules for their specific use cases. This system provides that flexibility while keeping the default experience simple.

## Requirements

### Functional Requirements
1. **Configuration Schema**
   - Define routing thresholds and rules
   - Model selection preferences
   - Task type mappings
   - Override patterns

2. **Configuration Sources**
   - Default configuration (built-in)
   - User configuration file
   - Environment variables
   - Runtime updates via API

3. **Rule Configuration**
   - Query length thresholds
   - Complexity indicators
   - Task type patterns
   - Model preferences

4. **Validation & Safety**
   - Schema validation
   - Safe defaults fallback
   - Configuration testing
   - Change impact preview

### Non-Functional Requirements
- Zero-config must work perfectly
- Hot reload without restart
- Clear configuration documentation
- Migration path for updates

## Acceptance Criteria
- [ ] Default configuration works optimally
- [ ] User can override any routing rule
- [ ] Configuration validation working
- [ ] Hot reload implemented
- [ ] Environment variable support
- [ ] Clear documentation
- [ ] Configuration testing tools
- [ ] Unit tests with >90% coverage
- [ ] Integration tests with routing

## Technical Design

### Components
```python
# src/signal_hub/routing/config/
├── __init__.py
├── schema.py          # Configuration schema
├── loader.py          # Configuration loader
├── validator.py       # Schema validation
├── defaults.py        # Default configuration
├── merger.py          # Config merging logic
└── watcher.py         # Hot reload support

# config/
├── routing.default.yaml  # Default routing rules
└── routing.yaml         # User overrides
```

### Configuration Schema
```yaml
routing:
  # Model selection thresholds
  models:
    haiku:
      max_tokens: 1000
      max_complexity: "simple"
      preferred_tasks: ["search", "simple_query"]
    sonnet:
      max_tokens: 4000
      max_complexity: "moderate"
      preferred_tasks: ["explain", "analyze"]
    opus:
      max_tokens: null  # no limit
      max_complexity: "complex"
      preferred_tasks: ["debug", "architect", "refactor"]
  
  # Routing rules
  rules:
    - name: "length_based"
      enabled: true
      priority: 1
      thresholds:
        haiku: 500
        sonnet: 2000
    
    - name: "complexity_based"
      enabled: true
      priority: 2
      indicators:
        simple: ["what", "when", "where", "list"]
        complex: ["analyze", "design", "optimize", "refactor"]
    
    - name: "task_type"
      enabled: true
      priority: 3
      mappings:
        search_code: "haiku"
        explain_code: "sonnet"
        analyze_architecture: "opus"
  
  # Overrides
  overrides:
    - pattern: "security|vulnerability"
      model: "opus"
      reason: "Security requires careful analysis"
```

### Configuration Loading
```python
class RoutingConfigLoader:
    def load(self) -> RoutingConfig:
        # 1. Load defaults
        config = self.load_defaults()
        
        # 2. Merge user configuration
        if user_config := self.load_user_config():
            config = self.merge(config, user_config)
            
        # 3. Apply environment overrides
        config = self.apply_env_overrides(config)
        
        # 4. Validate final configuration
        self.validator.validate(config)
        
        return config
```

## Implementation Tasks
- [ ] Define configuration schema
- [ ] Create default configuration
- [ ] Implement configuration loader
- [ ] Build schema validator
- [ ] Create config merger
- [ ] Implement hot reload
- [ ] Add environment variables
- [ ] Create configuration API
- [ ] Build config testing tools
- [ ] Write migration guide
- [ ] Create examples
- [ ] Write comprehensive tests
- [ ] Documentation

## Dependencies
- Routing engine (SH-S03-018)
- YAML parser (PyYAML)
- Schema validation (jsonschema)

## Environment Variables
```bash
# Override specific models
SIGNAL_HUB_ROUTING_DEFAULT_MODEL=sonnet
SIGNAL_HUB_ROUTING_HAIKU_MAX_TOKENS=500

# Toggle features
SIGNAL_HUB_ROUTING_COMPLEXITY_ENABLED=false

# Override thresholds
SIGNAL_HUB_ROUTING_CACHE_THRESHOLD=0.9
```

## Testing Strategy
1. **Unit Tests**: Configuration loading and merging
2. **Integration Tests**: With routing engine
3. **Validation Tests**: Invalid configurations
4. **Migration Tests**: Config version updates

## Example Configurations

### Conservative (Prefer Quality)
```yaml
routing:
  rules:
    - name: "length_based"
      thresholds:
        haiku: 300      # Only very short
        sonnet: 5000    # Prefer Sonnet
```

### Aggressive (Maximize Savings)
```yaml
routing:
  rules:
    - name: "length_based"
      thresholds:
        haiku: 1000     # More to Haiku
        sonnet: 3000    # Less to Opus
```

## Risks & Mitigations
- **Risk**: Bad configuration breaking routing
  - **Mitigation**: Validation, safe defaults
- **Risk**: Complex configuration confusing users
  - **Mitigation**: Great defaults, clear examples

## Success Metrics
- 80%+ users use default configuration
- <5 minutes to customize for power users
- Zero configuration errors in production
- Positive feedback on flexibility

## Notes
- Defaults should be excellent
- Keep configuration simple
- Provide many examples
- Design for Pro edition extensions