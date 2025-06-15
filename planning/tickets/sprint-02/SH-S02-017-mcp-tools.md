# Sprint Ticket: MCP Tool Implementation

## Ticket Information
- **Ticket ID**: SH-S02-017
- **Title**: Implement Core MCP Tools for RAG
- **Parent User Story**: Sprint 2 - RAG Implementation
- **Priority**: P0 (Blocker)
- **Story Points**: 5
- **Assigned To**: [Senior Backend Engineer]
- **Status**: To Do
- **Sprint**: Sprint 2 - RAG Implementation
- **Epic**: MCP

## Business Context
### Why This Matters
MCP tools are how Claude Code interacts with Signal Hub. These tools enable developers to search codebases, get explanations, and leverage RAG capabilities directly within their Claude Code workflow.

### Success Metrics
- **Performance Target**: Tool response time <3 seconds
- **User Impact**: Seamless code search and understanding in Claude Code
- **Business Value**: Complete RAG integration, usable product

## Description
Implement the core MCP tools that expose Signal Hub's RAG capabilities to Claude Code. This includes search_code, explain_code, find_similar, and get_context tools with proper parameter validation and response formatting.

## Acceptance Criteria
- [ ] **Functional**: All core tools working in Claude Code
- [ ] **Performance**: Response time <3 seconds for typical queries
- [ ] **Quality**: Clear, helpful responses with proper formatting
- [ ] **Integration**: Tools appear and function correctly in Claude Code

## Technical Implementation

### Architecture/Design
- Tool parameter schemas with validation
- Integration with search and assembly systems
- Response formatting for Claude Code
- Error handling and helpful messages
- Progress indicators for long operations
- Tool usage analytics

### Implementation Plan
```yaml
Phase 1: Tool Framework (Day 1)
  - Task: Enhance tool registration system
  - Output: Tools visible in Claude Code
  - Risk: MCP protocol compliance

Phase 2: search_code Tool (Day 2)
  - Task: Implement code search tool
  - Output: Natural language search
  - Risk: Query understanding

Phase 3: explain_code Tool (Day 3)
  - Task: Code explanation tool
  - Output: Context-aware explanations
  - Risk: Context assembly quality

Phase 4: Additional Tools (Day 4)
  - Task: find_similar, get_context
  - Output: Complete tool suite
  - Risk: Tool complexity

Phase 5: Polish & UX (Day 5)
  - Task: Error handling, formatting
  - Output: Production-ready tools
  - Risk: Edge cases
```

### Code Structure
```
src/signal_hub/core/tools/
├── __init__.py
├── base.py              # Enhanced base tool class
├── search_code.py       # Code search tool
├── explain_code.py      # Code explanation tool
├── find_similar.py      # Similarity search tool
├── get_context.py       # Context retrieval tool
├── schemas.py           # Parameter schemas
└── formatters.py        # Response formatting

src/signal_hub/mcp/
├── handlers.py          # Tool execution handlers
└── responses.py         # MCP response builders
```

## Dependencies & Risks
### Dependencies
- **Blocking**: SH-S02-014 (Search), SH-S02-016 (Context Assembly)
- **Dependent**: User adoption
- **External**: MCP protocol updates

### Risks & Mitigations
- **Risk**: Tool discovery issues in Claude Code
  - **Impact**: High
  - **Mitigation**: Comprehensive testing, clear naming
- **Risk**: Confusing tool parameters
  - **Impact**: Medium
  - **Mitigation**: Clear descriptions, examples

## Testing & Validation

### Testing Strategy
- **Unit Tests**: 
  - [ ] Tool parameter validation
  - [ ] Response formatting
  - [ ] Error handling
  - [ ] Edge cases
- **Integration Tests**:
  - [ ] End-to-end tool execution
  - [ ] Claude Code compatibility
  - [ ] Performance benchmarks
  - [ ] Multi-tool workflows

### Demo Scenarios
```python
# Tool definitions registered with MCP server
tools = {
    "search_code": {
        "description": "Search codebase using natural language queries",
        "parameters": {
            "query": "Natural language search query",
            "limit": "Maximum results (default: 10)",
            "language": "Filter by language (optional)",
            "file_pattern": "Filter by file pattern (optional)"
        }
    },
    "explain_code": {
        "description": "Get explanation of code functionality with context",
        "parameters": {
            "file_path": "Path to file to explain",
            "function_name": "Specific function/class (optional)",
            "include_dependencies": "Include related code (default: true)"
        }
    },
    "find_similar": {
        "description": "Find code similar to a given example",
        "parameters": {
            "code_snippet": "Example code to find similar",
            "limit": "Maximum results (default: 5)"
        }
    },
    "get_context": {
        "description": "Get relevant context for a coding task",
        "parameters": {
            "task_description": "What you're trying to accomplish",
            "current_file": "File you're working in (optional)"
        }
    }
}

# Example tool execution
async def handle_search_code(params):
    # Validate parameters
    query = params.get("query")
    if not query:
        return error_response("Query parameter is required")
    
    # Execute search
    results = await search_engine.search(
        query=query,
        limit=params.get("limit", 10),
        filters={
            "language": params.get("language"),
            "file_pattern": params.get("file_pattern")
        }
    )
    
    # Format response for Claude Code
    formatted = format_search_results(results)
    return success_response(formatted)

# In Claude Code:
# > search_code "how does user authentication work?"
# Returns formatted results with code snippets and explanations
```

## Definition of Done
- [ ] Tool registration system enhanced
- [ ] search_code tool implemented
- [ ] explain_code tool implemented
- [ ] find_similar tool implemented
- [ ] get_context tool implemented
- [ ] Parameter validation complete
- [ ] Response formatting optimized
- [ ] Error handling comprehensive
- [ ] Tools working in Claude Code
- [ ] Performance targets met
- [ ] Documentation with examples
- [ ] 90% test coverage

## Notes & Resources
- **Design Docs**: [MCP Tool Design](../../architecture/mcp-tools.md)
- **Partner Context**: Primary interface for users
- **Future Considerations**: More specialized tools, tool chaining
- **Learning Resources**: 
  - [MCP Tool Development](https://github.com/anthropics/mcp/docs/tools)
  - [Claude Code Integration](https://docs.anthropic.com/claude-code/mcp)
- **Edition Notes**: Core tools in Basic, advanced tools (refactor suggestions, code generation) in Pro