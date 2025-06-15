# Database Migration Guide

This guide walks you through migrating from ChromaDB (development) to PostgreSQL with pgvector (production).

## Overview

Signal Hub uses ChromaDB for local development due to its simplicity, but PostgreSQL with pgvector is recommended for production deployments because it offers:

- Better performance at scale
- ACID compliance
- Backup and replication
- Advanced querying capabilities
- Production-grade reliability

## Prerequisites

- PostgreSQL 14+ installed
- pgvector extension
- Signal Hub with existing ChromaDB data
- Sufficient disk space (2x your current index size)

## Step 1: Install PostgreSQL with pgvector

### Using Docker (Recommended)

```bash
# Run PostgreSQL with pgvector
docker run -d \
  --name signal-hub-postgres \
  -e POSTGRES_PASSWORD=secure_password_here \
  -e POSTGRES_DB=signalhub \
  -p 5432:5432 \
  -v signal-hub-pgdata:/var/lib/postgresql/data \
  ankane/pgvector:latest

# Verify it's running
docker ps | grep signal-hub-postgres
```

### Manual Installation

=== "Ubuntu/Debian"

    ```bash
    # Install PostgreSQL
    sudo apt update
    sudo apt install postgresql postgresql-contrib
    
    # Install pgvector
    sudo apt install postgresql-14-pgvector
    
    # Or build from source
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    ```

=== "macOS"

    ```bash
    # Using Homebrew
    brew install postgresql
    brew install pgvector
    
    # Start PostgreSQL
    brew services start postgresql
    ```

## Step 2: Initialize Database Schema

### Connect to PostgreSQL

```bash
# Using psql
psql -U postgres -d signalhub

# Or with Docker
docker exec -it signal-hub-postgres psql -U postgres -d signalhub
```

### Create Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create main tables
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    language VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, chunk_index)
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    embedding vector(1536),  -- OpenAI embedding dimension
    model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);

-- Create search function
CREATE OR REPLACE FUNCTION search_similar(
    query_embedding vector,
    match_count int DEFAULT 10,
    min_similarity float DEFAULT 0.7
)
RETURNS TABLE(
    document_id UUID,
    file_path TEXT,
    content TEXT,
    similarity float
)
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.file_path,
        d.content,
        1 - (e.embedding <=> query_embedding) as similarity
    FROM embeddings e
    JOIN documents d ON e.document_id = d.id
    WHERE 1 - (e.embedding <=> query_embedding) > min_similarity
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

## Step 3: Export Data from ChromaDB

### Run Export Command

```bash
# Export all data from ChromaDB
signal-hub migrate export \
  --source chromadb \
  --output ./migration/chromadb-export.jsonl \
  --verbose

# For large datasets, export in batches
signal-hub migrate export \
  --source chromadb \
  --output ./migration/chromadb-export \
  --batch-size 1000 \
  --format jsonl
```

### Verify Export

```bash
# Check export size
du -h ./migration/chromadb-export.jsonl

# Preview data
head -n 5 ./migration/chromadb-export.jsonl | jq .

# Count documents
wc -l ./migration/chromadb-export.jsonl
```

## Step 4: Import to PostgreSQL

### Configure PostgreSQL Connection

```yaml
# config/production.yaml
database:
  type: postgresql
  connection:
    host: localhost
    port: 5432
    database: signalhub
    user: postgres
    password: ${POSTGRES_PASSWORD}
    sslmode: require
  pool:
    min_size: 5
    max_size: 20
    timeout: 30
```

### Run Import

```bash
# Set environment variable
export POSTGRES_PASSWORD="your_secure_password"

# Import data
signal-hub migrate import \
  --source ./migration/chromadb-export.jsonl \
  --target postgresql \
  --config config/production.yaml \
  --batch-size 500 \
  --workers 4 \
  --verbose

# Monitor progress
# The command shows a progress bar and ETA
```

### Import Options

| Option | Description | Default |
|--------|-------------|---------|
| `--batch-size` | Documents per batch | 1000 |
| `--workers` | Parallel workers | 4 |
| `--skip-errors` | Continue on errors | false |
| `--verify` | Verify after import | true |
| `--update-existing` | Update if exists | false |

## Step 5: Verify Migration

### Run Verification

```bash
# Automatic verification
signal-hub migrate verify \
  --config config/production.yaml \
  --sample-size 100

# Output:
# ✅ Document count matches: 15,234
# ✅ Embedding dimensions correct: 1536
# ✅ Sample searches successful: 100/100
# ✅ Metadata integrity: OK
# ✅ Index performance: 47ms avg
```

### Manual Verification

```sql
-- Check document count
SELECT COUNT(*) FROM documents;

-- Check embedding count
SELECT COUNT(*) FROM embeddings;

-- Verify embeddings are indexed
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename = 'embeddings';

-- Test search performance
EXPLAIN ANALYZE
SELECT * FROM search_similar(
    '[0.1, 0.2, ...]'::vector,
    10
);
```

## Step 6: Update Configuration

### Switch to PostgreSQL

```yaml
# signal-hub.yaml
storage:
  vector_store: postgresql  # Changed from chromadb
  
# Environment-specific override
# config/production.yaml
database:
  type: postgresql
  # ... connection details ...
```

### Test Connection

```bash
# Test new configuration
signal-hub test --config config/production.yaml

# Run a test search
signal-hub search "test query" --config config/production.yaml
```

## Step 7: Performance Tuning

### PostgreSQL Optimization

```sql
-- Tune pgvector for production
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET work_mem = '256MB';

-- Reload configuration
SELECT pg_reload_conf();

-- Optimize vector indexes
REINDEX INDEX CONCURRENTLY idx_embeddings_vector;
```

### Index Optimization

```sql
-- Create optimized indexes based on query patterns
CREATE INDEX CONCURRENTLY idx_documents_language 
ON documents(language) 
WHERE language IS NOT NULL;

-- Partial index for recent documents
CREATE INDEX CONCURRENTLY idx_documents_recent 
ON documents(created_at) 
WHERE created_at > CURRENT_DATE - INTERVAL '30 days';
```

## Rollback Procedure

If you need to rollback to ChromaDB:

```bash
# 1. Stop using PostgreSQL
signal-hub stop

# 2. Restore ChromaDB configuration
cp config/development.yaml signal-hub.yaml

# 3. Verify ChromaDB data is intact
signal-hub test --storage chromadb

# 4. Resume operations
signal-hub serve
```

## Troubleshooting

### Common Issues

#### Connection Refused
```
Error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed
```
**Solution**: Ensure PostgreSQL is running and accepting connections.

#### Vector Extension Missing
```
ERROR: type "vector" does not exist
```
**Solution**: Install and enable pgvector extension.

#### Performance Degradation
- Check index usage with `EXPLAIN ANALYZE`
- Verify connection pooling settings
- Monitor with `pg_stat_statements`

### Migration Benchmarks

| Metric | ChromaDB | PostgreSQL | Improvement |
|--------|----------|------------|-------------|
| Search Latency (p95) | 250ms | 47ms | 5.3x |
| Concurrent Queries | 10 QPS | 100 QPS | 10x |
| Storage Size | 2.1 GB | 1.8 GB | 15% |
| Backup Time | N/A | 30 sec | ✅ |

## Next Steps

1. Set up [monitoring](monitoring.md) for PostgreSQL
2. Configure [backups](backup-restore.md)
3. Implement [high availability](high-availability.md)
4. Review [security hardening](../security/hardening-checklist.md)