# Sprint Ticket: Embedding Generation Pipeline

## Ticket Information
- **Ticket ID**: SH-S01-006
- **Title**: Implement Embedding Generation Pipeline
- **Parent User Story**: Sprint 1 - Core Infrastructure
- **Priority**: P0 (Blocker)
- **Story Points**: 5
- **Assigned To**: [ML Engineer]
- **Status**: To Do
- **Sprint**: Sprint 1 - Core Infrastructure
- **Epic**: Infrastructure

## Business Context
### Why This Matters
Embeddings are the foundation of semantic search. The quality and efficiency of embedding generation directly impacts search accuracy and cost. This pipeline must handle both online (OpenAI) and offline (local) generation.

### Success Metrics
- **Performance Target**: Generate 1000 embeddings/minute
- **User Impact**: Accurate semantic search results
- **Business Value**: Enables core RAG functionality

## Description
Build a robust embedding generation pipeline that can process code chunks into vector embeddings. Support both OpenAI's API for quality and local models for offline/cost-sensitive use. Include batching, rate limiting, and cost tracking.

## Acceptance Criteria
- [ ] **Functional**: Generate embeddings from text chunks
- [ ] **Performance**: Batch processing with rate limit handling
- [ ] **Quality**: Consistent embedding quality
- [ ] **Integration**: Seamless provider switching

## Technical Implementation

### Architecture/Design
- Provider abstraction for multiple embedding sources
- Intelligent batching for API efficiency
- Rate limit handling with backoff
- Cost tracking per embedding

### Implementation Plan
```yaml
Phase 1: Provider Interface (Day 1)
  - Task: Create embedding provider abstraction
  - Output: Pluggable providers
  - Risk: API differences

Phase 2: OpenAI Integration (Day 2)
  - Task: Implement OpenAI embeddings
  - Output: High-quality embeddings
  - Risk: API costs

Phase 3: Local Provider (Day 3)
  - Task: Sentence-transformers integration
  - Output: Offline capability
  - Risk: Quality vs speed

Phase 4: Pipeline & Batching (Day 4)
  - Task: Batch processing system
  - Output: Efficient generation
  - Risk: Memory usage

Phase 5: Cost & Monitoring (Day 5)
  - Task: Add cost tracking
  - Output: Usage visibility
  - Risk: Complexity
```

### Code Structure
```
src/signal_hub/indexing/embeddings/
├── __init__.py
├── service.py          # Main embedding service
├── providers/
│   ├── base.py        # Provider interface
│   ├── openai.py      # OpenAI implementation
│   └── local.py       # Sentence-transformers
├── batch.py           # Batch processing
└── cost.py            # Cost tracking

tests/unit/indexing/embeddings/
├── test_service.py
├── test_providers.py
└── test_batch.py
```

## Dependencies & Risks
### Dependencies
- **Blocking**: SH-S01-005 (Need chunks to embed)
- **Dependent**: SH-S01-007 (ChromaDB stores embeddings)
- **External**: OpenAI API, HuggingFace models

### Risks & Mitigations
- **Risk**: OpenAI API downtime
  - **Impact**: High
  - **Mitigation**: Fallback to local provider
- **Risk**: Rate limiting
  - **Impact**: Medium
  - **Mitigation**: Exponential backoff, queuing
- **Risk**: Embedding costs
  - **Impact**: Medium
  - **Mitigation**: Cost alerts, limits

## Testing & Validation

### Testing Strategy
- **Unit Tests**: 
  - [ ] Provider switching
  - [ ] Batch processing logic
  - [ ] Rate limit handling
  - [ ] Cost calculation
  - [ ] Error recovery
- **Integration Tests**:
  - [ ] Real API calls (test account)
  - [ ] Local model loading
  - [ ] End-to-end pipeline
  - [ ] Performance under load

### Demo Scenarios
```python
from signal_hub.indexing.embeddings import EmbeddingService

# Initialize service
service = EmbeddingService(provider="openai")

# Single embedding
text = "def calculate_total(items):"
embedding = await service.generate(text)
print(f"Embedding shape: {len(embedding)}")

# Batch processing
texts = ["chunk1", "chunk2", "chunk3"]
embeddings = await service.batch_generate(texts)
print(f"Generated {len(embeddings)} embeddings")
print(f"Total cost: ${service.get_cost()}")
```

## Definition of Done
- [ ] OpenAI provider implemented
- [ ] Local provider implemented
- [ ] Provider switching works
- [ ] Batch processing efficient
- [ ] Rate limiting handled gracefully
- [ ] Cost tracking accurate
- [ ] Performance targets met
- [ ] Fallback mechanism tested
- [ ] 90% test coverage

## Notes & Resources
- **Design Docs**: [Embedding Strategy](../../architecture/embedding-strategy.md)
- **Partner Context**: Critical for search quality
- **Future Considerations**: May add more providers
- **Learning Resources**: 
  - [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
  - [Sentence Transformers](https://www.sbert.net/)