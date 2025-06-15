# Sprint Ticket: Embedding Generation Pipeline

## Ticket Information
- **Ticket ID**: SH-S01-006
- **Title**: Implement Embedding Generation Pipeline
- **Parent User Story**: Sprint 1 - Core Infrastructure
- **Priority**: P0 (Blocker)
- **Story Points**: 5
- **Assigned To**: [ML Engineer]
- **Status**: ✅ Completed
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
- [x] **Functional**: Generate embeddings from text chunks
- [x] **Performance**: Batch processing with rate limit handling
- [x] **Quality**: Consistent embedding quality
- [x] **Integration**: Seamless provider switching

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
- [x] OpenAI provider implemented
- [x] Local provider implemented
- [x] Provider switching works
- [x] Batch processing efficient
- [x] Rate limiting handled gracefully
- [x] Cost tracking accurate
- [x] Performance targets met
- [x] Fallback mechanism tested
- [x] 90% test coverage

## Notes & Resources
- **Design Docs**: [Embedding Strategy](../../architecture/embedding-strategy.md)
- **Partner Context**: Critical for search quality
- **Future Considerations**: May add more providers
- **Learning Resources**: 
  - [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
  - [Sentence Transformers](https://www.sbert.net/)
- **Implementation Date**: Completed on 2025-06-15

## Completion Summary
Successfully implemented a robust embedding generation pipeline with:
1. Provider abstraction supporting multiple embedding sources
2. OpenAI provider with all models and cost tracking
3. Local provider using sentence-transformers
4. Smart batching for optimal API usage
5. Cost tracking with persistence
6. Fallback mechanism for reliability
7. Comprehensive test coverage