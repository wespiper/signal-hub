# Signal Hub Planning Documentation

## Overview
This directory contains the planning and implementation documentation for Signal Hub, an intelligent MCP server that extends Claude's context through RAG while optimizing costs via smart model routing.

### 🎯 Product Strategy: Hybrid Open Source Model

#### Signal Hub Basic (Open Source - MIT License)
**Core Features:**
- ✅ MCP server integration with Claude Code
- ✅ Codebase indexing and semantic search
- ✅ Rule-based model routing (Haiku/Sonnet/Opus)
- ✅ Basic semantic caching
- ✅ Simple cost tracking and reporting
- ✅ ChromaDB for local vector storage
- ✅ Zero configuration setup

#### Signal Hub Pro ($29/month + 15% of savings above $100)
**Advanced Features:**
- 🚀 ML-powered model routing (70%+ cost savings)
- 🚀 Learning algorithms that improve over time
- 🚀 Detailed analytics and ROI dashboard
- 🚀 Smart semantic deduplication
- 🚀 API access for custom integrations
- 🚀 Priority support

#### Signal Hub Enterprise (Custom Pricing)
**Team & Security Features:**
- 👥 Team management and user roles
- 🔐 SSO integration (SAML/OIDC)
- 🔐 Audit logging and compliance
- 🏢 Custom deployment options
- 🏢 Dedicated support with SLAs

#### Early Access Program
- 🎁 **All features free during beta** - Set `SIGNAL_HUB_EARLY_ACCESS=true`
- 🗣️ Direct input on product development
- 💰 Discounted pricing when we launch

## Current Planning Structure

### Core Documents
- **[Sprint Overview](sprints/overview.md)** - High-level view of all 16 sprints across 4 phases
- **[Sprint Goals](sprints/sprint-goals.md)** - Detailed goals, deliverables, and metrics for each sprint
- **[System Architecture](architecture/system-design.md)** - Technical design and component breakdown
- **[Testing Strategy](testing-strategy.md)** - Comprehensive testing approach

### Implementation Status
- **[Architecture Alignment Summary](architecture-alignment-summary.md)** - Shows how implementation aligns with design
- **[Implementation Summary](implementation-summary.md)** - Quick reference for getting started

### Sprint Tickets
- **[Sprint 1 Tickets](tickets/sprint-01/)** - 🔄 In Progress (10 tickets) - Building Signal Hub Basic foundation
  - Plugin architecture implemented ✅
  - Feature flags system created ✅
  - Repository setup 70% complete
- **[Sprint 2 Tickets](tickets/sprint-02/)** - 📋 Planned - RAG implementation for Basic edition

## Key Updates (Latest)

### Sprint 2 Enhancements
Based on architecture review, added critical components:
1. **Metadata Extraction** (SH-S02-011) - Enriches search with code structure
2. **Database Abstraction** (SH-S02-012) - Enables smooth production migration
3. **Batch Processing** (SH-S02-013) - 5x performance improvement

### Architecture Alignment
- All core components now have implementation tickets
- Clear path from development (ChromaDB) to production (pgvector)
- Performance optimizations scheduled appropriately

## Quick Navigation

### For Developers
1. Start with [Sprint 1 Tickets](tickets/sprint-01/README.md)
2. Review [System Architecture](architecture/system-design.md)
3. Follow [Testing Strategy](testing-strategy.md)

### For Project Managers
1. Track progress via [Sprint Overview](sprints/overview.md)
2. Review [Sprint Goals](sprints/sprint-goals.md) for metrics
3. Check [Implementation Summary](implementation-summary.md) for status

### For Contributors
1. Current sprint: Sprint 1 (Core Infrastructure)
2. Next sprint: Sprint 2 (RAG Implementation - Enhanced)
3. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines
4. Enable early access: `SIGNAL_HUB_EARLY_ACCESS=true`
5. Review [Edition Features](../docs/EDITIONS.md) for feature availability

## Sprint Progress

| Sprint | Phase | Status | Key Focus |
|--------|-------|---------|-----------|
| 1 | Foundation | 🟡 In Progress | Core infrastructure, MCP server |
| 2 | Foundation | 📋 Planned | RAG + Architecture improvements |
| 3 | Foundation | 📋 Planned | Model routing & caching |
| 4 | Foundation | 📋 Planned | Polish & documentation |
| 5-8 | Community | 🔮 Future | Community building & early access |
| 9-12 | Monetization | 🔮 Future | Pro features & pricing validation |
| 13-16 | Scale | 🔮 Future | Enterprise & platform growth |

## Deprecated Documents
Older planning documents have been moved to [deprecated/](deprecated/) for reference but are no longer actively maintained.