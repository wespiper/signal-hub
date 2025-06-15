# SH-S04-027: API Reference Documentation

## Summary
Create comprehensive API reference documentation for all MCP tools, configuration schemas, and plugin interfaces, enabling developers to integrate and extend Signal Hub effectively.

## Background
Developers need detailed API documentation to use Signal Hub's tools effectively and build custom integrations. This includes MCP tool specifications, configuration schemas, and plugin development guides.

## Requirements

### Functional Requirements
1. **MCP Tools Reference**
   - Tool descriptions and parameters
   - Request/response examples
   - Error handling
   - Usage patterns

2. **Configuration Reference**
   - Complete YAML schema
   - Environment variables
   - Default values
   - Advanced options

3. **Plugin API Documentation**
   - Plugin interface specifications
   - Hook points and callbacks
   - Example plugin code
   - Testing guidelines

4. **Python API Reference**
   - Public classes and methods
   - Type annotations
   - Code examples
   - Migration guides

### Non-Functional Requirements
- Auto-generated from code where possible
- Versioned documentation
- Interactive API explorer
- Code examples in multiple languages
- Search functionality

## Acceptance Criteria
- [ ] All MCP tools fully documented
- [ ] Configuration schema documented
- [ ] Plugin API reference complete
- [ ] Python API docs generated
- [ ] Examples for every endpoint
- [ ] Error codes documented
- [ ] API versioning explained
- [ ] Interactive examples working

## Technical Design

### Documentation Generation
```python
# Use Sphinx for Python API docs
# Use OpenAPI/Swagger for REST APIs (future)
# Use JSON Schema for configuration

docs/api/
├── mcp-tools/
│   ├── search_code.md
│   ├── explain_code.md
│   ├── find_similar.md
│   ├── get_context.md
│   └── escalate_query.md
├── configuration/
│   ├── schema.json
│   ├── routing.md
│   ├── security.md
│   └── indexing.md
├── plugins/
│   ├── interfaces.md
│   ├── hooks.md
│   ├── examples.md
│   └── testing.md
└── python/
    ├── signal_hub.core.rst
    ├── signal_hub.routing.rst
    └── signal_hub.indexing.rst
```

### MCP Tool Documentation Template
```markdown
# search_code

Search for code semantically across your indexed codebase.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | Natural language search query |
| limit | integer | No | Maximum results (default: 10) |
| threshold | float | No | Similarity threshold (default: 0.7) |

## Request Example
```json
{
  "tool": "search_code",
  "arguments": {
    "query": "function to validate email addresses",
    "limit": 5
  }
}
```

## Response Example
```json
{
  "results": [
    {
      "file": "src/validators.py",
      "line": 42,
      "score": 0.89,
      "content": "def validate_email(email: str) -> bool:...",
      "context": "..."
    }
  ]
}
```

## Error Handling
- `NO_INDEX`: No index found for project
- `INVALID_QUERY`: Query too short or invalid
```

### Configuration Schema Documentation
```yaml
# Signal Hub Configuration Schema

# Indexing Configuration
indexing:
  # File patterns to include (glob)
  include_patterns: 
    type: array
    items: string
    default: ["**/*.py", "**/*.js", "**/*.ts"]
  
  # Patterns to exclude
  exclude_patterns:
    type: array
    items: string
    default: ["**/node_modules/**", "**/.git/**"]
  
  # Chunking strategy
  chunk_size:
    type: integer
    minimum: 100
    maximum: 2000
    default: 500

# Routing Configuration  
routing:
  # Default model selection
  default_model:
    type: string
    enum: ["haiku", "sonnet", "opus"]
    default: "haiku"
```

## Implementation Tasks
- [ ] Document all MCP tools
- [ ] Create configuration schema
- [ ] Generate Python API docs
- [ ] Write plugin development guide
- [ ] Create API testing examples
- [ ] Build interactive API explorer
- [ ] Set up auto-generation pipeline
- [ ] Add versioning system
- [ ] Create migration guides
- [ ] Test all examples

## Dependencies
- Sphinx for Python docs
- JSON Schema validator
- API documentation theme
- Example test framework

## Testing Strategy
1. **Example Validation**: All examples must run
2. **Schema Testing**: Configuration validates
3. **Link Checking**: No broken references
4. **Completeness**: No undocumented APIs

## Success Metrics
- 100% API coverage
- All examples executable
- < 5% questions about documented APIs
- Positive developer feedback

## Notes
- Keep examples practical
- Show both success and error cases
- Include performance considerations
- Document rate limits and quotas
- Provide troubleshooting tips