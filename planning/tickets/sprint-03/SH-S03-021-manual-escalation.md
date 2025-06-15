# SH-S03-021: Manual Escalation Mechanism

## Summary
Implement a manual escalation mechanism that allows users to override the automatic model routing and explicitly request a more capable model when needed.

## Background
While automatic routing saves costs, users sometimes know they need a more powerful model for complex tasks. The manual escalation mechanism gives users control while maintaining the benefits of automatic routing for most queries.

## Requirements

### Functional Requirements
1. **Escalation Interface**
   - MCP tool: `escalate_query` for explicit escalation
   - Inline hints: Support `@opus` or `@sonnet` in queries
   - Temporary escalation: Single query escalation
   - Session escalation: All queries in session

2. **Escalation Logic**
   - Override routing decision when escalated
   - Track escalation usage and patterns
   - Respect model availability
   - Clear feedback on escalation status

3. **User Experience**
   - Simple, intuitive escalation syntax
   - Clear documentation on when to escalate
   - Feedback on model selection
   - Cost implications displayed

4. **Integration**
   - Seamless integration with routing engine
   - Cost tracking for escalated queries
   - Metrics on escalation patterns

### Non-Functional Requirements
- Zero latency impact on routing
- Clear audit trail of escalations
- Configurable escalation options
- Future-proof for Pro features

## Acceptance Criteria
- [ ] `escalate_query` MCP tool working
- [ ] Inline hints (`@model`) recognized
- [ ] Session escalation implemented
- [ ] Escalation tracked in metrics
- [ ] Cost impact displayed to user
- [ ] <10% escalation rate in testing
- [ ] Unit tests with >90% coverage
- [ ] Integration tests with routing

## Technical Design

### Components
```python
# src/signal_hub/routing/escalation/
├── __init__.py
├── escalator.py      # Main escalation logic
├── models.py         # Escalation data models
├── parser.py         # Query hint parser
├── session.py        # Session escalation manager
└── metrics.py        # Escalation metrics

# src/signal_hub/core/tools/
└── escalate_query.py # MCP tool implementation
```

### Escalation Flow
```python
class EscalationManager:
    def check_escalation(self, query: Query, session: Session) -> Optional[ModelOverride]:
        # 1. Check session-level escalation
        if session.escalated_model:
            return ModelOverride(session.escalated_model, "session")
            
        # 2. Check inline hints
        if hint := self.parser.extract_hint(query.text):
            return ModelOverride(hint.model, "inline")
            
        # 3. Check explicit tool call
        if query.tool == "escalate_query":
            return ModelOverride(query.params.model, "explicit")
            
        return None
```

### MCP Tool Definition
```python
class EscalateQueryTool(Tool):
    name = "escalate_query"
    description = "Manually request a more capable model"
    
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "model": {
                "type": "string",
                "enum": ["sonnet", "opus"],
                "default": "opus"
            },
            "reason": {"type": "string"}
        },
        "required": ["query"]
    }
```

## Implementation Tasks
- [ ] Create escalation manager
- [ ] Implement hint parser for @model syntax
- [ ] Build session escalation system
- [ ] Create escalate_query MCP tool
- [ ] Integrate with routing engine
- [ ] Add escalation metrics
- [ ] Create cost impact calculator
- [ ] Build user feedback system
- [ ] Write comprehensive tests
- [ ] Documentation and examples

## Dependencies
- Routing engine (SH-S03-018)
- Cost tracking (SH-S03-020)
- MCP tool system (Sprint 1)

## Testing Strategy
1. **Unit Tests**: Parser and escalation logic
2. **Integration Tests**: With routing engine
3. **User Tests**: Escalation patterns
4. **Performance Tests**: Zero overhead verification

## User Documentation
```markdown
## Manual Escalation

When you need a more powerful model:

1. **Inline hints**: Add @opus or @sonnet to your query
   ```
   @opus Analyze this complex architecture and suggest improvements
   ```

2. **Escalate tool**: Use the escalate_query tool
   ```
   Tool: escalate_query
   Query: "Explain this quantum algorithm"
   Model: "opus"
   ```

3. **Session escalation**: Escalate all queries in session
   ```
   Set session model: opus
   ```
```

## Risks & Mitigations
- **Risk**: Overuse of escalation negating savings
  - **Mitigation**: Track patterns, educate users
- **Risk**: Complex syntax confusing users
  - **Mitigation**: Simple @model syntax, clear docs

## Success Metrics
- <10% of queries escalated
- 90%+ user satisfaction with control
- Zero complaints about model selection
- Clear cost impact understanding

## Notes
- Keep escalation simple and intuitive
- Track patterns for ML training (Pro)
- Consider escalation suggestions
- Balance control with cost savings