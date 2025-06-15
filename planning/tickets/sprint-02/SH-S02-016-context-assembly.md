# Sprint Ticket: Context Assembly

## Ticket Information
- **Ticket ID**: SH-S02-016
- **Title**: Build Coherent Context Assembly System
- **Parent User Story**: Sprint 2 - RAG Implementation
- **Priority**: P0 (Blocker)
- **Story Points**: 5
- **Assigned To**: [Senior Backend Engineer]
- **Status**: To Do
- **Sprint**: Sprint 2 - RAG Implementation
- **Epic**: RAG

## Business Context
### Why This Matters
Context assembly transforms individual search results into coherent, usable context for Claude. Poor context assembly leads to confusion, errors, and degraded AI responses. This is critical for delivering value from our RAG system.

### Success Metrics
- **Performance Target**: Assemble context in <500ms
- **User Impact**: Claude receives well-structured, relevant context
- **Business Value**: Enables accurate AI responses, core product functionality

## Description
Build a system that assembles retrieved code chunks into coherent context for Claude. This includes deduplication, ordering, relationship detection, and formatting to maximize Claude's understanding while respecting token limits.

## Acceptance Criteria
- [ ] **Functional**: Assembled context maintains code coherence
- [ ] **Performance**: Context assembly <500ms for typical queries
- [ ] **Quality**: No duplicate information, logical ordering
- [ ] **Integration**: Respects Claude's token limits and formatting preferences

## Technical Implementation

### Architecture/Design
- Intelligent deduplication of overlapping chunks
- Dependency-aware ordering
- Relationship graph construction
- Token budget management
- Context compression strategies
- Format optimization for Claude

### Implementation Plan
```yaml
Phase 1: Deduplication (Day 1)
  - Task: Remove redundant information
  - Output: Clean, unique chunks
  - Risk: Losing important context

Phase 2: Ordering Logic (Day 2)
  - Task: Dependency-aware ordering
  - Output: Logical code flow
  - Risk: Complex dependencies

Phase 3: Relationship Graph (Day 3)
  - Task: Build chunk relationships
  - Output: Connected context
  - Risk: Performance overhead

Phase 4: Token Management (Day 4)
  - Task: Smart token budgeting
  - Output: Optimal context size
  - Risk: Information loss

Phase 5: Formatting (Day 5)
  - Task: Claude-optimized output
  - Output: Well-structured context
  - Risk: Format complexity
```

### Code Structure
```
src/signal_hub/retrieval/assembly/
├── __init__.py
├── assembler.py         # Main context assembler
├── deduplication.py     # Chunk deduplication
├── ordering.py          # Intelligent ordering
├── relationships.py     # Relationship detection
├── compression.py       # Context compression
├── formatting.py        # Output formatting
└── token_manager.py     # Token budget management
```

## Dependencies & Risks
### Dependencies
- **Blocking**: SH-S02-014 (Semantic search), SH-S02-015 (Chunking)
- **Dependent**: MCP tool responses
- **External**: Claude's context window limits

### Risks & Mitigations
- **Risk**: Context exceeds token limits
  - **Impact**: High
  - **Mitigation**: Smart compression, prioritization
- **Risk**: Loss of critical context
  - **Impact**: High
  - **Mitigation**: Importance scoring, validation

## Testing & Validation

### Testing Strategy
- **Unit Tests**: 
  - [ ] Deduplication accuracy
  - [ ] Ordering logic correctness
  - [ ] Relationship detection
  - [ ] Token counting accuracy
- **Integration Tests**:
  - [ ] End-to-end assembly
  - [ ] Claude compatibility
  - [ ] Performance under load
  - [ ] Edge cases (large results)

### Demo Scenarios
```python
from signal_hub.retrieval.assembly import ContextAssembler

# Initialize assembler
assembler = ContextAssembler(
    max_tokens=8000,
    dedup_threshold=0.85,
    preserve_relationships=True
)

# Search results from semantic search
search_results = await search_engine.search("user authentication flow")

# Assemble coherent context
context = await assembler.assemble(
    chunks=search_results,
    query="explain the user authentication flow",
    format="claude_optimized"
)

print(f"Total chunks: {len(search_results)}")
print(f"Assembled sections: {len(context.sections)}")
print(f"Token count: {context.token_count}")
print(f"Relationships found: {len(context.relationships)}")

# Examine assembled context
for section in context.sections:
    print(f"\n=== {section.title} ===")
    print(f"Source: {section.source_file}")
    print(f"Type: {section.content_type}")
    print(section.content[:500] + "...")

# Relationship graph
print("\nCode Relationships:")
for rel in context.relationships:
    print(f"- {rel.from_entity} {rel.relationship_type} {rel.to_entity}")
```

## Definition of Done
- [ ] Deduplication system implemented
- [ ] Intelligent ordering algorithm complete
- [ ] Relationship detection working
- [ ] Token management system operational
- [ ] Context compression strategies implemented
- [ ] Claude-optimized formatting complete
- [ ] Performance targets met
- [ ] Quality validation tests passing
- [ ] Integration with search pipeline
- [ ] 85% test coverage

## Notes & Resources
- **Design Docs**: [Context Assembly Architecture](../../architecture/context-assembly.md)
- **Partner Context**: Direct impact on Claude's response quality
- **Future Considerations**: ML-based importance scoring, user preference learning
- **Learning Resources**: 
  - [RAG Best Practices](https://docs.anthropic.com/claude/docs/retrieval-augmented-generation)
  - [Context Window Management](https://www.anthropic.com/research/context-windows)
- **Edition Notes**: Basic assembly in all editions, advanced strategies (compression, importance scoring) in Pro