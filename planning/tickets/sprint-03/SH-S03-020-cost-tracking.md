# SH-S03-020: Cost Tracking System

## Summary
Implement a comprehensive cost tracking system that monitors AI model usage, calculates costs, and provides insights into savings achieved through routing and caching.

## Background
Cost transparency is essential for Signal Hub's value proposition. Users need to see how much they're saving through intelligent routing and caching. This system tracks all model calls, calculates costs, and generates reports.

## Requirements

### Functional Requirements
1. **Usage Tracking**
   - Track every model API call (model, tokens, latency)
   - Record routing decisions and reasons
   - Track cache hits and misses
   - Store usage data persistently

2. **Cost Calculation**
   - Accurate token counting for requests/responses
   - Model-specific pricing (Haiku/Sonnet/Opus)
   - Real-time cost accumulation
   - Comparison with "always Opus" baseline

3. **Reporting**
   - Daily/weekly/monthly cost summaries
   - Savings achieved through routing
   - Savings achieved through caching
   - Model usage distribution

4. **Analytics Dashboard**
   - Real-time cost display
   - Historical trends
   - Savings visualization
   - Export capabilities

### Non-Functional Requirements
- Minimal performance impact (<1% overhead)
- Accurate token counting
- Reliable data persistence
- Privacy-preserving (no query content stored)

## Acceptance Criteria
- [ ] All model calls tracked accurately
- [ ] Cost calculations match Anthropic billing
- [ ] Dashboard showing real-time costs
- [ ] Savings calculations documented
- [ ] Export functionality working
- [ ] <1% performance overhead
- [ ] Unit tests with >90% coverage
- [ ] Integration tests with real API calls

## Technical Design

### Components
```python
# src/signal_hub/costs/
├── __init__.py
├── tracker.py         # Main cost tracking
├── models.py         # Cost data models
├── calculator.py     # Cost calculations
├── storage/          # Cost data storage
│   ├── __init__.py
│   ├── base.py      # Storage interface
│   └── sqlite.py    # SQLite backend
├── reports/          # Report generation
│   ├── __init__.py
│   ├── daily.py     # Daily summaries
│   ├── savings.py   # Savings analysis
│   └── export.py    # Data export
└── dashboard/        # Analytics dashboard
    ├── __init__.py
    ├── api.py       # Dashboard API
    └── static/      # Dashboard UI
```

### Data Model
```python
@dataclass
class ModelUsage:
    timestamp: datetime
    model: ModelType
    input_tokens: int
    output_tokens: int
    cost: float
    routing_reason: str
    cache_hit: bool
    latency_ms: int
    
@dataclass
class CostSummary:
    period: str
    total_cost: float
    total_saved: float
    routing_savings: float
    cache_savings: float
    model_distribution: Dict[ModelType, int]
```

### Tracking Flow
1. Intercept all model API calls
2. Count tokens accurately
3. Calculate cost based on model pricing
4. Record routing decision and reason
5. Store in persistent database
6. Update real-time dashboard

## Implementation Tasks
- [ ] Create cost tracking structure
- [ ] Implement usage tracker
- [ ] Build token counting system
- [ ] Create cost calculator
- [ ] Implement SQLite storage
- [ ] Build reporting system
- [ ] Create savings analyzer
- [ ] Develop dashboard API
- [ ] Build dashboard UI
- [ ] Add export functionality
- [ ] Write comprehensive tests
- [ ] Performance optimization
- [ ] Documentation

## Dependencies
- Anthropic pricing information
- SQLite for data storage
- Token counting library (tiktoken)

## Pricing Reference
Current Anthropic pricing (per million tokens):
- Haiku: $0.25 input, $1.25 output
- Sonnet: $3 input, $15 output  
- Opus: $15 input, $75 output

## Testing Strategy
1. **Unit Tests**: Calculator accuracy
2. **Integration Tests**: Full tracking flow
3. **Performance Tests**: Overhead measurement
4. **Accuracy Tests**: Token counting validation

## Configuration
```yaml
costs:
  tracking:
    enabled: true
    storage_path: "~/.signal-hub/costs.db"
    retention_days: 90
    dashboard_port: 3335
    export_formats: ["csv", "json"]
```

## Risks & Mitigations
- **Risk**: Inaccurate token counting
  - **Mitigation**: Use official tokenizer, extensive testing
- **Risk**: Performance overhead
  - **Mitigation**: Async tracking, batch writes
- **Risk**: Storage growing too large
  - **Mitigation**: Configurable retention, data aggregation

## Success Metrics
- 100% of API calls tracked
- <1% tracking overhead
- Cost accuracy within 1% of billing
- Dashboard load time <1 second

## Notes
- Privacy first: no query content stored
- Design for Pro edition advanced analytics
- Consider cost alerts and budgets
- Make savings visualization compelling