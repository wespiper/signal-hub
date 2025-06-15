# SH-S03-018: Rule-Based Routing Engine

## Summary
Implement a simple but effective rule-based routing engine that intelligently selects between Haiku, Sonnet, and Opus models based on query characteristics. This is the core of Signal Hub Basic's cost optimization.

## Background
Signal Hub's primary value proposition is reducing AI costs while maintaining quality. This ticket implements the basic routing logic that will route simpler queries to cheaper models (Haiku) and complex queries to more capable models (Sonnet/Opus).

## Requirements

### Functional Requirements
1. **Routing Decision Logic**
   - Route based on query length (short → Haiku, medium → Sonnet, long → Opus)
   - Route based on complexity indicators (code analysis → Sonnet/Opus)
   - Route based on task type (simple search → Haiku, explanation → Sonnet)
   - Support routing hints from MCP tools

2. **Model Interfaces**
   - Abstract interface for model providers
   - Support for Haiku, Sonnet, and Opus models
   - Extensible for future models
   - Handle model-specific token limits

3. **Routing Rules**
   - Configurable thresholds for routing decisions
   - Default rules that work well out-of-the-box
   - Override capability for specific patterns
   - Plugin hook for ML-based routing (Pro edition)

4. **Performance Requirements**
   - Routing decision in <100ms
   - Minimal memory overhead
   - Efficient rule evaluation
   - Async/concurrent request handling

### Non-Functional Requirements
- Clean interfaces for Pro edition ML routing
- Comprehensive logging of routing decisions
- Metrics collection for routing effectiveness
- Thread-safe operation

## Acceptance Criteria
- [ ] Routing engine correctly selects models based on rules
- [ ] 50%+ of test queries routed to Haiku/Sonnet
- [ ] Routing decision time <100ms
- [ ] Configuration system for routing rules
- [ ] Plugin interface for advanced routing
- [ ] Unit tests with >90% coverage
- [ ] Integration tests with real model calls
- [ ] Performance benchmarks documented

## Technical Design

### Components
```python
# src/signal_hub/routing/
├── __init__.py
├── engine.py          # Main routing engine
├── models.py          # Data models
├── rules/            # Rule implementations
│   ├── __init__.py
│   ├── base.py       # Base rule interface
│   ├── length.py     # Query length rules
│   ├── complexity.py # Complexity analysis
│   └── task_type.py  # Task-based routing
├── providers/        # Model provider interfaces
│   ├── __init__.py
│   ├── base.py      # Provider interface
│   └── anthropic.py # Anthropic implementation
└── config.py        # Routing configuration
```

### Routing Algorithm
```python
class RoutingEngine:
    def route(self, query: Query) -> ModelSelection:
        # 1. Check for manual override
        if query.preferred_model:
            return ModelSelection(query.preferred_model)
        
        # 2. Apply routing rules in priority order
        for rule in self.rules:
            if result := rule.evaluate(query):
                return result
        
        # 3. Default to most capable model
        return ModelSelection(Model.OPUS)
```

### Default Rules
1. **Length-based**: <500 chars → Haiku, <2000 → Sonnet, else → Opus
2. **Complexity**: Code with >3 functions → Sonnet/Opus
3. **Task type**: search → Haiku, explain → Sonnet, analyze → Opus
4. **Context size**: Large context → Opus (better context handling)

## Implementation Tasks
- [ ] Create routing engine structure
- [ ] Implement base rule interface
- [ ] Build length-based routing rule
- [ ] Build complexity analysis rule
- [ ] Build task type detection
- [ ] Create model provider interface
- [ ] Implement Anthropic provider
- [ ] Add configuration system
- [ ] Create routing decision logger
- [ ] Add metrics collection
- [ ] Write comprehensive tests
- [ ] Performance optimization
- [ ] Documentation

## Dependencies
- Anthropic Python SDK
- Configuration system from Sprint 1
- Metrics system from Sprint 1

## Testing Strategy
1. **Unit Tests**: Each rule and component
2. **Integration Tests**: Full routing decisions
3. **Performance Tests**: Routing latency
4. **Load Tests**: Concurrent routing decisions

## Risks & Mitigations
- **Risk**: Poor routing decisions increasing costs
  - **Mitigation**: Conservative defaults, extensive testing
- **Risk**: Complexity analysis too slow
  - **Mitigation**: Simple heuristics, caching results

## Success Metrics
- 50%+ queries routed to cheaper models
- <100ms routing decision time
- 30%+ cost reduction in testing
- <5% user complaints about model selection

## Notes
- Keep rules simple and explainable
- Ensure easy configuration for users
- Design with Pro edition ML routing in mind
- Focus on effectiveness over complexity