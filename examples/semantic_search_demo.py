#!/usr/bin/env python3
"""Demonstration of intelligent chunking and semantic search."""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from signal_hub.indexing.chunking import ChunkingStrategy
from signal_hub.indexing.embeddings import EmbeddingService
from signal_hub.retrieval import SemanticSearchEngine, SearchQuery, SearchConfig
from signal_hub.storage.factory import StoreFactory

console = Console()


async def demo_semantic_search():
    """Demonstrate semantic search capabilities."""
    console.print("\n[bold blue]Signal Hub Semantic Search Demo[/bold blue]\n")
    
    # Initialize components
    console.print("[yellow]Initializing components...[/yellow]")
    
    stores = StoreFactory.create_from_config({
        "vector_store": {"type": "chromadb", "path": "./demo_vectors"},
        "cache_store": {"type": "sqlite", "path": "./demo_cache.db"}
    })
    
    embedding_service = EmbeddingService()
    search_engine = SemanticSearchEngine(
        vector_store=stores["vector_store"],
        embedding_service=embedding_service,
        config=SearchConfig(similarity_threshold=0.5, rerank_results=True),
        cache_store=stores["cache_store"]
    )
    
    # Sample code to index
    sample_code = '''
"""Authentication module for web application."""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

class AuthManager:
    """Manages user authentication and JWT tokens."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
    def generate_token(self, user_id: int, email: str) -> str:
        """Generate a JWT token for a user."""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
'''
    
    # Step 1: Chunk the code
    console.print("\n[bold]Step 1: Intelligent Code Chunking[/bold]")
    
    strategy = ChunkingStrategy.for_language("python")
    chunks = strategy.chunk_text(sample_code)
    
    # Display chunks
    chunk_table = Table(title="Code Chunks")
    chunk_table.add_column("Type", style="cyan")
    chunk_table.add_column("Lines", style="green")
    chunk_table.add_column("Content Preview", style="white")
    
    for chunk in chunks:
        preview = chunk.content[:50].replace('\n', ' ') + "..."
        chunk_table.add_row(
            chunk.chunk_type.value,
            f"{chunk.start_line}-{chunk.end_line}",
            preview
        )
        
    console.print(chunk_table)
    
    # Step 2: Index the chunks
    console.print("\n[bold]Step 2: Indexing Code for Search[/bold]")
    
    for i, chunk in enumerate(chunks):
        # Generate embedding
        result = await embedding_service.generate_embeddings([chunk.content])
        
        # Store in vector database
        metadata = {
            "chunk_type": chunk.chunk_type.value,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "parent_context": chunk.parent_context,
            "chunk_index": i
        }
        
        if chunk.chunk_type.value == "method":
            # Extract method name
            import re
            match = re.search(r'def\s+(\w+)', chunk.content)
            if match:
                metadata["function_name"] = match.group(1)
        
        await stores["vector_store"].add_vectors(
            vectors=result.embeddings,
            texts=[chunk.content],
            metadata=[metadata]
        )
        
    console.print(f"[green]✓ Indexed {len(chunks)} code chunks[/green]")
    
    # Step 3: Demonstrate searches
    console.print("\n[bold]Step 3: Semantic Search Examples[/bold]\n")
    
    # Example queries
    queries = [
        ("How to hash passwords?", None),
        ("JWT token generation", None),
        ("verify user credentials", {"chunk_type": "method"}),
        ("security functions", None),
    ]
    
    for query_text, filters in queries:
        console.print(f"[yellow]Query:[/yellow] {query_text}")
        if filters:
            console.print(f"[yellow]Filters:[/yellow] {filters}")
            
        query = SearchQuery(
            text=query_text,
            limit=3,
            filters=filters or {}
        )
        
        results = await search_engine.search(query)
        
        if results:
            # Display results
            for i, result in enumerate(results, 1):
                console.print(f"\n[green]Result {i}:[/green] (Score: {result.score:.3f})")
                
                # Show metadata
                if result.metadata.get("function_name"):
                    console.print(f"  Function: {result.metadata['function_name']}")
                console.print(f"  Type: {result.metadata.get('chunk_type', 'unknown')}")
                console.print(f"  Lines: {result.metadata.get('start_line', '?')}-{result.metadata.get('end_line', '?')}")
                
                # Show code snippet
                syntax = Syntax(
                    result.text[:200] + "..." if len(result.text) > 200 else result.text,
                    "python",
                    theme="monokai",
                    line_numbers=False
                )
                console.print(syntax)
        else:
            console.print("[red]No results found[/red]")
            
        console.print("-" * 50)
    
    # Step 4: Demonstrate hybrid search
    console.print("\n[bold]Step 4: Hybrid Search (Semantic + Keyword)[/bold]")
    
    hybrid_query = SearchQuery(
        text="bcrypt password security",
        mode="hybrid",
        limit=2
    )
    
    results = await search_engine.search(hybrid_query)
    
    console.print(f"\n[yellow]Hybrid Query:[/yellow] {hybrid_query.text}")
    console.print(f"[green]Found {len(results)} results combining semantic and keyword matching[/green]")
    
    for result in results:
        console.print(f"\n• {result.metadata.get('function_name', 'Code snippet')}")
        console.print(f"  Score: {result.score:.3f}")
        console.print(f"  Preview: {result.text[:100]}...")
    
    # Cleanup
    await stores["vector_store"].clear()
    
    console.print("\n[bold green]Demo Complete![/bold green]")


if __name__ == "__main__":
    asyncio.run(demo_semantic_search())